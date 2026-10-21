"""Shared provider contract and HTTP helpers.

A provider adapter has four jobs:
1. declare capabilities;
2. validate a normalized VideoRequest before submission;
3. translate that request into the provider's wire format;
4. normalize task/status responses back into TaskResult.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any


class ProviderError(RuntimeError):
    """A user-actionable provider/capability error."""


@dataclass
class Capabilities:
    provider: str
    default_model: str
    models: dict[str, dict[str, Any]]
    modes: list[str]
    duration_min: int
    duration_max: int
    default_duration: int
    aspect_ratios: list[str]
    resolutions: list[str]
    max_images: int
    max_audios: int
    max_videos: int
    supports_first_frame: bool
    supports_last_frame: bool
    supports_video_reference: bool
    supports_audio_reference: bool
    requires_public_urls: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "default_model": self.default_model,
            "models": self.models,
            "modes": self.modes,
            "duration": {"min": self.duration_min, "max": self.duration_max, "default": self.default_duration},
            "aspect_ratios": self.aspect_ratios,
            "resolutions": self.resolutions,
            "limits": {
                "max_images": self.max_images,
                "max_audios": self.max_audios,
                "max_videos": self.max_videos,
            },
            "media": {
                "supports_first_frame": self.supports_first_frame,
                "supports_last_frame": self.supports_last_frame,
                "supports_video_reference": self.supports_video_reference,
                "supports_audio_reference": self.supports_audio_reference,
                "requires_public_urls": self.requires_public_urls,
            },
        }


@dataclass
class VideoRequest:
    provider: str
    model: str | None = None
    prompt: str = ""
    mode: str = "auto"  # auto | text | keyframe | reference
    duration: int | None = None
    aspect_ratio: str | None = None
    resolution: str | None = None
    first_frame: str | None = None
    last_frame: str | None = None
    reference_images: list[str] = field(default_factory=list)
    reference_audios: list[str] = field(default_factory=list)
    reference_videos: list[str] = field(default_factory=list)
    seed: int | None = None


@dataclass
class TaskResult:
    provider: str
    model: str
    task_id: str = ""
    video_id: str = ""
    status: str = "unknown"
    video_url: str = ""
    duration: str = ""
    resolution: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


class Provider:
    name = "base"

    @property
    def capabilities(self) -> Capabilities:
        raise NotImplementedError

    @property
    def api_key_env(self) -> str:
        raise NotImplementedError

    def get_api_key(self) -> str:
        key = os.environ.get(self.api_key_env, "").strip()
        if not key:
            raise ProviderError(
                f"{self.api_key_env} is not set. Export it before calling the provider."
            )
        return key

    def resolve_mode(self, req: VideoRequest) -> str:
        if req.mode != "auto":
            return req.mode
        if req.reference_images or req.reference_audios or req.reference_videos:
            return "reference"
        if req.first_frame or req.last_frame:
            return "keyframe"
        return "text"

    def validate(self, req: VideoRequest) -> list[str]:
        caps = self.capabilities
        errors: list[str] = []
        mode = self.resolve_mode(req)
        if mode not in caps.modes:
            errors.append(f"provider {self.name} does not support mode={mode}; supported: {', '.join(caps.modes)}")
        duration = req.duration if req.duration is not None else caps.default_duration
        if not (caps.duration_min <= duration <= caps.duration_max):
            errors.append(f"duration must be {caps.duration_min}-{caps.duration_max}s for {self.name} (got {duration})")
        ratio = req.aspect_ratio or caps.aspect_ratios[0]
        if ratio not in caps.aspect_ratios:
            errors.append(f"aspect_ratio must be one of {caps.aspect_ratios} for {self.name} (got {ratio})")
        resolution = req.resolution or caps.resolutions[0]
        if resolution not in caps.resolutions:
            errors.append(f"resolution must be one of {caps.resolutions} for {self.name} (got {resolution})")
        if len(req.reference_images) > caps.max_images:
            errors.append(f"too many reference images: {len(req.reference_images)} > {caps.max_images}")
        if len(req.reference_audios) > caps.max_audios:
            errors.append(f"too many reference audios: {len(req.reference_audios)} > {caps.max_audios}")
        if len(req.reference_videos) > caps.max_videos:
            errors.append(f"too many reference videos: {len(req.reference_videos)} > {caps.max_videos}")
        if mode == "text" and (req.first_frame or req.last_frame or req.reference_images or req.reference_audios or req.reference_videos):
            errors.append("mode=text does not accept frame or reference media")
        if mode == "keyframe":
            if not (req.first_frame or req.last_frame):
                errors.append("mode=keyframe requires first_frame and/or last_frame")
            if req.reference_images or req.reference_audios or req.reference_videos:
                errors.append("mode=keyframe does not accept reference images/audio/video")
        if mode == "reference":
            if not (req.reference_images or req.reference_audios or req.reference_videos):
                errors.append("mode=reference requires at least one reference image/audio/video")
            if req.first_frame or req.last_frame:
                errors.append("mode=reference does not accept first_frame/last_frame")
        if not caps.supports_first_frame and req.first_frame:
            errors.append(f"{self.name} does not support first_frame")
        if not caps.supports_last_frame and req.last_frame:
            errors.append(f"{self.name} does not support last_frame")
        if not caps.supports_video_reference and req.reference_videos:
            errors.append(f"{self.name} does not support reference videos")
        if not caps.supports_audio_reference and req.reference_audios:
            errors.append(f"{self.name} does not support reference audio")
        if caps.requires_public_urls:
            for label, values in (
                ("first_frame", [req.first_frame] if req.first_frame else []),
                ("last_frame", [req.last_frame] if req.last_frame else []),
                ("reference_images", req.reference_images),
                ("reference_audios", req.reference_audios),
                ("reference_videos", req.reference_videos),
            ):
                for value in values:
                    if not str(value).startswith(("http://", "https://")):
                        errors.append(
                            f"{self.name} requires a publicly reachable URL for {label}: {value}"
                        )
        if not str(req.prompt or "").strip() and not (req.first_frame or req.last_frame):
            errors.append("prompt is required unless a frame-only keyframe request is supported")
        return errors

    def build_create_request(self, req: VideoRequest, dry_run: bool = False) -> tuple[str, dict[str, Any]]:
        raise NotImplementedError

    def parse_create_response(self, data: dict[str, Any]) -> TaskResult:
        raise NotImplementedError

    def build_status_request(self, task: TaskResult) -> tuple[str, str]:
        raise NotImplementedError

    def parse_status_response(self, data: dict[str, Any], task: TaskResult) -> TaskResult:
        raise NotImplementedError


def http_json(method: str, url: str, api_key: str, payload: dict[str, Any] | None = None, timeout: int = 60) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8")
            return json.loads(text) if text else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(detail)
            message = parsed.get("detail") or parsed.get("error", {}).get("message") or detail
        except json.JSONDecodeError:
            message = detail
        raise ProviderError(f"HTTP {exc.code} from {url}: {message}") from exc
    except urllib.error.URLError as exc:
        raise ProviderError(f"Network error calling {url}: {exc.reason}") from exc


def normalize_status(value: str) -> str:
    value = str(value or "").lower()
    if value in {"succeeded", "success", "completed", "done"}:
        return "succeeded"
    if value in {"failed", "error", "cancelled", "canceled", "expired"}:
        return "failed"
    if value in {"queued", "pending", "running", "in_progress", "processing", "created", "submitted"}:
        return "running"
    return value or "unknown"

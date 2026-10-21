"""Volcengine Ark / Seedance adapter.

This mirrors the existing seedance.py wire contract while exposing the same
normalized request/response interface as other providers.
"""
from __future__ import annotations

import base64
import mimetypes
import os
from pathlib import Path
from typing import Any

from .base import Capabilities, Provider, ProviderError, TaskResult, VideoRequest, http_json, normalize_status


class SeedanceProvider(Provider):
    name = "seedance"
    api_key_env = "ARK_API_KEY"
    default_base = "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks"

    @property
    def capabilities(self) -> Capabilities:
        return Capabilities(
            provider=self.name,
            default_model="doubao-seedance-2-0-260128",
            models={
                "doubao-seedance-2-0-260128": {"label": "Seedance 2.0", "duration": [4, 15], "media": "image/video/audio"},
                "doubao-seedance-1-5-pro-251215": {"label": "Seedance 1.5 Pro", "duration": [4, 15], "media": "image/audio"},
                "doubao-seedance-1-0-pro-250528": {"label": "Seedance 1.0 Pro", "duration": [4, 12], "media": "image/frames"},
            },
            modes=["text", "keyframe", "reference"],
            duration_min=4,
            duration_max=15,
            default_duration=5,
            aspect_ratios=["16:9", "4:3", "1:1", "3:4", "9:16", "21:9", "adaptive"],
            resolutions=["480p", "720p", "1080p"],
            max_images=9,
            max_audios=3,
            max_videos=3,
            supports_first_frame=True,
            supports_last_frame=True,
            supports_video_reference=True,
            supports_audio_reference=True,
            requires_public_urls=False,
        )

    @property
    def base_url(self) -> str:
        return os.environ.get("ARK_BASE_URL", self.default_base).rstrip("/")

    def _media_url(self, value: str, kind: str, dry_run: bool) -> str:
        if value.startswith(("http://", "https://", "data:")):
            return value
        if dry_run:
            return f"<local-{kind}:{value}>"
        path = Path(value).expanduser()
        if not path.is_file():
            raise ProviderError(f"local {kind} file not found: {value}")
        limit_mb = {"image": 30, "video": 50, "audio": 15}[kind]
        if path.stat().st_size > limit_mb * 1024 * 1024:
            raise ProviderError(f"{kind} file too large: {value} (max {limit_mb} MB)")
        if kind == "image":
            ext = path.suffix.lower().lstrip(".") or "png"
            mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp", "bmp": "bmp", "tif": "tiff", "tiff": "tiff"}.get(ext, ext)
        else:
            mime = mimetypes.guess_type(str(path))[0] or (("video/mp4") if kind == "video" else "audio/mpeg")
        return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"

    def build_create_request(self, req: VideoRequest, dry_run: bool = False) -> tuple[str, dict[str, Any]]:
        mode = self.resolve_mode(req)
        content: list[dict[str, Any]] = [{"type": "text", "text": req.prompt}]
        if mode == "reference":
            for image in req.reference_images:
                content.append({"type": "image_url", "image_url": {"url": self._media_url(image, "image", dry_run)}, "role": "reference_image"})
            for video in req.reference_videos:
                content.append({"type": "video_url", "video_url": {"url": self._media_url(video, "video", dry_run)}})
            for audio in req.reference_audios:
                content.append({"type": "audio_url", "audio_url": {"url": self._media_url(audio, "audio", dry_run)}})
        elif mode == "keyframe":
            if req.first_frame:
                content.append({"type": "image_url", "image_url": {"url": self._media_url(req.first_frame, "image", dry_run)}, "role": "first_frame"})
            if req.last_frame:
                content.append({"type": "image_url", "image_url": {"url": self._media_url(req.last_frame, "image", dry_run)}, "role": "last_frame"})
        body: dict[str, Any] = {
            "model": req.model or self.capabilities.default_model,
            "content": content,
            "ratio": req.aspect_ratio or "16:9",
            "duration": req.duration if req.duration is not None else self.capabilities.default_duration,
            "resolution": req.resolution or "720p",
        }
        if req.seed is not None:
            body["seed"] = req.seed
        return self.base_url, body

    def parse_create_response(self, data: dict[str, Any]) -> TaskResult:
        task_id = str(data.get("id") or data.get("task_id") or "")
        return TaskResult(provider=self.name, model=str(data.get("model") or ""), task_id=task_id, status=normalize_status(data.get("status", "queued")), raw=data)

    def build_status_request(self, task: TaskResult) -> tuple[str, str]:
        if not task.task_id:
            raise ProviderError("Seedance task_id is missing")
        return f"{self.base_url}/{task.task_id}", "GET"

    def parse_status_response(self, data: dict[str, Any], task: TaskResult) -> TaskResult:
        content = data.get("content") or {}
        url = content.get("video_url") or content.get("url") or data.get("video_url") or ""
        status = normalize_status(data.get("status", "unknown"))
        return TaskResult(
            provider=self.name,
            model=task.model,
            task_id=task.task_id,
            status=status,
            video_url=url,
            duration=str(data.get("duration", "")),
            resolution=str(data.get("resolution", "")),
            raw=data,
        )

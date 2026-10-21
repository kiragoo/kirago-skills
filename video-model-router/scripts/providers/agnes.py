"""Agnes Video 2.5 Flash adapter.

Official contract used here:
- POST {base}/videos
- GET {origin}/agnesapi?video_id=...&model_name=...
- model: agnes-video-2.5-flash
- seconds: "4".."12"
- size: "720P"
- modes: text | keyframe | reference
- reference: images <= 5, audios <= 3, videos unsupported
- media must be publicly reachable URLs
"""
from __future__ import annotations

import os
import urllib.parse
from urllib.parse import urlsplit
from typing import Any

from .base import Capabilities, Provider, ProviderError, TaskResult, VideoRequest, http_json, normalize_status


class AgnesProvider(Provider):
    name = "agnes"
    api_key_env = "AGNES_API_KEY"
    default_base = "https://api.agnes-ai.cn/v1"

    @property
    def capabilities(self) -> Capabilities:
        return Capabilities(
            provider=self.name,
            default_model="agnes-video-2.5-flash",
            models={
                "agnes-video-2.5-flash": {
                    "label": "Agnes Video 2.5 Flash",
                    "duration": [4, 12],
                    "resolution": ["720P"],
                    "media": "text/image/audio; no video reference",
                }
            },
            modes=["text", "keyframe", "reference"],
            duration_min=4,
            duration_max=12,
            default_duration=5,
            aspect_ratios=["21:9", "16:9", "4:3", "1:1", "3:4", "9:16"],
            resolutions=["720P"],
            max_images=5,
            max_audios=3,
            max_videos=0,
            supports_first_frame=True,
            supports_last_frame=True,
            supports_video_reference=False,
            supports_audio_reference=True,
            requires_public_urls=True,
        )

    @property
    def base_url(self) -> str:
        return os.environ.get("AGNES_BASE_URL", self.default_base).rstrip("/")

    def _check_public_url(self, value: str, label: str) -> str:
        if not str(value).startswith(("http://", "https://")):
            raise ProviderError(
                f"Agnes requires a publicly reachable URL for {label}: {value}. "
                "Upload the file to object storage or another public host first."
            )
        return value

    def build_create_request(self, req: VideoRequest, dry_run: bool = False) -> tuple[str, dict[str, Any]]:
        mode = self.resolve_mode(req)
        body: dict[str, Any] = {
            "model": req.model or self.capabilities.default_model,
            "prompt": req.prompt,
            "seconds": str(req.duration if req.duration is not None else self.capabilities.default_duration),
            "mode": mode,
            "size": "720P",
            "aspect_ratio": req.aspect_ratio or "16:9",
        }
        if req.seed is not None:
            body["seed"] = req.seed
        if mode == "keyframe":
            if req.first_frame:
                body["first_frame"] = self._check_public_url(req.first_frame, "first_frame")
            if req.last_frame:
                body["last_frame"] = self._check_public_url(req.last_frame, "last_frame")
        elif mode == "reference":
            if req.reference_images:
                body["images"] = [self._check_public_url(v, "reference image") for v in req.reference_images]
            if req.reference_audios:
                body["audios"] = [self._check_public_url(v, "reference audio") for v in req.reference_audios]
        return f"{self.base_url}/videos", body

    def parse_create_response(self, data: dict[str, Any]) -> TaskResult:
        task_id = str(data.get("id") or data.get("task_id") or data.get("video_id") or "")
        video_id = str(data.get("video_id") or "")
        return TaskResult(
            provider=self.name,
            model=str(data.get("model") or ""),
            task_id=task_id,
            video_id=video_id,
            status=normalize_status(data.get("status", "queued")),
            raw=data,
        )

    def build_status_request(self, task: TaskResult) -> tuple[str, str]:
        identifier = task.video_id or task.task_id
        if not identifier:
            raise ProviderError("Agnes video_id/task_id is missing")
        parts = urlsplit(self.base_url)
        origin = f"{parts.scheme}://{parts.netloc}"
        query = urllib.parse.urlencode({"video_id": identifier, "model_name": task.model or self.capabilities.default_model})
        return f"{origin}/agnesapi?{query}", "GET"

    def parse_status_response(self, data: dict[str, Any], task: TaskResult) -> TaskResult:
        url = data.get("url") or data.get("video_url") or ""
        if isinstance(url, dict):
            url = url.get("url", "")
        return TaskResult(
            provider=self.name,
            model=task.model,
            task_id=task.task_id,
            video_id=task.video_id or str(data.get("video_id") or ""),
            status=normalize_status(data.get("status", "unknown")),
            video_url=url,
            duration=str(data.get("seconds", "")),
            resolution=str(data.get("size", "")),
            raw=data,
        )

# Provider Contract

## Goal

Support any third-party video model without branching the creative workflow.

## Interface

Every provider must implement:

```python
class Provider:
    name: str
    api_key_env: str

    @property
    def capabilities(self) -> Capabilities: ...

    def validate(self, req: VideoRequest) -> list[str]: ...

    def build_create_request(self, req: VideoRequest, dry_run: bool = False) -> tuple[str, dict]: ...

    def parse_create_response(self, data: dict) -> TaskResult: ...

    def build_status_request(self, task: TaskResult) -> tuple[str, str]: ...

    def parse_status_response(self, data: dict, task: TaskResult) -> TaskResult: ...
```

## Capabilities must be explicit

At minimum declare:

- provider name;
- default model and supported model IDs;
- supported modes;
- duration min/max/default;
- supported aspect ratios;
- supported resolutions;
- image/audio/video reference limits;
- first-frame/last-frame support;
- whether local media can be sent or public URLs are required;
- API key environment variable.

## Validation before submission

Validation should reject unsupported combinations before any network call:

- duration out of range;
- unsupported aspect ratio or resolution;
- too many reference assets;
- keyframe mode mixed with reference media;
- reference mode mixed with first/last frame;
- local file where the provider requires a public URL;
- video reference where the provider explicitly rejects video.

## Normalization

Provider responses differ. Normalize them into:

```python
TaskResult(
    provider=...,
    model=...,
    task_id=...,
    video_id=...,
    status="running" | "succeeded" | "failed",
    video_url=...,
    duration=...,
    resolution=...,
    raw=...,
)
```

## Agnes specifics

Official contract:

- create: `POST {base}/videos`;
- query: `GET {origin}/agnesapi?video_id=...&model_name=...`;
- model: `agnes-video-2.5-flash`;
- `seconds`: `"4"`–`"12"`;
- `size`: `"720P"`;
- modes: `text`, `keyframe`, `reference`;
- reference images: ≤5;
- reference audio: ≤3;
- reference video: unsupported;
- media: public URLs only.

## Seedance specifics

- create: `POST {base}`;
- query: `GET {base}/{task_id}`;
- model: `doubao-seedance-2-0-260128` by default;
- `content`: array of text/image/video/audio parts;
- distance may be local base64 data URL;
- `duration`, `ratio`, `resolution` are top-level fields;
- result URL is `content.video_url`.

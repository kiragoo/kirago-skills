---
name: video-model-router
description: "Provider-neutral AI video generation skill. Routes one normalized request to Seedance (Volcengine Ark) or Agnes Video 2.5 Flash, validates each provider's duration/resolution/media limits before submission, and normalizes task creation, polling, and result URLs. Use for AI video generation, Seedance, 即梦, Agnes, text-to-video, image-to-video, first/last-frame video, reference-to-video, or when adding a new third-party video provider."
metadata:
  version: "0.2.0"
  repository: "https://github.com/kirago/ai-video"
---

# Video Model Router

Turn one normalized video request into a specific provider's API request, validate it against that provider's real limits, then normalize the async task lifecycle.

**Core rule: provider-specific syntax never leaks into the creative prompt workflow.** The creative workflow decides what the video should contain; the provider adapter decides how to submit it.

## When to use

Use this skill for:

- text-to-video, image-to-video, first/last-frame video, reference-to-video;
- Seedance / 即梦 / Volcengine Ark generation;
- Agnes / Agnes Video 2.5 Flash generation;
- adding a third-party video model to this project;
- diagnosing provider-specific limits (duration, resolution, media count, public-URL requirements).

## Architecture

```
User brief
  → creative prompt workflow
  → normalized VideoRequest
  → provider adapter
      → validate capabilities
      → build provider request
      → create task
      → poll status
      → normalize TaskResult
  → download / report
```

Files:

- `scripts/video_cli.py` — provider-neutral CLI;
- `scripts/providers/base.py` — shared contract, validation, HTTP helpers;
- `scripts/providers/seedance.py` — Volcengine Ark adapter;
- `scripts/providers/agnes.py` — Agnes Video 2.5 Flash adapter;
- `references/provider-contract.md` — how to add another provider;
- `tests/test_providers.py` — capability and request-shape tests.

## Shared creative references

Before writing a prompt, load the smallest relevant set:

| Task | Read |
|---|---|
| Any prompt | `references/prompt-patterns.md` |
| Shot size, angle, camera, lighting, composition | `references/cinematography.md` |
| Style, palette, texture, director references | `references/styles-and-visuals.md` |
| One-take, shot-to-shot continuity, extension | `references/continuity-and-transitions.md` |
| Provider differences | `references/provider-profiles.md` |
| Product, dialogue, action, horror, emotion, etc. | `references/scene-recipes.md` |
| Add a new provider | `references/provider-contract.md` |

Index: `references/README.md`.

Rules:

1. These references are the single source of truth for shared creative knowledge. Do not duplicate them into provider skills.
2. Provider-specific syntax, limits, and examples belong in `provider-profiles.md` or the provider's own supplementary manual.
3. Load only what the task needs; do not preload every reference.

## Provider capabilities

### Seedance

- Models: `doubao-seedance-2-0-260128`, `doubao-seedance-1-5-pro-251215`, `doubao-seedance-1-0-pro-250528`.
- Duration: 4–15 s for 2.0/1.5; 4–12 s for 1.0.
- Resolutions: 480p, 720p, 1080p.
- Modes: text, keyframe, reference.
- Media: up to 9 images, 3 videos, 3 audio.
- Local files: supported (converted to base64 data URLs).
- API key: `ARK_API_KEY`.

### Agnes Video 2.5 Flash

Official model ID: `agnes-video-2.5-flash`.

Official docs:
https://www.agnes-ai.cn/zh-Hans/docs/agnes-video-25-flash

- Base URL: `https://api.agnes-ai.cn/v1`.
- Create: `POST /v1/videos`.
- Query: `GET /agnesapi?video_id=...&model_name=agnes-video-2.5-flash`.
- Duration: **4–12 s**, sent as a string.
- Resolution: **only `720P`**.
- Aspect ratios: `21:9`, `16:9`, `4:3`, `1:1`, `3:4`, `9:16`.
- Modes: `text`, `keyframe`, `reference`.
- Reference images: **max 5**.
- Reference audio: **max 3**.
- Reference video: **not supported**.
- Media: **publicly reachable URLs only**; local files are rejected before submission.
- API key: `AGNES_API_KEY`.
- Base URL override: `AGNES_BASE_URL`.

## Core workflow

1. Read the user's creative brief.
2. Load the relevant shared references: prompt structure, cinematography, style, continuity, and scene recipe.
3. Choose the provider explicitly. If the user names Seedance/即梦, use `seedance`; if the user names Agnes, use `agnes`.
4. Write the creative prompt with the shared vocabulary and templates.
5. Build one normalized request:
   - `prompt`;
   - `mode` (`auto` / `text` / `keyframe` / `reference`);
   - `duration`;
   - `aspect_ratio`;
   - `resolution`;
   - first/last frame;
   - reference images/audio/video.
6. Run `capabilities` or `--dry-run` before a paid submission when any limit is uncertain.
7. Submit only after the user has asked for generation or approved the spend.
8. Poll until `succeeded` or `failed`; report the provider's normalized result.

## Commands

List providers:

```bash
python3 scripts/video_cli.py providers
```

Inspect one provider:

```bash
python3 scripts/video_cli.py capabilities --provider agnes
```

Agnes 12-second text-to-video:

```bash
export AGNES_API_KEY="..."
python3 scripts/video_cli.py create   --provider agnes   --prompt "单一连续镜头，一镜到底，雨夜城市街道，镜头缓慢跟随人物"   --duration 12   --aspect-ratio 16:9   --wait   --download ./output
```

Agnes keyframe:

```bash
python3 scripts/video_cli.py create   --provider agnes   --mode keyframe   --prompt "人物自然转身，镜头平滑推进"   --duration 8   --image https://example.com/first.png   --last-frame https://example.com/last.png   --wait
```

Agnes reference images:

```bash
python3 scripts/video_cli.py create   --provider agnes   --mode reference   --prompt "以 <Picture 1> 的角色和美术风格为参考，在花田中奔跑"   --duration 12   --ref-images https://example.com/character.png   --wait
```

Seedance 8-second text-to-video:

```bash
export ARK_API_KEY="..."
python3 scripts/video_cli.py create   --provider seedance   --prompt "..."   --duration 8   --resolution 720p   --wait   --download ./output
```

Validate without calling the API:

```bash
python3 scripts/video_cli.py create --provider agnes --prompt "x" --duration 12 --dry-run
```

## Hard rules

1. Never silently change a user's requested duration, aspect ratio, mode, or provider.
2. Never submit a request that fails `validate()`.
3. For Agnes, reject local media paths and explain that a public URL is required.
4. For Agnes, never send `videos`; Flash explicitly rejects it.
5. For Agnes, `seconds` must be a string from `"4"` to `"12"`, and `size` must be `"720P"`.
6. For Seedance, keep the existing Ark semantics and local-file support.
7. If an API key is missing, print the request in dry-run/validation form and state that no task was submitted.
8. Do not claim a video was generated until a task reaches `succeeded` with a video URL.
9. For one-take shots, explicitly state “single continuous shot, no cuts” and avoid “shot 1 / shot 2 / cut to” language.
10. For multi-shot work, record each shot's start and end state and use `references/continuity-and-transitions.md`.
11. Do not copy the generic vocabulary into a provider adapter. Keep provider code free of creative taxonomy.

## Adding another provider

Read `references/provider-contract.md`.

The short version:

1. Subclass `Provider`.
2. Declare `Capabilities`.
3. Implement four methods:
   - `validate()`;
   - `build_create_request()`;
   - `parse_create_response()`;
   - `build_status_request()` + `parse_status_response()`.
4. Register it in `scripts/providers/__init__.py`.
5. Add capability tests.
6. Do not put provider syntax into the shared creative references; keep it in the adapter and `provider-profiles.md`.

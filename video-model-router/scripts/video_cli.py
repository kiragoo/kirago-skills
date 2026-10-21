#!/usr/bin/env python3
"""Provider-neutral video generation CLI.

Examples:
  python video_cli.py providers
  python video_cli.py capabilities --provider agnes
  python video_cli.py create --provider agnes --prompt "..." --duration 12 --wait --download ./out
  python video_cli.py create --provider seedance --prompt "..." --duration 8 --dry-run
  python video_cli.py status --provider agnes --task-id task_x --video-id video_x
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from providers import PROVIDERS, ProviderError, VideoRequest, TaskResult
from providers.base import http_json


def provider_or_fail(name: str):
    key = (name or "").strip().lower()
    if key not in PROVIDERS:
        raise ProviderError(f"unknown provider '{name}'. Available: {', '.join(PROVIDERS)}")
    return PROVIDERS[key]


def cmd_providers(_args):
    print(json.dumps({name: p.capabilities.to_dict() for name, p in PROVIDERS.items()}, ensure_ascii=False, indent=2))


def cmd_capabilities(args):
    p = provider_or_fail(args.provider)
    print(json.dumps(p.capabilities.to_dict(), ensure_ascii=False, indent=2))


def build_request(args) -> VideoRequest:
    return VideoRequest(
        provider=args.provider,
        model=args.model,
        prompt=args.prompt or "",
        mode=args.mode,
        duration=args.duration,
        aspect_ratio=args.aspect_ratio,
        resolution=args.resolution,
        first_frame=args.image,
        last_frame=args.last_frame,
        reference_images=args.ref_images or [],
        reference_audios=args.audio or [],
        reference_videos=args.video or [],
        seed=args.seed,
    )


def cmd_create(args):
    p = provider_or_fail(args.provider)
    req = build_request(args)
    req.model = req.model or p.capabilities.default_model
    errors = p.validate(req)
    if errors:
        print(json.dumps({"provider": p.name, "valid": False, "errors": errors}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2

    url, body = p.build_create_request(req, dry_run=args.dry_run)
    safe_body = dict(body)
    print(json.dumps({"provider": p.name, "mode": p.resolve_mode(req), "url": url, "request": safe_body}, ensure_ascii=False, indent=2))
    if args.dry_run:
        return 0

    api_key = os.environ.get(p.api_key_env, "").strip()
    if not api_key:
        print(json.dumps({"error": f"{p.api_key_env} is not set; request was not submitted"}, ensure_ascii=False), file=sys.stderr)
        return 3
    created = http_json("POST", url, api_key, body)
    task = p.parse_create_response(created)
    task.model = req.model
    print(json.dumps({"provider": task.provider, "task_id": task.task_id, "video_id": task.video_id, "status": task.status}, ensure_ascii=False, indent=2))
    if args.wait:
        return wait_and_download(p, task, args)
    return 0


def wait_and_download(p, task: TaskResult, args):
    deadline = time.time() + args.timeout
    while time.time() < deadline:
        status_url, method = p.build_status_request(task)
        data = http_json(method, status_url, os.environ[p.api_key_env])
        task = p.parse_status_response(data, task)
        print(json.dumps({"provider": task.provider, "task_id": task.task_id, "video_id": task.video_id, "status": task.status, "video_url": task.video_url}, ensure_ascii=False), flush=True)
        if task.status == "succeeded":
            if args.download and task.video_url:
                out = Path(args.download).expanduser()
                out.mkdir(parents=True, exist_ok=True)
                suffix = ".mp4"
                filename = f"{task.provider}_{task.video_id or task.task_id}{suffix}"
                path = out / filename
                urllib.request.urlretrieve(task.video_url, str(path))
                print(json.dumps({"downloaded": str(path), "video_url": task.video_url}, ensure_ascii=False, indent=2))
            print(json.dumps(task.raw, ensure_ascii=False, indent=2))
            return 0
        if task.status == "failed":
            print(json.dumps(task.raw, ensure_ascii=False, indent=2), file=sys.stderr)
            return 1
        time.sleep(args.interval)
    print(json.dumps({"error": "timeout", "task_id": task.task_id, "video_id": task.video_id}, ensure_ascii=False), file=sys.stderr)
    return 1


def cmd_status(args):
    p = provider_or_fail(args.provider)
    task = TaskResult(provider=p.name, model=args.model or p.capabilities.default_model, task_id=args.task_id or "", video_id=args.video_id or "")
    url, method = p.build_status_request(task)
    api_key = os.environ.get(p.api_key_env)
    if not api_key:
        raise ProviderError(f"{p.api_key_env} is not set")
    data = http_json(method, url, api_key)
    result = p.parse_status_response(data, task)
    print(json.dumps({"provider": result.provider, "status": result.status, "video_url": result.video_url, "duration": result.duration, "resolution": result.resolution}, ensure_ascii=False, indent=2))


def parse_bool(v):
    if isinstance(v, bool):
        return v
    return str(v).lower() in {"1", "true", "yes", "y", "on"}


def main():
    parser = argparse.ArgumentParser(description="Provider-neutral AI video generation CLI")
    subs = parser.add_subparsers(dest="command", required=True)

    subs.add_parser("providers", help="List providers and capabilities").set_defaults(func=cmd_providers)

    p_cap = subs.add_parser("capabilities", help="Show one provider's capabilities")
    p_cap.add_argument("--provider", required=True)
    p_cap.set_defaults(func=cmd_capabilities)

    p_create = subs.add_parser("create", help="Create a generation task")
    p_create.add_argument("--provider", required=True)
    p_create.add_argument("--model")
    p_create.add_argument("--prompt", "-p", required=True)
    p_create.add_argument("--mode", choices=["auto", "text", "keyframe", "reference"], default="auto")
    p_create.add_argument("--duration", "-d", type=int)
    p_create.add_argument("--aspect-ratio", "--ratio", dest="aspect_ratio")
    p_create.add_argument("--resolution", "-r")
    p_create.add_argument("--image", help="first frame / image URL")
    p_create.add_argument("--last-frame")
    p_create.add_argument("--ref-images", nargs="+")
    p_create.add_argument("--audio", nargs="+")
    p_create.add_argument("--video", nargs="+")
    p_create.add_argument("--seed", type=int)
    p_create.add_argument("--dry-run", action="store_true", help="validate and print the provider request without calling the API")
    p_create.add_argument("--wait", action="store_true")
    p_create.add_argument("--interval", type=float, default=2.0)
    p_create.add_argument("--timeout", type=int, default=900)
    p_create.add_argument("--download")
    p_create.set_defaults(func=cmd_create)

    p_status = subs.add_parser("status", help="Query a task")
    p_status.add_argument("--provider", required=True)
    p_status.add_argument("--model")
    p_status.add_argument("--task-id")
    p_status.add_argument("--video-id")
    p_status.set_defaults(func=cmd_status)

    args = parser.parse_args()
    try:
        return args.func(args) or 0
    except ProviderError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

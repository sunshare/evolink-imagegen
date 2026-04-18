#!/usr/bin/env python3
"""Submit, poll, and download Evolink async image generations."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_BASE_URL = os.environ.get("EVOLINK_API_BASE_URL", "https://api.evolink.ai")
DEFAULT_MODEL = os.environ.get("EVOLINK_IMAGE_MODEL", "z-image-turbo")
DEFAULT_OUTPUT_BASE = Path("generated/evolink-imagegen")
USER_AGENT = "EvolinkImageGenSkill/1.0"


class EvolinkApiError(RuntimeError):
    """Raised when the Evolink API returns an error response."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Work with the Evolink async image generation API."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    submit_parser = subparsers.add_parser("submit", help="Submit an image task.")
    add_request_args(submit_parser)
    submit_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the payload without calling the API.",
    )

    poll_parser = subparsers.add_parser(
        "poll", help="Poll an existing task and optionally download results."
    )
    add_connection_args(poll_parser)
    poll_parser.add_argument("--task-id", required=True, help="Existing Evolink task id.")
    poll_parser.add_argument("--max-polls", type=int, default=40, help="Maximum number of poll attempts.")
    poll_parser.add_argument("--poll-sleep", type=int, default=3, help="Seconds between poll attempts.")
    poll_parser.add_argument(
        "--outdir",
        default=str(DEFAULT_OUTPUT_BASE),
        help="Base directory for run artifacts and downloaded images.",
    )
    poll_parser.add_argument(
        "--no-download",
        action="store_true",
        help="Do not download completed result URLs.",
    )

    generate_parser = subparsers.add_parser(
        "generate", help="Submit, poll, and download a completed image task."
    )
    add_request_args(generate_parser)
    generate_parser.add_argument("--max-polls", type=int, default=40, help="Maximum number of poll attempts.")
    generate_parser.add_argument("--poll-sleep", type=int, default=3, help="Seconds between poll attempts.")
    generate_parser.add_argument(
        "--outdir",
        default=str(DEFAULT_OUTPUT_BASE),
        help="Base directory for run artifacts and downloaded images.",
    )
    generate_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the request plan without calling the API.",
    )

    return parser.parse_args()


def add_connection_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="Evolink API base URL. Defaults to EVOLINK_API_BASE_URL or https://api.evolink.ai.",
    )


def add_request_args(parser: argparse.ArgumentParser) -> None:
    add_connection_args(parser)
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Image model name.")
    parser.add_argument("--prompt", required=True, help="Prompt text for the image request.")
    parser.add_argument("--size", default="1:1", help="Aspect ratio or WxH size.")
    parser.add_argument("--seed", type=int, help="Optional deterministic seed.")
    parser.add_argument(
        "--nsfw-check",
        action="store_true",
        help="Enable the provider's stricter NSFW moderation flag.",
    )
    parser.add_argument("--callback-url", help="Optional HTTPS callback URL for submit-only flows.")


def require_token() -> str:
    token = os.environ.get("EVOLINK_API_TOKEN", "").strip()
    if token:
        return token
    raise SystemExit("EVOLINK_API_TOKEN is required.")


def request_json(
    *,
    method: str,
    base_url: str,
    path: str,
    token: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    url = base_url.rstrip("/") + path
    data = None
    headers = {
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
        "Authorization": f"Bearer {token}",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise EvolinkApiError(format_http_error(exc.code, raw)) from exc
    except urllib.error.URLError as exc:
        raise EvolinkApiError(f"Request failed: {exc.reason}") from exc


def download_binary(url: str) -> tuple[bytes, str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            content_type = response.headers.get("Content-Type", "application/octet-stream")
            return response.read(), content_type
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise EvolinkApiError(format_http_error(exc.code, raw)) from exc
    except urllib.error.URLError as exc:
        raise EvolinkApiError(f"Download failed: {exc.reason}") from exc


def format_http_error(status_code: int, raw: str) -> str:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return f"HTTP {status_code}: {raw.strip() or 'Unknown error'}"

    error = payload.get("error")
    if isinstance(error, dict):
        code = error.get("code", "unknown_error")
        message = error.get("message", "Unknown error")
        return f"HTTP {status_code}: {code}: {message}"
    return f"HTTP {status_code}: {json.dumps(payload, ensure_ascii=True)}"


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": args.model,
        "prompt": args.prompt,
        "size": args.size,
    }
    if args.seed is not None:
        payload["seed"] = args.seed
    if args.nsfw_check:
        payload["nsfw_check"] = True
    if args.callback_url:
        payload["callback_url"] = args.callback_url
    return payload


def timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def prompt_slug(prompt: str) -> str:
    collapsed = re.sub(r"[^a-z0-9]+", "-", prompt.lower()).strip("-")
    if not collapsed:
        collapsed = "image"
    return collapsed[:48].rstrip("-") or "image"


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def infer_extension(url: str, content_type: str) -> str:
    parsed = urllib.parse.urlparse(url)
    suffix = Path(parsed.path).suffix.lower().lstrip(".")
    if suffix:
        return suffix
    content_type = content_type.split(";", 1)[0].strip().lower()
    guessed = mimetypes.guess_extension(content_type) or ".bin"
    return guessed.lstrip(".")


def run_directory_path(base_dir: Path, label: str) -> Path:
    return base_dir / f"{timestamp_slug()}-{label}"


def create_run_directory(base_dir: Path, label: str) -> Path:
    return ensure_directory(run_directory_path(base_dir, label))


def download_results(results: list[str], run_dir: Path) -> list[str]:
    files: list[str] = []
    for index, result_url in enumerate(results, start=1):
        data, content_type = download_binary(result_url)
        extension = infer_extension(result_url, content_type)
        destination = run_dir / f"result-{index:02d}.{extension}"
        destination.write_bytes(data)
        files.append(str(destination))
    return files


def task_summary(task: dict[str, Any], downloaded_files: list[str] | None = None) -> dict[str, Any]:
    summary = {
        "id": task.get("id"),
        "status": task.get("status"),
        "progress": task.get("progress"),
        "model": task.get("model"),
        "results": task.get("results", []),
        "error": task.get("error"),
    }
    if downloaded_files is not None:
        summary["downloaded_files"] = downloaded_files
    return summary


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=True))


def submit_command(args: argparse.Namespace) -> int:
    payload = build_payload(args)
    preview = {
        "base_url": args.base_url,
        "endpoint": "/v1/images/generations",
        "payload": payload,
    }
    if args.dry_run:
        print_json(preview)
        return 0

    token = require_token()
    response = request_json(
        method="POST",
        base_url=args.base_url,
        path="/v1/images/generations",
        token=token,
        payload=payload,
    )
    print_json(response)
    return 0


def poll_until_complete(
    *,
    base_url: str,
    token: str,
    task_id: str,
    max_polls: int,
    poll_sleep: int,
) -> dict[str, Any]:
    task_path = "/v1/tasks/" + urllib.parse.quote(task_id, safe="")
    latest: dict[str, Any] = {}
    for attempt in range(1, max_polls + 1):
        latest = request_json(
            method="GET",
            base_url=base_url,
            path=task_path,
            token=token,
        )
        status = str(latest.get("status", "pending"))
        progress = latest.get("progress", 0)
        print(f"[poll {attempt}/{max_polls}] status={status} progress={progress}", file=sys.stderr)
        if status in {"completed", "failed"}:
            return latest
        if attempt < max_polls and poll_sleep > 0:
            time.sleep(poll_sleep)
    raise EvolinkApiError(f"Task {task_id} did not complete within {max_polls} polls.")


def poll_command(args: argparse.Namespace) -> int:
    token = require_token()
    run_dir = create_run_directory(Path(args.outdir), args.task_id)
    task = poll_until_complete(
        base_url=args.base_url,
        token=token,
        task_id=args.task_id,
        max_polls=max(1, args.max_polls),
        poll_sleep=max(0, args.poll_sleep),
    )
    write_json(run_dir / "task-final.json", task)

    downloaded_files: list[str] | None = None
    if str(task.get("status")) == "completed" and not args.no_download:
        results = [url for url in task.get("results", []) if isinstance(url, str) and url]
        downloaded_files = download_results(results, run_dir)

    print_json(task_summary(task, downloaded_files))
    return 0


def generate_command(args: argparse.Namespace) -> int:
    payload = build_payload(args)
    label = prompt_slug(args.prompt)
    run_dir = run_directory_path(Path(args.outdir), label)

    if args.dry_run:
        print_json(
            {
                "base_url": args.base_url,
                "endpoint": "/v1/images/generations",
                "payload": payload,
                "run_dir": str(run_dir),
            }
        )
        return 0

    token = require_token()
    ensure_directory(run_dir)
    write_json(
        run_dir / "request.json",
        {
            "base_url": args.base_url,
            "endpoint": "/v1/images/generations",
            "payload": payload,
            "run_dir": str(run_dir),
        },
    )
    submitted = request_json(
        method="POST",
        base_url=args.base_url,
        path="/v1/images/generations",
        token=token,
        payload=payload,
    )
    write_json(run_dir / "task-submitted.json", submitted)

    task_id = str(submitted.get("id", "")).strip()
    if not task_id:
        raise EvolinkApiError("Submission response did not include a task id.")

    task = poll_until_complete(
        base_url=args.base_url,
        token=token,
        task_id=task_id,
        max_polls=max(1, args.max_polls),
        poll_sleep=max(0, args.poll_sleep),
    )
    write_json(run_dir / "task-final.json", task)

    downloaded_files: list[str] | None = None
    if str(task.get("status")) == "completed":
        results = [url for url in task.get("results", []) if isinstance(url, str) and url]
        downloaded_files = download_results(results, run_dir)

    print_json(task_summary(task, downloaded_files))
    return 0


def main() -> int:
    args = parse_args()
    try:
        if args.command == "submit":
            return submit_command(args)
        if args.command == "poll":
            return poll_command(args)
        if args.command == "generate":
            return generate_command(args)
    except EvolinkApiError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

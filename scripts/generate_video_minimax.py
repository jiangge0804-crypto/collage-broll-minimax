#!/usr/bin/env python3
"""
Generates videos using MiniMax H3 (Hailuo 3.0) first/last-frame image-to-video
via the MiniMax open platform V2 API (api.minimaxi.com, mainland-China direct).

- Async task flow: POST /v2/video_generation -> poll /v2/query/video_generation/{task_id}
- Auth: Authorization: Bearer $MINIMAX_API_KEY
- Images are inlined as base64 data URLs (first frame / last frame)
- Python standard library only; no third-party SDK required
- Supports parallel batch execution via ThreadPoolExecutor
"""

import argparse
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import mimetypes
import os
import re
import sys
import time
import urllib.request
import urllib.error

API_BASE = "https://api.minimaxi.com"
DEFAULT_MODEL = "MiniMax-H3"
DEFAULT_RESOLUTION = "768P"      # 768P is cheaper; 2K available via --resolution
POLL_INTERVAL = 5                # seconds between status polls
POLL_DEADLINE = 20 * 60          # give up after 20 minutes per task
MAX_INLINE_IMAGE_BYTES = 25 * 1024 * 1024  # docs: <=30MB per image, keep margin


def get_api_key(args):
    """Retrieves API key: --api-key arg > env var > .env file next to the skill."""
    if args.api_key:
        return args.api_key
    env_key = os.environ.get("MINIMAX_API_KEY")
    if env_key:
        return env_key
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("MINIMAX_API_KEY="):
                    return line.split("=", 1)[1].strip()
    return None


def slugify(text):
    """Converts a text prompt into a safe, descriptive filename slug."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_')[:50]


def parse_and_validate_duration(value):
    """Parses and validates a duration integer between 4 and 15 seconds (MiniMax H3 range)."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        val = float(value)
    else:
        clean_value = str(value).strip().lower()
        if clean_value in ('none', ''):
            return None
        if clean_value.endswith('s'):
            clean_value = clean_value[:-1]
        try:
            val = float(clean_value)
        except ValueError:
            raise ValueError(f"Invalid duration value: '{value}'. Must be an integer (e.g., 5, 10).")

    if not val.is_integer():
        raise ValueError(f"Duration must be an integer, not a float (e.g., got {value}).")

    val_int = int(val)
    if val_int < 4 or val_int > 15:
        raise ValueError(f"Duration must be between 4 and 15 seconds for MiniMax H3. Got {val_int}.")

    return val_int


def argparse_duration_type(value):
    """argparse type converter for validating duration."""
    if value is None or str(value).strip().lower() in ('none', ''):
        return None
    try:
        return parse_and_validate_duration(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError(str(e))


def encode_image_data_url(image_path):
    """Reads a local image and returns a base64 data URL."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    size = os.path.getsize(image_path)
    if size > MAX_INLINE_IMAGE_BYTES:
        raise RuntimeError(
            f"Image '{image_path}' is {size / (1024 * 1024):.1f} MB, too large to inline "
            f"(limit {MAX_INLINE_IMAGE_BYTES // (1024 * 1024)} MB). Compress it first."
        )

    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type or not mime_type.startswith("image/"):
        mime_type = "image/png"

    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def http_json_request(method, url, api_key, payload=None):
    """Minimal JSON HTTP helper with clear error surfacing."""
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {api_key}")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code} from {url}: {body}")


def create_task(prompt, first_frame, last_frame, ratio, duration, resolution, model, api_key):
    """Creates a MiniMax H3 first/last-frame video generation task. Returns task id."""
    content = [{"type": "text", "text": prompt}]

    if first_frame:
        content.append({
            "type": "image_url",
            "image_url": {"url": encode_image_data_url(first_frame)},
            "role": "first_frame",
        })
    if last_frame:
        content.append({
            "type": "image_url",
            "image_url": {"url": encode_image_data_url(last_frame)},
            "role": "last_frame",
        })

    has_frames = bool(first_frame or last_frame)
    payload = {
        "model": model,
        "content": content,
        "resolution": resolution,
        "duration": duration,
        # i2v ignores ratio and derives it from the input images; t2v requires an explicit ratio
        "ratio": "adaptive" if has_frames else ratio,
        "aigc_watermark": False,   # skill requires clean deliverables
    }

    resp = http_json_request("POST", f"{API_BASE}/v2/video_generation", api_key, payload)

    # MiniMax may wrap errors in base_resp even with HTTP 200
    base_resp = resp.get("base_resp") or {}
    if base_resp.get("status_code", 0) not in (0, None):
        raise RuntimeError(f"API error {base_resp.get('status_code')}: {base_resp.get('status_msg')}")

    task_id = resp.get("task_id")
    if not task_id:
        raise RuntimeError(f"No task_id in create response: {resp}")
    return task_id


def poll_task(task_id, api_key):
    """Polls task status until succeeded/failed. Returns the task object."""
    url = f"{API_BASE}/v2/query/video_generation/{task_id}"
    deadline = time.time() + POLL_DEADLINE
    last_status = None

    while time.time() < deadline:
        resp = http_json_request("GET", url, api_key)
        task = resp.get("task") or {}
        status = task.get("status")
        if status != last_status:
            print(f"Task {task_id} status: {status}")
            last_status = status

        if status == "succeeded":
            return task
        if status in ("failed", "cancelled"):
            err = task.get("error") or resp.get("base_resp") or task
            raise RuntimeError(f"Task {status}: {json.dumps(err, ensure_ascii=False)}")

        time.sleep(POLL_INTERVAL)

    raise RuntimeError(f"Task {task_id} did not finish within {POLL_DEADLINE // 60} minutes (last status: {last_status}).")


def download_video_file(video_url, output_path):
    """Downloads the generated MP4 in a memory-safe, chunked manner."""
    print(f"Downloading video to {output_path} ...")
    req = urllib.request.Request(video_url)
    try:
        with urllib.request.urlopen(req, timeout=480) as resp:
            parent_dir = os.path.dirname(output_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            with open(output_path, "wb") as f:
                while True:
                    chunk = resp.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
        print(f"Video saved to: {output_path}")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Error downloading video: {e.code} - {e.read().decode(errors='replace')}")


def generate_video(prompt, api_key, model=DEFAULT_MODEL, aspect_ratio="3:4", duration=5,
                   resolution=DEFAULT_RESOLUTION, first_frame=None, last_frame=None,
                   output_path="output.mp4"):
    """Creates a MiniMax task, waits for completion, downloads the MP4."""
    duration = parse_and_validate_duration(duration) or 5

    print(f"\nCreating MiniMax H3 task (model '{model}', {resolution})...")
    print(f"Prompt: '{prompt[:80]}{'...' if len(prompt) > 80 else ''}' | Ratio: {aspect_ratio} | Duration: {duration}s")
    print(f"First frame: {first_frame} | Last frame: {last_frame}")

    task_id = create_task(prompt, first_frame, last_frame, aspect_ratio, duration, resolution, model, api_key)
    print(f"Task created: {task_id}")

    task = poll_task(task_id, api_key)

    video_url = (task.get("content") or {}).get("url")
    if not video_url:
        raise RuntimeError(f"Task succeeded but no content.url in response: {task}")

    download_video_file(video_url, output_path)


def run_job(job, api_key):
    """Runs a single generation job inside a thread pool, catching exceptions."""
    prompt = job.get("prompt")
    if not prompt:
        print("Warning: Skipping job with empty prompt.", file=sys.stderr)
        return {"job": job, "status": "SKIPPED", "error": "Empty prompt"}

    aspect_ratio = job.get("aspect_ratio", "3:4")
    duration = job.get("duration")
    output_path = job.get("output")
    model = job.get("model", DEFAULT_MODEL)
    resolution = job.get("resolution", DEFAULT_RESOLUTION)

    # job["image"] = [first_frame, last_frame]; a single image is treated as last frame only
    images = job.get("image") or []
    if isinstance(images, str):
        images = [images]
    first_frame = images[0] if len(images) >= 2 else None
    last_frame = images[-1] if images else None

    if not last_frame:
        return {"job": job, "status": "SKIPPED", "error": "No image provided (need first/last frame)"}

    if not output_path:
        output_path = f"media/output_{slugify(prompt)}.mp4"

    print(f"[Parallel] Dispatching: '{prompt[:60]}' (Output: {output_path})")

    try:
        generate_video(
            prompt=prompt,
            api_key=api_key,
            model=model,
            aspect_ratio=aspect_ratio,
            duration=duration,
            resolution=resolution,
            first_frame=first_frame,
            last_frame=last_frame,
            output_path=output_path,
        )
        return {"job": job, "status": "SUCCESS", "output_path": output_path}
    except Exception as e:
        print(f"[Parallel] Failed: '{prompt[:60]}' - Error: {e}", file=sys.stderr)
        return {"job": job, "status": "FAILED", "error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Generate videos with MiniMax H3 first/last-frame API (api.minimaxi.com V2, stdlib only, parallel batch)."
    )
    parser.add_argument("prompt", nargs="?", help="Text prompt for a single video generation")
    parser.add_argument("--image", action="append",
                        help="Local frame image path. Two images = first frame + last frame; one image = last frame only (can be specified multiple times)")
    parser.add_argument("--aspect-ratio", default="3:4", choices=["16:9", "9:16", "1:1", "4:3", "3:4", "21:9", "adaptive"],
                        help="Aspect ratio for text-to-video; ignored for first/last-frame mode (derived from images, default 3:4)")
    parser.add_argument("--duration", type=argparse_duration_type, default=5,
                        help="Video duration in seconds, integer 4-15 (default: 5)")
    parser.add_argument("--resolution", default=DEFAULT_RESOLUTION, choices=["768P", "2K"],
                        help="Output resolution (default: 768P; 2K costs more)")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"MiniMax model name (default: {DEFAULT_MODEL})")
    parser.add_argument("--output", help="Local output file path for single generation (default: media/output.mp4)")
    parser.add_argument("--api-key", help="MiniMax API Key (overrides MINIMAX_API_KEY env)")
    parser.add_argument("--batch", help="Path to a JSON file containing an array of generation jobs")
    parser.add_argument("--prompts-file", help="Path to a text file containing one prompt per line to run in parallel")
    parser.add_argument("--concurrency", type=int, default=3, help="Maximum concurrent tasks (default: 3)")

    args = parser.parse_args()

    api_key = get_api_key(args)
    if not api_key:
        print("Error: API key is not set. Use --api-key or set MINIMAX_API_KEY environment variable.\n"
              "Get one at: https://platform.minimaxi.com/user-center/basic-information/interface-key", file=sys.stderr)
        sys.exit(1)

    jobs = []

    # 1. Batch JSON
    if args.batch:
        if not os.path.exists(args.batch):
            print(f"Error: Batch JSON file '{args.batch}' not found.", file=sys.stderr)
            sys.exit(1)
        try:
            with open(args.batch, "r", encoding="utf-8") as f:
                jobs = json.load(f)
            if not isinstance(jobs, list):
                print("Error: Batch JSON file must contain a list/array of job objects.", file=sys.stderr)
                sys.exit(1)
        except Exception as e:
            print(f"Error parsing Batch JSON: {e}", file=sys.stderr)
            sys.exit(1)
        print(f"Loaded {len(jobs)} jobs from batch JSON. Running with concurrency={args.concurrency}...")

    # 2. Prompts file
    elif args.prompts_file:
        if not os.path.exists(args.prompts_file):
            print(f"Error: Prompts file '{args.prompts_file}' not found.", file=sys.stderr)
            sys.exit(1)
        with open(args.prompts_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    jobs.append({
                        "prompt": line,
                        "aspect_ratio": args.aspect_ratio,
                        "duration": args.duration,
                        "resolution": args.resolution,
                        "image": args.image,
                        "model": args.model,
                    })
        print(f"Loaded {len(jobs)} prompts from text file. Running with concurrency={args.concurrency}...")

    # 3. Single prompt
    else:
        if not args.prompt:
            parser.print_help()
            sys.exit(1)

        images = args.image or []
        first_frame = images[0] if len(images) >= 2 else None
        last_frame = images[-1] if images else None
        if not last_frame:
            print("Error: single generation needs at least one --image (last frame).", file=sys.stderr)
            sys.exit(1)

        output_path = args.output if args.output else "media/output.mp4"
        try:
            generate_video(
                prompt=args.prompt,
                api_key=api_key,
                model=args.model,
                aspect_ratio=args.aspect_ratio,
                duration=args.duration,
                resolution=args.resolution,
                first_frame=first_frame,
                last_frame=last_frame,
                output_path=output_path,
            )
            sys.exit(0)
        except Exception as e:
            print(f"Error: Generation failed: {e}", file=sys.stderr)
            sys.exit(1)

    # Parallel execution loop
    if not jobs:
        print("Warning: No valid jobs found to execute.")
        sys.exit(0)

    results = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = {executor.submit(run_job, job, api_key): job for job in jobs}
        for future in as_completed(futures):
            results.append(future.result())

    print("\n" + "=" * 50)
    print("BATCH PARALLEL EXECUTION SUMMARY")
    print("=" * 50)
    success_count = sum(1 for r in results if r["status"] == "SUCCESS")
    failed_count = sum(1 for r in results if r["status"] == "FAILED")
    skipped_count = sum(1 for r in results if r["status"] == "SKIPPED")

    print(f"Total: {len(results)} | Success: {success_count} | Failed: {failed_count} | Skipped: {skipped_count}\n")
    for r in results:
        status_str = r["status"]
        prompt = r["job"].get("prompt")
        if r["status"] == "SUCCESS":
            print(f"  [{status_str}] '{prompt[:60]}' -> {r['output_path']}")
        else:
            print(f"  [{status_str}] '{prompt[:60]}' -> Error: {r.get('error')}")
    print("=" * 50)

    if failed_count > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()

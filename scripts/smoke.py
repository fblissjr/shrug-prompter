"""Live smoke test against heylookitsanllm over the LAN.

Exercises every endpoint ShrugClient talks to, prints per-call latency.
Safe to re-run. Admin endpoints are skipped unless --admin-token is passed.

Usage:
    uv run python scripts/smoke.py --base-url https://your-llm-host --model qwen3-vl
    uv run python scripts/smoke.py --base-url https://your-llm-host --model qwen3-vl --admin-token <token>
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import io
import sys
import time
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from client import ChatMessage, ShrugClient  # noqa: E402


def _make_jpeg(size: int = 64) -> bytes:
    img = Image.new("RGB", (size, size), color=(120, 160, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


async def _time(label: str, coro):
    start = time.perf_counter()
    try:
        result = await coro
        dt = (time.perf_counter() - start) * 1000
        print(f"  [OK  {dt:7.1f} ms] {label}")
        return result
    except Exception as e:
        dt = (time.perf_counter() - start) * 1000
        print(f"  [ERR {dt:7.1f} ms] {label}: {e.__class__.__name__}: {e}")
        return None


async def run(base_url: str, model: str, api_key: str | None, admin_token: str | None) -> None:
    client = ShrugClient(base_url=base_url, api_key=api_key, admin_token=admin_token, timeout=60.0)
    print(f"\nheylookitsanllm smoke test → {base_url}")
    print("-" * 60)

    print("\n[discovery]")
    models = await _time("GET /v1/models", client.models())
    if models:
        print("         found:", ", ".join(m.id for m in models[:5]), ("..." if len(models) > 5 else ""))
    await _time("GET /v1/capabilities", client.capabilities())

    print("\n[inference]")
    await _time(
        "POST /v1/chat/completions (text)",
        client.chat(
            messages=[ChatMessage(role="user", content="ping")],
            model=model,
            max_tokens=16,
        ),
    )

    jpeg = _make_jpeg()
    data_url = f"data:image/jpeg;base64,{base64.b64encode(jpeg).decode()}"
    await _time(
        "POST /v1/chat/completions (vision base64)",
        client.chat(
            messages=[
                ChatMessage(
                    role="user",
                    content=[
                        {"type": "text", "text": "one word: what color?"},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                )
            ],
            model=model,
            max_tokens=16,
        ),
    )

    await _time(
        "POST /v1/chat/completions/multipart",
        client.chat_multipart(
            messages=[ChatMessage(role="user", content="one word: what color?")],
            images=[jpeg],
            model=model,
            max_tokens=16,
        ),
    )

    await _time(
        "POST /v1/batch/chat/completions",
        client.chat_batch([
            {"messages": [{"role": "user", "content": "say 'a'"}], "model": model, "max_tokens": 8},
            {"messages": [{"role": "user", "content": "say 'b'"}], "model": model, "max_tokens": 8},
        ]),
    )

    await _time(
        "POST /v1/embeddings",
        client.embed(["hello"], model=model),
    )

    print("\n[cache]")
    await _time("GET /v1/cache/list", client.cache_list())
    if admin_token:
        await _time("POST /v1/cache/clear", client.cache_clear())
    else:
        print("  [skip] POST /v1/cache/clear (pass --admin-token to test)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--api-key", default=None)
    ap.add_argument("--admin-token", default=None)
    args = ap.parse_args()
    asyncio.run(run(args.base_url, args.model, args.api_key, args.admin_token))
    return 0


if __name__ == "__main__":
    sys.exit(main())

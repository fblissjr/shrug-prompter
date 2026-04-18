"""ComfyUI nodes for heylookitsanllm.

Uses the V3 declarative API (`io.ComfyNode` + `define_schema` + async execute).
Mirrors the patterns in `coderef/ComfyUI-AudioLoopHelper/nodes.py`.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import orjson
import torch
from typing_extensions import override

try:
    from comfy_api.latest import ComfyExtension, io
except ImportError:
    # Outside ComfyUI runtime (pytest). Provide stubs so nodes remain testable.
    class _Passthrough:
        def __getattr__(self, _name):
            return _Passthrough()

        def __call__(self, *args, **kwargs):
            return _Passthrough()

    class _IOStub(_Passthrough):
        class ComfyNode:
            pass

        @staticmethod
        def NodeOutput(*args):
            return args

    ComfyExtension = type("ComfyExtension", (), {})
    io = _IOStub()

# Dual-form imports so this file works both as part of the ComfyUI package
# (`from .client import ...`) and as a top-level module under pytest
# (`from client import ...`). Mirrors AudioLoopHelper's pattern but explicit —
# AudioLoopHelper avoids the problem by doing sibling imports inside methods.
try:
    from .client import ChatMessage, ChatResult, ShrugClient
    from .media import (
        audio_dict_to_wav_bytes,
        tensor_batch_to_jpeg_bytes,
        tensor_to_data_url_list,
    )
except ImportError:
    from client import ChatMessage, ChatResult, ShrugClient  # type: ignore[no-redef]
    from media import (  # type: ignore[no-redef]
        audio_dict_to_wav_bytes,
        tensor_batch_to_jpeg_bytes,
        tensor_to_data_url_list,
    )

CATEGORY = "shrug"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
_CLEANUP_LEVELS = ("none", "basic", "standard", "strict")


@dataclass
class ShrugConnection:
    """Bundles a ShrugClient with the selected model. Emitted as SHRUG_CONN."""

    client: ShrugClient
    model: str


def _clean_text(text: str, level: str) -> str:
    """Levels: none (as-is), basic (trim), standard (+unicode NFC + collapse blanks), strict (ASCII)."""
    if level == "none":
        return text
    out = text.strip()
    if level == "basic":
        return out
    out = unicodedata.normalize("NFC", out)
    # Collapse runs of blank lines to a single blank line.
    out = "\n".join(line.rstrip() for line in out.splitlines())
    while "\n\n\n" in out:
        out = out.replace("\n\n\n", "\n\n")
    if level == "standard":
        return out
    # strict: ASCII-only
    return out.encode("ascii", errors="ignore").decode("ascii")


def _list_template_files() -> list[str]:
    if not TEMPLATES_DIR.exists():
        return []
    paths = sorted(p for p in TEMPLATES_DIR.rglob("*.md") if p.is_file())
    return [str(p.relative_to(TEMPLATES_DIR)) for p in paths]


def _parse_inline_list(raw: str) -> list[str] | None:
    """Parse `[a, b, c]` into a list, else None."""
    raw = raw.strip()
    if not (raw.startswith("[") and raw.endswith("]")):
        return None
    inner = raw[1:-1].strip()
    if not inner:
        return []
    return [item.strip() for item in inner.split(",")]


def _parse_frontmatter_lines(lines: list[str]) -> dict[str, Any]:
    """Parse a small YAML-ish subset: `key: scalar`, `key: |` block, `key: [a, b]`.

    Intentionally minimal — no flow mappings, no anchors, no type coercion
    beyond int/float. Adding pyyaml would be overkill for ComfyUI single-user.
    """
    data: dict[str, Any] = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.rstrip()
        if not stripped.strip() or stripped.lstrip().startswith("#"):
            i += 1
            continue
        if ":" not in stripped:
            i += 1
            continue
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()
        if value == "|":
            i += 1
            block: list[str] = []
            base_indent: int | None = None
            while i < len(lines):
                raw = lines[i]
                if raw.strip() == "":
                    block.append("")
                    i += 1
                    continue
                indent = len(raw) - len(raw.lstrip())
                if base_indent is None:
                    if indent == 0:
                        break
                    base_indent = indent
                if indent < base_indent:
                    break
                block.append(raw[base_indent:].rstrip())
                i += 1
            data[key] = "\n".join(block).strip("\n")
            continue
        parsed_list = _parse_inline_list(value)
        if parsed_list is not None:
            data[key] = parsed_list
        else:
            data[key] = value
        i += 1
    return data


def parse_template(raw: str) -> tuple[dict[str, Any], str, str, str]:
    """Split a template into (metadata, system_prompt, user_prompt, body).

    Templates may start with a `---`...`---` frontmatter block. Frontmatter
    keys `system` and `user` (block scalars) become the system/user
    outputs. Everything after the closing `---` is `body`. If no
    frontmatter is present, the entire input is `body` and the others are "".
    """
    if not raw.startswith("---"):
        return {}, "", "", raw
    rest = raw[3:]
    if rest.startswith("\n"):
        rest = rest[1:]
    # Find closing `---` on its own line.
    closing_idx = -1
    for match_start in range(len(rest)):
        if rest.startswith("---", match_start):
            before = rest[match_start - 1] if match_start > 0 else "\n"
            after_end = match_start + 3
            after = rest[after_end] if after_end < len(rest) else "\n"
            if before == "\n" and after in ("\n", ""):
                closing_idx = match_start
                break
    if closing_idx == -1:
        return {}, "", "", raw
    fm_raw = rest[:closing_idx].rstrip("\n")
    body = rest[closing_idx + 3 :]
    if body.startswith("\n"):
        body = body[1:]
    meta = _parse_frontmatter_lines(fm_raw.splitlines())
    system = str(meta.get("system", ""))
    user = str(meta.get("user", ""))
    return meta, system, user, body


def _chat_messages_with_images(
    system_prompt: str,
    user_prompt: str,
    image_urls: list[str],
) -> list[ChatMessage]:
    messages: list[ChatMessage] = []
    if system_prompt.strip():
        messages.append(ChatMessage(role="system", content=system_prompt))
    if image_urls:
        content: list[dict] = [{"type": "text", "text": user_prompt}]
        for url in image_urls:
            content.append({"type": "image_url", "image_url": {"url": url}})
        messages.append(ChatMessage(role="user", content=content))
    else:
        messages.append(ChatMessage(role="user", content=user_prompt))
    return messages


# ---------- Nodes ----------


class ShrugConnectionNode(io.ComfyNode):
    """Connection config for heylookitsanllm. Emits a SHRUG_CONN object downstream."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="ShrugConnection",
            display_name="Shrug Connection",
            category=CATEGORY,
            description="Base URL, model, and optional auth for heylookitsanllm.",
            inputs=[
                io.String.Input(
                    "base_url",
                    default="http://localhost:8080",
                    tooltip="Base URL of the heylookitsanllm server. Localhost by default; set to https://your-host for LAN use.",
                ),
                io.String.Input(
                    "model",
                    default="",
                    tooltip="Model id. JS widget populates a dropdown via /shrug/get_models.",
                ),
                io.String.Input(
                    "api_key",
                    default="",
                    advanced=True,
                    tooltip="Optional. Sent as `Authorization: Bearer <key>`. Ignored by vanilla heylookitsanllm.",
                ),
                io.String.Input(
                    "admin_token",
                    default="",
                    advanced=True,
                    tooltip="Optional. Sent as `X-Heylook-Admin-Token` on admin endpoints only.",
                ),
                io.Int.Input(
                    "timeout",
                    default=300,
                    min=5,
                    max=1800,
                    advanced=True,
                    tooltip="Request timeout in seconds.",
                ),
            ],
            outputs=[io.Custom("SHRUG_CONN").Output("connection")],
        )

    @classmethod
    def execute(cls, base_url, model, api_key, admin_token, timeout) -> io.NodeOutput:
        if not model.strip():
            raise ValueError("ShrugConnection: model is required.")
        client = ShrugClient(
            base_url=base_url,
            api_key=api_key or None,
            admin_token=admin_token or None,
            timeout=float(timeout),
        )
        return io.NodeOutput(ShrugConnection(client=client, model=model))


class ShrugTemplate(io.ComfyNode):
    """Load a prompt template from `templates/`.

    Templates may start with a YAML-ish frontmatter block (`---` delimited)
    declaring `name`, `description`, `system:`, `user:`, etc. Block scalars
    (`system: |` + indent) are supported. Pattern borrowed from
    coderef/llm-dit-experiments/presets/.
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        files = _list_template_files() or ["(no templates found)"]
        return io.Schema(
            node_id="ShrugTemplate",
            display_name="Shrug Template",
            category=CATEGORY,
            description=f"Load a Markdown template from {TEMPLATES_DIR.name}/.",
            inputs=[
                io.Combo.Input("template", options=files),
            ],
            outputs=[
                io.String.Output("system"),
                io.String.Output("user"),
                io.String.Output("body"),
                io.String.Output("description"),
                io.String.Output("metadata"),
            ],
        )

    @classmethod
    def execute(cls, template) -> io.NodeOutput:
        path = TEMPLATES_DIR / template
        try:
            raw = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return io.NodeOutput("", "", "", "", "{}")
        meta, system, user, body = parse_template(raw)
        description = str(meta.get("description", ""))
        metadata_json = orjson.dumps(meta).decode()
        return io.NodeOutput(system, user, body.strip("\n"), description, metadata_json)


class ShrugTextCleanup(io.ComfyNode):
    """Normalize whitespace, unicode, or ASCII-strip a string."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="ShrugTextCleanup",
            display_name="Shrug Text Cleanup",
            category=CATEGORY,
            inputs=[
                io.String.Input("text", multiline=True, default=""),
                io.Combo.Input(
                    "level",
                    options=list(_CLEANUP_LEVELS),
                    default="standard",
                ),
            ],
            outputs=[io.String.Output("text")],
        )

    @classmethod
    def execute(cls, text, level) -> io.NodeOutput:
        return io.NodeOutput(_clean_text(text, level))


class ShrugAccumulator(io.ComfyNode):
    """Graph-scoped accumulator for strings.

    State is keyed by the node's `unique_id` so each instance in the graph has
    its own list. Modes: append, reset, read, pick. Mirrors the pattern in
    coderef/ComfyUI-AudioLoopHelper/nodes.py.
    """

    _state: dict[str, list[str]] = {}

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="ShrugAccumulator",
            display_name="Shrug Accumulator",
            category=CATEGORY,
            inputs=[
                io.Combo.Input("mode", options=["append", "reset", "read", "pick"], default="append"),
                io.String.Input("text", multiline=True, default="", optional=True),
                io.Int.Input("index", default=0, min=0, optional=True, advanced=True),
                io.String.Input("delimiter", default="\n", advanced=True),
            ],
            outputs=[
                io.String.Output("joined"),
                io.String.Output("picked"),
                io.Int.Output("count"),
            ],
            hidden=[io.Hidden.unique_id],
        )

    @classmethod
    def execute(cls, mode, text, index, delimiter, unique_id) -> io.NodeOutput:
        key = str(unique_id)
        buf = cls._state.setdefault(key, [])
        if mode == "reset":
            buf.clear()
        elif mode == "append":
            if text:
                buf.append(text)
        picked = buf[index] if (mode == "pick" and 0 <= index < len(buf)) else ""
        joined = delimiter.join(buf)
        return io.NodeOutput(joined, picked, len(buf))


class ShrugASR(io.ComfyNode):
    """Transcribe audio via heylookitsanllm `/v1/audio/transcriptions`."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="ShrugASR",
            display_name="Shrug ASR",
            category=CATEGORY,
            is_api_node=True,
            inputs=[
                io.Custom("SHRUG_CONN").Input("connection"),
                io.Audio.Input("audio"),
            ],
            outputs=[io.String.Output("text")],
        )

    @classmethod
    async def execute(cls, connection: ShrugConnection, audio: dict) -> io.NodeOutput:
        wav = audio_dict_to_wav_bytes(audio)
        text = await connection.client.transcribe(wav, model=connection.model)
        return io.NodeOutput(text)


class ShrugEmbeddings(io.ComfyNode):
    """Embed text via heylookitsanllm `/v1/embeddings`. Emits SHRUG_EMBEDDINGS (torch.Tensor)."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="ShrugEmbeddings",
            display_name="Shrug Embeddings",
            category=CATEGORY,
            is_api_node=True,
            inputs=[
                io.Custom("SHRUG_CONN").Input("connection"),
                io.String.Input("text", multiline=True, default=""),
            ],
            outputs=[io.Custom("SHRUG_EMBEDDINGS").Output("embeddings")],
        )

    @classmethod
    async def execute(cls, connection: ShrugConnection, text: str) -> io.NodeOutput:
        tensor = await connection.client.embed([text], model=connection.model)
        return io.NodeOutput(tensor)


class ShrugVLM(io.ComfyNode):
    """Primary VLM/chat node. Calls /v1/chat/completions or /multipart based on `transport`."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="ShrugVLM",
            display_name="Shrug VLM",
            category=CATEGORY,
            is_api_node=True,
            description="Chat/vision call to heylookitsanllm. Images optional.",
            inputs=[
                io.Custom("SHRUG_CONN").Input("connection"),
                io.String.Input("user_prompt", multiline=True, default=""),
                io.String.Input("system_prompt", multiline=True, default="", advanced=True),
                io.Image.Input("images", optional=True),
                io.Int.Input("max_tokens", default=1024, min=1, max=32000),
                io.Float.Input("temperature", default=0.7, min=0.0, max=2.0, step=0.01),
                io.Float.Input("top_p", default=1.0, min=0.0, max=1.0, step=0.01, advanced=True),
                io.Int.Input("top_k", default=0, min=0, advanced=True),
                io.Float.Input("min_p", default=0.0, min=0.0, max=1.0, step=0.01, advanced=True),
                io.Float.Input(
                    "repetition_penalty", default=1.0, min=0.0, max=2.0, step=0.01, advanced=True
                ),
                io.Int.Input("seed", default=-1, min=-1, advanced=True),
                io.Boolean.Input("enable_thinking", default=False, advanced=True),
                io.Combo.Input(
                    "transport",
                    options=["base64", "multipart"],
                    default="base64",
                    advanced=True,
                    tooltip="multipart is ~57ms/image faster but requires server support.",
                ),
                io.Int.Input(
                    "image_resize_max",
                    default=0,
                    min=0,
                    max=4096,
                    advanced=True,
                    tooltip="If >0, longest edge is resized to this before upload.",
                ),
                io.Int.Input(
                    "image_quality", default=85, min=20, max=100, advanced=True,
                ),
            ],
            outputs=[
                io.String.Output("response"),
                io.String.Output("thinking"),
            ],
        )

    @classmethod
    async def execute(
        cls,
        connection: ShrugConnection,
        user_prompt,
        system_prompt,
        images,
        max_tokens,
        temperature,
        top_p,
        top_k,
        min_p,
        repetition_penalty,
        seed,
        enable_thinking,
        transport,
        image_resize_max,
        image_quality,
    ) -> io.NodeOutput:
        resize = image_resize_max if image_resize_max > 0 else None
        result = await _call_vlm(
            conn=connection,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            images=images,
            transport=transport,
            resize_max=resize,
            quality=image_quality,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            min_p=min_p,
            repetition_penalty=repetition_penalty,
            seed=seed,
            enable_thinking=enable_thinking,
        )
        return io.NodeOutput(result.text, result.thinking)


async def _call_vlm(
    conn: ShrugConnection,
    system_prompt: str,
    user_prompt: str,
    images: torch.Tensor | None,
    transport: str,
    resize_max: int | None,
    quality: int,
    **params,
) -> ChatResult:
    """Shared code path for ShrugVLM and ShrugVLMBatch."""
    has_images = images is not None and (hasattr(images, "shape") and images.numel() > 0)
    if has_images and transport == "multipart":
        raw_bytes = tensor_batch_to_jpeg_bytes(images, quality=quality, resize_max=resize_max)
        messages = _chat_messages_with_images(system_prompt, user_prompt, image_urls=[])
        # Multipart doesn't share chat()'s "omit defaults" logic, so forward
        # the rest of the sampling params verbatim. The server ignores any
        # extra fields it doesn't understand.
        extra = {
            k: v
            for k, v in params.items()
            if k not in ("max_tokens", "temperature", "top_p")
        }
        return await conn.client.chat_multipart(
            messages=messages,
            images=raw_bytes,
            model=conn.model,
            max_tokens=params.get("max_tokens", 1024),
            temperature=params.get("temperature", 0.7),
            top_p=params.get("top_p", 1.0),
            extra_fields=extra or None,
        )
    image_urls: list[str] = []
    if has_images:
        image_urls = tensor_to_data_url_list(images, quality=quality, resize_max=resize_max)
    messages = _chat_messages_with_images(system_prompt, user_prompt, image_urls)
    return await conn.client.chat(messages=messages, model=conn.model, **params)


class ShrugVLMBatch(io.ComfyNode):
    """Batched chat calls via `/v1/batch/chat/completions`.

    `user_prompts` is a newline-separated list (one prompt per line). Images
    are optional; if provided, the batch is zipped: prompt[i] with image[i].
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="ShrugVLMBatch",
            display_name="Shrug VLM Batch",
            category=CATEGORY,
            is_api_node=True,
            description="Sends N prompts (and optional N images) in one request. 2-4x throughput.",
            inputs=[
                io.Custom("SHRUG_CONN").Input("connection"),
                io.String.Input(
                    "user_prompts",
                    multiline=True,
                    default="",
                    tooltip="One prompt per line. Empty lines are ignored.",
                ),
                io.String.Input("system_prompt", multiline=True, default="", advanced=True),
                io.Image.Input("images", optional=True),
                io.Int.Input("max_tokens", default=1024, min=1, max=32000),
                io.Float.Input("temperature", default=0.7, min=0.0, max=2.0, step=0.01),
                io.Int.Input(
                    "image_resize_max", default=512, min=0, max=4096, advanced=True,
                ),
                io.Int.Input("image_quality", default=85, min=20, max=100, advanced=True),
            ],
            outputs=[
                io.String.Output("responses", is_output_list=True),
                io.Int.Output("count"),
            ],
        )

    @classmethod
    async def execute(
        cls,
        connection: ShrugConnection,
        user_prompts,
        system_prompt,
        images,
        max_tokens,
        temperature,
        image_resize_max,
        image_quality,
    ) -> io.NodeOutput:
        prompts = [p for p in user_prompts.splitlines() if p.strip()]
        if not prompts:
            return io.NodeOutput([], 0)

        resize = image_resize_max if image_resize_max > 0 else None
        has_images = images is not None and hasattr(images, "shape") and images.numel() > 0
        image_urls_per_prompt: list[list[str]] = [[] for _ in prompts]
        if has_images:
            urls = tensor_to_data_url_list(images, quality=image_quality, resize_max=resize)
            for i, url in enumerate(urls):
                if i < len(prompts):
                    image_urls_per_prompt[i] = [url]

        requests: list[dict] = []
        for prompt, urls in zip(prompts, image_urls_per_prompt):
            messages = _chat_messages_with_images(system_prompt, prompt, urls)
            requests.append({
                "model": connection.model,
                "messages": [m.to_dict() for m in messages],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False,
            })
        results = await connection.client.chat_batch(requests)
        return io.NodeOutput([r.text for r in results], len(results))


class ShrugFramePair(io.ComfyNode):
    """Select a (start, end) frame pair from a video-style IMAGE batch."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="ShrugFramePair",
            display_name="Shrug Frame Pair",
            category=CATEGORY,
            inputs=[
                io.Image.Input("images"),
                io.Combo.Input(
                    "mode",
                    options=["sequential_pairs", "first_to_each"],
                    default="sequential_pairs",
                ),
                io.Int.Input("pair_index", default=0, min=0),
                io.Int.Input("stride", default=1, min=1, max=32, advanced=True),
            ],
            outputs=[
                io.Image.Output("start_frame"),
                io.Image.Output("end_frame"),
                io.Int.Output("total_pairs"),
            ],
        )

    @classmethod
    def execute(cls, images, mode, pair_index, stride) -> io.NodeOutput:
        if images.dim() != 4:
            raise ValueError(f"expected (B,H,W,C) image batch, got shape {tuple(images.shape)}")
        n = images.shape[0]
        if mode == "sequential_pairs":
            total = max(0, (n - 1) // stride)
            start_idx = min(pair_index * stride, max(0, n - 2))
            end_idx = min(start_idx + stride, n - 1)
        else:  # first_to_each
            total = max(0, n - 1)
            start_idx = 0
            end_idx = min(pair_index + 1, n - 1)
        return io.NodeOutput(images[start_idx : start_idx + 1], images[end_idx : end_idx + 1], total)


class ShrugCacheControl(io.ComfyNode):
    """List or clear the server's prompt/KV cache. Pairs with ShrugConnection."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="ShrugCacheControl",
            display_name="Shrug Cache Control",
            category=CATEGORY,
            is_api_node=True,
            inputs=[
                io.Custom("SHRUG_CONN").Input("connection"),
                io.Combo.Input("action", options=["list", "clear"], default="list"),
            ],
            outputs=[io.String.Output("info")],
        )

    @classmethod
    async def execute(cls, connection: ShrugConnection, action) -> io.NodeOutput:
        if action == "clear":
            await connection.client.cache_clear()
            return io.NodeOutput("cache cleared")
        info = await connection.client.cache_list()
        return io.NodeOutput(orjson.dumps(info).decode())


class ShrugExtension(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type]:
        return [
            ShrugConnectionNode,
            ShrugTemplate,
            ShrugTextCleanup,
            ShrugAccumulator,
            ShrugASR,
            ShrugEmbeddings,
            ShrugVLM,
            ShrugVLMBatch,
            ShrugFramePair,
            ShrugCacheControl,
        ]


def comfy_entrypoint() -> ShrugExtension:
    return ShrugExtension()

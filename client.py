"""Async HTTP client for heylookitsanllm.

Single-user, LAN-only. No retries, no elaborate capability caching. The server
is close and usually up; if it isn't, fail fast and let the user notice.

Auth model:
- Inference endpoints (chat, multipart, batch, embed, transcribe, models,
  capabilities, cache_list): `api_key` -> `Authorization: Bearer <key>` if set,
  else no auth header.
- Admin endpoints (cache_clear): `admin_token` -> `X-Heylook-Admin-Token` if set.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from typing import Any, Iterable

import httpx
import orjson
import torch

_ADMIN_HEADER = "X-Heylook-Admin-Token"
_THINK_RE = re.compile(r"^\s*<think>(.*?)</think>\s*(.*)$", re.DOTALL)


@dataclass
class ChatMessage:
    role: str
    content: str | list[dict]

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


@dataclass
class ChatResult:
    text: str
    thinking: str = ""


@dataclass
class ModelInfo:
    id: str
    vision: bool = False


def extract_thinking(content: str) -> tuple[str, str]:
    """Split a response into (visible_text, thinking). Handles leading `<think>` blocks."""
    if not content:
        return "", ""
    match = _THINK_RE.match(content)
    if match:
        return match.group(2).strip(), match.group(1).strip()
    return content, ""


def _parse_chat_response(payload: dict) -> ChatResult:
    choice = payload["choices"][0]
    message = choice.get("message", {})
    raw_content = message.get("content", "") or ""
    thinking = message.get("thinking", "") or ""
    if thinking:
        return ChatResult(text=raw_content, thinking=thinking)
    text, extracted = extract_thinking(raw_content)
    return ChatResult(text=text, thinking=extracted)


class ShrugClient:
    """Thin async client for heylookitsanllm endpoints."""

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        admin_token: str | None = None,
        timeout: float = 300.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or None
        self.admin_token = admin_token or None
        self.timeout = timeout
        self._http: httpx.AsyncClient | None = None
        self._http_loop: asyncio.AbstractEventLoop | None = None

    def _inference_headers(self, content_type: str | None = "application/json") -> dict[str, str]:
        headers: dict[str, str] = {}
        if content_type is not None:
            headers["Content-Type"] = content_type
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _admin_headers(self) -> dict[str, str]:
        headers = self._inference_headers()
        if self.admin_token:
            headers[_ADMIN_HEADER] = self.admin_token
        return headers

    def _client(self) -> httpx.AsyncClient:
        # Keep-alive across calls for the same ShrugClient instance. A new
        # ShrugClient is built per ComfyUI graph run, so TLS/TCP cost pays
        # off across all inference nodes in a single workflow.
        #
        # ComfyUI spins up a fresh asyncio loop per prompt execution but may
        # reuse a cached ShrugConnection output (and its ShrugClient) across
        # runs. Pooled connections bound to the prior loop can't be cleaned
        # up on the new loop — that surfaces as "Event loop is closed" on
        # every other run. Track the loop the client was created on and
        # drop it when it changes.
        loop = asyncio.get_running_loop()
        if self._http is None or self._http.is_closed or self._http_loop is not loop:
            self._discard_http()
            self._http = httpx.AsyncClient(timeout=self.timeout)
            self._http_loop = loop
        return self._http

    def _discard_http(self) -> None:
        """Release the previous httpx client without blocking the new loop.

        In ComfyUI the old loop is almost always already closed by the time
        we notice — its transports went down with it, so dropping the
        reference is the whole job. If the old loop is somehow still alive
        (tests, embedded use), best-effort schedule a clean aclose on it so
        we don't leak sockets or leave httpx's __del__ to surface warnings.
        """
        old, old_loop = self._http, self._http_loop
        self._http = None
        self._http_loop = None
        if old is None or old_loop is None or old_loop.is_closed():
            return
        try:
            old_loop.call_soon_threadsafe(lambda: old_loop.create_task(old.aclose()))
        except RuntimeError:
            pass  # Loop died between is_closed() check and scheduling — drop.

    async def aclose(self) -> None:
        if self._http is not None:
            await self._http.aclose()
            self._http = None
            self._http_loop = None

    async def _post_json(self, path: str, body: dict, headers: dict | None = None) -> dict:
        http = self._client()
        resp = await http.post(
            f"{self.base_url}{path}",
            content=orjson.dumps(body),
            headers=headers or self._inference_headers(),
        )
        resp.raise_for_status()
        return orjson.loads(resp.content)

    async def _get_json(self, path: str, headers: dict | None = None) -> dict:
        http = self._client()
        resp = await http.get(
            f"{self.base_url}{path}",
            headers=headers or self._inference_headers(content_type=None),
        )
        resp.raise_for_status()
        return orjson.loads(resp.content)

    async def chat(
        self,
        messages: Iterable[ChatMessage | dict],
        model: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: float = 1.0,
        top_k: int = 0,
        min_p: float = 0.0,
        repetition_penalty: float = 1.0,
        seed: int = -1,
        enable_thinking: bool = False,
        extra: dict[str, Any] | None = None,
    ) -> ChatResult:
        """Call `/v1/chat/completions`. Omits optional params at their default."""
        body: dict[str, Any] = {
            "model": model,
            "messages": [m.to_dict() if isinstance(m, ChatMessage) else m for m in messages],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stream": False,
        }
        if top_k > 0:
            body["top_k"] = top_k
        if min_p > 0.0:
            body["min_p"] = min_p
        if repetition_penalty != 1.0:
            body["repetition_penalty"] = repetition_penalty
        if seed >= 0:
            body["seed"] = seed
        if enable_thinking:
            body["enable_thinking"] = True
        if extra:
            body.update(extra)
        payload = await self._post_json("/v1/chat/completions", body)
        return _parse_chat_response(payload)

    async def chat_multipart(
        self,
        messages: Iterable[ChatMessage | dict],
        images: list[bytes],
        model: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: float = 1.0,
        extra_fields: dict[str, Any] | None = None,
    ) -> ChatResult:
        """Call `/v1/chat/completions/multipart` — raw image bytes as files."""
        msgs = [m.to_dict() if isinstance(m, ChatMessage) else m for m in messages]
        data = {
            "model": model,
            "messages": orjson.dumps(msgs).decode(),
            "max_tokens": str(max_tokens),
            "temperature": str(temperature),
            "top_p": str(top_p),
            "stream": "false",
        }
        if extra_fields:
            for k, v in extra_fields.items():
                data[k] = str(v)
        files = [("images", (f"img_{i}.jpg", img, "image/jpeg")) for i, img in enumerate(images)]
        headers = self._inference_headers(content_type=None)  # httpx sets multipart boundary
        http = self._client()
        resp = await http.post(
            f"{self.base_url}/v1/chat/completions/multipart",
            data=data,
            files=files,
            headers=headers,
        )
        resp.raise_for_status()
        return _parse_chat_response(orjson.loads(resp.content))

    async def chat_batch(self, requests: list[dict]) -> list[ChatResult]:
        """Call `/v1/batch/chat/completions` with a list of chat-request dicts."""
        payload = await self._post_json("/v1/batch/chat/completions", {"requests": requests})
        return [_parse_chat_response(r) for r in payload.get("responses", [])]

    async def embed(self, texts: list[str] | str, model: str) -> torch.Tensor:
        """Call `/v1/embeddings`. Returns (N, D) float tensor."""
        body = {"model": model, "input": texts}
        payload = await self._post_json("/v1/embeddings", body)
        rows = sorted(payload["data"], key=lambda d: d.get("index", 0))
        return torch.tensor([r["embedding"] for r in rows], dtype=torch.float32)

    async def transcribe(self, audio_bytes: bytes, model: str, filename: str = "audio.wav") -> str:
        """Call `/v1/audio/transcriptions`. Returns the transcript string."""
        files = [("file", (filename, audio_bytes, "audio/wav"))]
        data = {"model": model}
        headers = self._inference_headers(content_type=None)
        http = self._client()
        resp = await http.post(
            f"{self.base_url}/v1/audio/transcriptions",
            data=data,
            files=files,
            headers=headers,
        )
        resp.raise_for_status()
        return orjson.loads(resp.content).get("text", "")

    async def models(self) -> list[ModelInfo]:
        """Call `/v1/models`."""
        payload = await self._get_json("/v1/models")
        return [ModelInfo(id=m["id"], vision=bool(m.get("vision", False))) for m in payload.get("data", [])]

    async def capabilities(self) -> dict:
        """Call `/v1/capabilities`."""
        return await self._get_json("/v1/capabilities")

    async def cache_list(self) -> dict:
        """Call `/v1/cache/list`."""
        return await self._get_json("/v1/cache/list")

    async def cache_clear(self) -> None:
        """Call `/v1/cache/clear` (admin-gated)."""
        http = self._client()
        resp = await http.post(
            f"{self.base_url}/v1/cache/clear",
            headers=self._admin_headers(),
        )
        resp.raise_for_status()

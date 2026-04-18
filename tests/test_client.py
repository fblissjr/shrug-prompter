"""Tests for client.py — httpx-based heylookitsanllm client.

All network IO is mocked with respx. No live server required.
"""

import io

import httpx
import pytest
import respx
import torch
from PIL import Image

from client import (
    ChatMessage,
    ChatResult,
    ShrugClient,
    extract_thinking,
)

BASE_URL = "https://test.invalid"


def _make_jpeg_bytes() -> bytes:
    img = Image.new("RGB", (16, 16), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def client():
    return ShrugClient(base_url=BASE_URL, timeout=5.0)


@pytest.fixture
def client_with_auth():
    return ShrugClient(
        base_url=BASE_URL,
        api_key="sk-test",
        admin_token="admin-xyz",
        timeout=5.0,
    )


class TestBaseUrlHandling:
    def test_strips_trailing_slash(self):
        c = ShrugClient(base_url="https://test.invalid/")
        assert c.base_url == "https://test.invalid"

    def test_preserves_no_slash(self):
        c = ShrugClient(base_url="https://test.invalid")
        assert c.base_url == "https://test.invalid"


class TestChat:
    @respx.mock
    async def test_basic_chat(self, client):
        route = respx.post(f"{BASE_URL}/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "choices": [
                        {"message": {"role": "assistant", "content": "hello!"}}
                    ],
                },
            )
        )
        result = await client.chat(
            messages=[ChatMessage(role="user", content="hi")],
            model="qwen3-vl",
        )
        assert isinstance(result, ChatResult)
        assert result.text == "hello!"
        assert result.thinking == ""
        assert route.called
        request_body = route.calls[0].request.read().decode()
        assert '"model":"qwen3-vl"' in request_body
        assert '"content":"hi"' in request_body

    @respx.mock
    async def test_includes_sampling_params(self, client):
        captured = {}

        def handler(request):
            import orjson
            captured["body"] = orjson.loads(request.read())
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "ok"}}]},
            )

        respx.post(f"{BASE_URL}/v1/chat/completions").mock(side_effect=handler)
        await client.chat(
            messages=[ChatMessage(role="user", content="hi")],
            model="m",
            max_tokens=256,
            temperature=0.5,
            top_p=0.9,
            top_k=40,
            min_p=0.05,
            repetition_penalty=1.1,
            seed=42,
        )
        body = captured["body"]
        assert body["max_tokens"] == 256
        assert body["temperature"] == 0.5
        assert body["top_p"] == 0.9
        assert body["top_k"] == 40
        assert body["min_p"] == 0.05
        assert body["repetition_penalty"] == 1.1
        assert body["seed"] == 42

    @respx.mock
    async def test_omits_default_optional_params(self, client):
        captured = {}

        def handler(request):
            import orjson
            captured["body"] = orjson.loads(request.read())
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "ok"}}]},
            )

        respx.post(f"{BASE_URL}/v1/chat/completions").mock(side_effect=handler)
        await client.chat(
            messages=[ChatMessage(role="user", content="hi")],
            model="m",
        )
        body = captured["body"]
        # Non-essential sampling params not sent when at default
        assert "top_k" not in body
        assert "min_p" not in body
        assert "repetition_penalty" not in body
        assert "seed" not in body

    @respx.mock
    async def test_sends_thinking_flag(self, client):
        captured = {}

        def handler(request):
            import orjson
            captured["body"] = orjson.loads(request.read())
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "done", "thinking": "pondered"}}]},
            )

        respx.post(f"{BASE_URL}/v1/chat/completions").mock(side_effect=handler)
        result = await client.chat(
            messages=[ChatMessage(role="user", content="hi")],
            model="m",
            enable_thinking=True,
        )
        assert captured["body"]["enable_thinking"] is True
        assert result.thinking == "pondered"
        assert result.text == "done"

    @respx.mock
    async def test_error_status_raises(self, client):
        respx.post(f"{BASE_URL}/v1/chat/completions").mock(
            return_value=httpx.Response(500, json={"error": "boom"})
        )
        with pytest.raises(httpx.HTTPStatusError):
            await client.chat(
                messages=[ChatMessage(role="user", content="hi")],
                model="m",
            )


class TestAuth:
    @respx.mock
    async def test_bearer_sent_when_api_key_set(self, client_with_auth):
        captured = {}

        def handler(request):
            captured["headers"] = dict(request.headers)
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "ok"}}]},
            )

        respx.post(f"{BASE_URL}/v1/chat/completions").mock(side_effect=handler)
        await client_with_auth.chat(
            messages=[ChatMessage(role="user", content="hi")],
            model="m",
        )
        assert captured["headers"].get("authorization") == "Bearer sk-test"

    @respx.mock
    async def test_no_auth_header_when_no_key(self, client):
        captured = {}

        def handler(request):
            captured["headers"] = dict(request.headers)
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "ok"}}]},
            )

        respx.post(f"{BASE_URL}/v1/chat/completions").mock(side_effect=handler)
        await client.chat(
            messages=[ChatMessage(role="user", content="hi")],
            model="m",
        )
        assert "authorization" not in captured["headers"]

    @respx.mock
    async def test_admin_token_sent_to_cache_clear(self, client_with_auth):
        captured = {}

        def handler(request):
            captured["headers"] = dict(request.headers)
            return httpx.Response(200, json={"status": "ok"})

        respx.post(f"{BASE_URL}/v1/cache/clear").mock(side_effect=handler)
        await client_with_auth.cache_clear()
        assert captured["headers"].get("x-heylook-admin-token") == "admin-xyz"

    @respx.mock
    async def test_no_admin_token_sent_to_public_endpoints(self, client_with_auth):
        captured = {}

        def handler(request):
            captured["headers"] = dict(request.headers)
            return httpx.Response(200, json={"data": []})

        respx.get(f"{BASE_URL}/v1/models").mock(side_effect=handler)
        await client_with_auth.models()
        assert "x-heylook-admin-token" not in captured["headers"]


class TestChatMultipart:
    @respx.mock
    async def test_multipart_posts_images_as_files(self, client):
        captured = {}

        def handler(request):
            captured["content_type"] = request.headers.get("content-type", "")
            captured["body"] = request.read()
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": "saw it"}}]},
            )

        respx.post(f"{BASE_URL}/v1/chat/completions/multipart").mock(side_effect=handler)
        jpeg = _make_jpeg_bytes()
        result = await client.chat_multipart(
            messages=[ChatMessage(role="user", content="what's here")],
            images=[jpeg],
            model="qwen3-vl",
        )
        assert result.text == "saw it"
        assert "multipart/form-data" in captured["content_type"]
        assert jpeg in captured["body"]


class TestChatBatch:
    @respx.mock
    async def test_batch_returns_list(self, client):
        respx.post(f"{BASE_URL}/v1/batch/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "responses": [
                        {"choices": [{"message": {"content": "a"}}]},
                        {"choices": [{"message": {"content": "b"}}]},
                    ]
                },
            )
        )
        results = await client.chat_batch(
            [
                {"messages": [{"role": "user", "content": "1"}], "model": "m"},
                {"messages": [{"role": "user", "content": "2"}], "model": "m"},
            ]
        )
        assert len(results) == 2
        assert results[0].text == "a"
        assert results[1].text == "b"


class TestEmbeddings:
    @respx.mock
    async def test_embed_returns_tensor(self, client):
        respx.post(f"{BASE_URL}/v1/embeddings").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [
                        {"embedding": [0.1, 0.2, 0.3], "index": 0},
                        {"embedding": [0.4, 0.5, 0.6], "index": 1},
                    ]
                },
            )
        )
        result = await client.embed(["hi", "there"], model="embed-m")
        assert isinstance(result, torch.Tensor)
        assert result.shape == (2, 3)
        assert torch.allclose(result[0], torch.tensor([0.1, 0.2, 0.3]))


class TestTranscribe:
    @respx.mock
    async def test_transcribe_returns_text(self, client):
        captured = {}

        def handler(request):
            captured["content_type"] = request.headers.get("content-type", "")
            return httpx.Response(200, json={"text": "hello world"})

        respx.post(f"{BASE_URL}/v1/audio/transcriptions").mock(side_effect=handler)
        text = await client.transcribe(b"RIFFfake", model="whisper-m")
        assert text == "hello world"
        assert "multipart/form-data" in captured["content_type"]


class TestModels:
    @respx.mock
    async def test_models_returns_list(self, client):
        respx.get(f"{BASE_URL}/v1/models").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [
                        {"id": "qwen3-vl", "vision": True},
                        {"id": "qwen3-text", "vision": False},
                    ]
                },
            )
        )
        models = await client.models()
        assert len(models) == 2
        assert models[0].id == "qwen3-vl"
        assert models[0].vision is True
        assert models[1].vision is False


class TestCapabilities:
    @respx.mock
    async def test_capabilities_returns_dict(self, client):
        respx.get(f"{BASE_URL}/v1/capabilities").mock(
            return_value=httpx.Response(
                200,
                json={"multipart": True, "batch": True, "version": "0.9"},
            )
        )
        caps = await client.capabilities()
        assert caps["multipart"] is True


class TestCacheControl:
    @respx.mock
    async def test_cache_list(self, client):
        respx.get(f"{BASE_URL}/v1/cache/list").mock(
            return_value=httpx.Response(200, json={"entries": ["a", "b"]})
        )
        entries = await client.cache_list()
        assert entries == {"entries": ["a", "b"]}

    @respx.mock
    async def test_cache_clear(self, client):
        route = respx.post(f"{BASE_URL}/v1/cache/clear").mock(
            return_value=httpx.Response(200, json={"status": "cleared"})
        )
        await client.cache_clear()
        assert route.called


class TestExtractThinking:
    def test_plain_response_has_no_thinking(self):
        text, thinking = extract_thinking("just a response")
        assert text == "just a response"
        assert thinking == ""

    def test_think_block_extracted(self):
        text, thinking = extract_thinking("<think>reasoning</think>the answer")
        assert text == "the answer"
        assert thinking == "reasoning"

    def test_multiline_think_block(self):
        raw = "<think>line 1\nline 2</think>final"
        text, thinking = extract_thinking(raw)
        assert thinking == "line 1\nline 2"
        assert text == "final"

    def test_think_block_with_surrounding_whitespace(self):
        text, thinking = extract_thinking("  <think>x</think>\n\nanswer  ")
        assert thinking == "x"
        assert text == "answer"

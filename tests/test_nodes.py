"""Behavioral tests for nodes.py — uses the IO stub fallback so ComfyUI is not required."""

import asyncio
from unittest.mock import AsyncMock

import pytest
import torch

import nodes as N
from client import ChatResult


@pytest.fixture(autouse=True)
def _reset_accumulator():
    N.ShrugAccumulator._state.clear()
    yield
    N.ShrugAccumulator._state.clear()


class TestTextCleanup:
    def test_none_passthrough(self):
        (out,) = N.ShrugTextCleanup.execute(text=" hi\u00a0there ", level="none")
        assert out == " hi\u00a0there "

    def test_basic_strips_edges(self):
        (out,) = N.ShrugTextCleanup.execute(text="  hi  ", level="basic")
        assert out == "hi"

    def test_standard_collapses_blank_lines(self):
        (out,) = N.ShrugTextCleanup.execute(text="a\n\n\n\nb", level="standard")
        assert out == "a\n\nb"

    def test_strict_ascii_only(self):
        # NFC of "café\u00a0x" -> "café\u00a0x"; ASCII-strip drops é and NBSP.
        (out,) = N.ShrugTextCleanup.execute(text="café\u00a0x", level="strict")
        assert out == "cafx"


class TestAccumulator:
    def test_append_and_read(self):
        N.ShrugAccumulator.execute(mode="append", text="a", index=0, delimiter="\n", unique_id="u1")
        N.ShrugAccumulator.execute(mode="append", text="b", index=0, delimiter="\n", unique_id="u1")
        joined, picked, count = N.ShrugAccumulator.execute(
            mode="read", text="", index=0, delimiter=",", unique_id="u1"
        )
        assert joined == "a,b"
        assert count == 2

    def test_reset_clears(self):
        N.ShrugAccumulator.execute(mode="append", text="x", index=0, delimiter="\n", unique_id="u2")
        N.ShrugAccumulator.execute(mode="reset", text="", index=0, delimiter="\n", unique_id="u2")
        joined, picked, count = N.ShrugAccumulator.execute(
            mode="read", text="", index=0, delimiter="\n", unique_id="u2"
        )
        assert joined == ""
        assert count == 0

    def test_state_is_per_unique_id(self):
        N.ShrugAccumulator.execute(mode="append", text="only-in-a", index=0, delimiter="\n", unique_id="a")
        joined, _, count = N.ShrugAccumulator.execute(
            mode="read", text="", index=0, delimiter="\n", unique_id="b"
        )
        assert count == 0
        assert joined == ""

    def test_pick_returns_indexed(self):
        for s in ["zero", "one", "two"]:
            N.ShrugAccumulator.execute(mode="append", text=s, index=0, delimiter="\n", unique_id="p")
        joined, picked, count = N.ShrugAccumulator.execute(
            mode="pick", text="", index=1, delimiter="\n", unique_id="p"
        )
        assert picked == "one"
        assert count == 3


class TestFramePair:
    def _imgs(self, n):
        return torch.arange(n * 4 * 4 * 3, dtype=torch.float32).reshape(n, 4, 4, 3) / (n * 48)

    def test_sequential_pairs_count(self):
        imgs = self._imgs(5)
        start, end, total = N.ShrugFramePair.execute(
            images=imgs, mode="sequential_pairs", pair_index=0, stride=1,
        )
        assert total == 4
        assert start.shape[0] == 1
        assert end.shape[0] == 1
        assert torch.equal(start[0], imgs[0])
        assert torch.equal(end[0], imgs[1])

    def test_first_to_each(self):
        imgs = self._imgs(4)
        start, end, total = N.ShrugFramePair.execute(
            images=imgs, mode="first_to_each", pair_index=2, stride=1,
        )
        assert total == 3
        assert torch.equal(start[0], imgs[0])
        assert torch.equal(end[0], imgs[3])

    def test_rejects_non_bhwc(self):
        with pytest.raises(ValueError):
            N.ShrugFramePair.execute(
                images=torch.zeros(4, 4, 3), mode="sequential_pairs", pair_index=0, stride=1,
            )


class TestShrugVLMHelpers:
    def test_chat_messages_no_images(self):
        messages = N._chat_messages_with_images("sys", "hi", [])
        assert len(messages) == 2
        assert messages[0].role == "system"
        assert messages[1].content == "hi"

    def test_chat_messages_omits_empty_system(self):
        messages = N._chat_messages_with_images("  ", "hi", [])
        assert len(messages) == 1
        assert messages[0].role == "user"

    def test_chat_messages_with_images_uses_content_blocks(self):
        urls = ["data:image/jpeg;base64,abc"]
        messages = N._chat_messages_with_images("", "describe", urls)
        assert isinstance(messages[0].content, list)
        assert messages[0].content[0] == {"type": "text", "text": "describe"}
        assert messages[0].content[1]["type"] == "image_url"


class TestShrugVLMExecute:
    async def test_calls_chat_without_images(self):
        conn = N.ShrugConnection(client=AsyncMock(), model="m")
        conn.client.chat = AsyncMock(return_value=ChatResult(text="hi back", thinking=""))
        out = await N.ShrugVLM.execute(
            connection=conn,
            user_prompt="hi",
            system_prompt="",
            images=None,
            max_tokens=100,
            temperature=0.5,
            top_p=1.0,
            top_k=0,
            min_p=0.0,
            repetition_penalty=1.0,
            seed=-1,
            enable_thinking=False,
            transport="base64",
            image_resize_max=0,
            image_quality=85,
        )
        text, thinking = out
        assert text == "hi back"
        conn.client.chat.assert_called_once()
        kwargs = conn.client.chat.call_args.kwargs
        assert kwargs["model"] == "m"
        assert kwargs["max_tokens"] == 100


class TestShrugVLMBatch:
    async def test_splits_on_newlines(self):
        conn = N.ShrugConnection(client=AsyncMock(), model="m")
        conn.client.chat_batch = AsyncMock(return_value=[
            ChatResult(text="r1"),
            ChatResult(text="r2"),
        ])
        responses, count = await N.ShrugVLMBatch.execute(
            connection=conn,
            user_prompts="prompt one\n\nprompt two",
            system_prompt="",
            images=None,
            max_tokens=100,
            temperature=0.5,
            image_resize_max=0,
            image_quality=85,
        )
        assert count == 2
        assert responses == ["r1", "r2"]
        conn.client.chat_batch.assert_called_once()
        sent = conn.client.chat_batch.call_args.args[0]
        assert len(sent) == 2

    async def test_empty_prompts_short_circuits(self):
        conn = N.ShrugConnection(client=AsyncMock(), model="m")
        conn.client.chat_batch = AsyncMock()
        responses, count = await N.ShrugVLMBatch.execute(
            connection=conn,
            user_prompts="   \n\n  \n",
            system_prompt="",
            images=None,
            max_tokens=100,
            temperature=0.5,
            image_resize_max=0,
            image_quality=85,
        )
        assert count == 0
        assert responses == []
        conn.client.chat_batch.assert_not_called()


class TestExtension:
    def test_comfy_entrypoint_lists_all_ten_nodes(self):
        ext = N.comfy_entrypoint()
        nodes = asyncio.run(ext.get_node_list())
        assert len(nodes) == 10

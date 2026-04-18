# CLAUDE.md — shrug-prompter

## TLDR

ComfyUI custom nodes that talk to [heylookitsanllm](https://github.com/fbjr/heylookitsanllm),
a single-user MLX inference server on macOS, from any ComfyUI client (typically
a CUDA workstation on the same LAN over HTTPS via Caddy).

10 nodes, one file each for client + media codecs + nodes. No multi-provider
layer — tightly coupled to heylookitsanllm's endpoints.

## Architecture

Four Python files, ~1,600 LOC total:

- **`client.py`** — async `ShrugClient` with one method per endpoint:
  `chat`, `chat_multipart`, `chat_batch`, `embed`, `transcribe`, `models`,
  `capabilities`, `cache_list`, `cache_clear`. Owns one persistent
  `httpx.AsyncClient` per instance (TCP/TLS reuse across a workflow run).
  Uses `orjson` (not stdlib json). Handles Qwen3 `<think>` block extraction.
- **`media.py`** — tensor ↔ bytes. `tensor_batch_to_jpeg_bytes`,
  `tensor_to_data_url_list` (OpenAI chat format), `audio_dict_to_wav_bytes`
  (via stdlib `wave` module). ComfyUI image convention: BHWC float32 [0,1].
  ComfyUI audio: `{"waveform": (B,C,T), "sample_rate": int}`.
- **`nodes.py`** — all 10 node classes + `ShrugExtension` + `comfy_entrypoint()`.
  Uses the V3 declarative API (`io.ComfyNode` + `define_schema` + async
  `execute` + `io.NodeOutput`). `_IOStub` fallback so the module imports
  under pytest without ComfyUI (pattern copied from
  `coderef/ComfyUI-AudioLoopHelper/nodes.py:26-44` — keep synced).
- **`__init__.py`** — thin probe for the V3 API; registers
  `/shrug/get_models` aiohttp route that proxies `client.models()` to
  `web/provider.js`.

Runtime dependencies are minimal (`httpx`, `orjson`, `pillow`, `torch`,
`numpy`). `aiohttp` and other ComfyUI runtime deps are deliberately NOT
declared in `pyproject.toml` — declaring them would shadow ComfyUI's
pinned versions at install time.

## Nodes

All in the `shrug` category.

| Node | Endpoint / purpose |
|---|---|
| `ShrugConnection` | Builds a `SHRUG_CONN` object (client + model). `base_url`, `model`, optional `api_key` (→ Bearer), optional `admin_token` (→ `X-Heylook-Admin-Token`, only sent on admin endpoints). |
| `ShrugTemplate` | Loads a `.md` file from `templates/`. Parses YAML-ish frontmatter. Outputs `(system, user, body, description, metadata_json)`. |
| `ShrugTextCleanup` | Single-string normalize: `none` / `basic` (strip) / `standard` (+NFC + collapse blanks) / `strict` (ASCII-only). |
| `ShrugAccumulator` | Graph-scoped string accumulator keyed by `unique_id`. Modes: `append`, `reset`, `read`, `pick`. Class-level state dict — never evicts; rely on mode=reset between runs. |
| `ShrugASR` | `/v1/audio/transcriptions`. Takes ComfyUI `AUDIO`, encodes to WAV, returns text. |
| `ShrugEmbeddings` | `/v1/embeddings`. Returns a `SHRUG_EMBEDDINGS` torch.Tensor. |
| `ShrugVLM` | Main chat/vision node. `/v1/chat/completions` (base64) or `/v1/chat/completions/multipart` via `transport` widget. Returns `(response, thinking)`. |
| `ShrugVLMBatch` | `/v1/batch/chat/completions`. Splits `user_prompts` by newlines; zips with optional image batch. 2-4× throughput for many-image workflows. |
| `ShrugFramePair` | Frame-pair extractor for video interpolation workflows. |
| `ShrugCacheControl` | `/v1/cache/list` (public) or `/v1/cache/clear` (admin; needs admin_token on `ShrugConnection`). |

## Templates library

`templates/` is tracked in git and surfaced via `ShrugTemplate`.

- `templates/vlm/` — structured templates with explicit `system:` / `user:`
  frontmatter keys. Wire directly into `ShrugVLM`.
- `templates/styles/` — 250+ style / system-prompt snippets migrated from
  `coderef/llm-dit-experiments/templates/z_image/`. Z-Image-specific
  frontmatter (`model: z-image`, `add_think_block:`) was stripped on import —
  the bodies are general-purpose system prompts. Wire `body` →
  `ShrugVLM.system_prompt`.
- `templates/styles/rewriter/` — prompt-rewriter system prompts that expand
  short user inputs into full image-gen prompts.

See `templates/README.md` for the frontmatter spec.

## heylookitsanllm features surfaced

- multipart vision upload (~57 ms/image faster than base64) via `transport` widget
- batch endpoint via `ShrugVLMBatch`
- Qwen3 thinking blocks via the second `thinking` output on `ShrugVLM`
- KV-cache management via `ShrugCacheControl`
- server-side image resize (`image_resize_max`, `image_quality` on `ShrugVLM`)

## Server feedback (not yet implemented on the server)

- no lightweight `/v1/health` — clients hit `/v1/models` for reachability
- `/v1/capabilities` response not versioned (`schema_version` would help)
- batch-endpoint partial-failure semantics undocumented
- no request-cancellation endpoint for interrupting a long generate when
  ComfyUI aborts the prompt

## Key patterns

- **Node pattern** mirrors `coderef/ComfyUI-AudioLoopHelper/nodes.py`:
  try/except `comfy_api.latest` import with `_IOStub`/`_Passthrough`
  fallback so the module imports under pytest. `@override
  async def execute(cls, ...)` returns `io.NodeOutput(*values)`.
- **Auth** — inference endpoints never require headers. `api_key` is
  passed as `Authorization: Bearer <key>` if set (future-proofs +
  OpenAI-compat endpoints). `admin_token` only goes on `/v1/cache/clear`.
- **Accumulator state** — class-level `_state: dict[str, list[str]]`
  keyed by the node's `unique_id`. Each graph instance has its own
  list. Not evicted across workflow runs — use mode=reset.
- **Frontmatter** — hand-rolled parser in `nodes.parse_template`
  (no pyyaml dep). Supports `key: value`, `key: [a, b]`, and block
  scalars (`key: |` + indent). Deliberately minimal.
- **Single-user** — no retries, no capability TTL cache. Server is close
  and usually up; fail fast. The one exception: ShrugClient keeps a
  persistent httpx.AsyncClient for TCP/TLS reuse across a workflow.
- **Dual-form sibling imports in `nodes.py`** —
  `try: from .client import …; except ImportError: from client import …`.
  Don't collapse to one form: the try path is what ComfyUI uses (nodes.py
  is a package member); the fallback is what pytest uses
  (`pythonpath = ["."]` loads it as a top-level module). AudioLoopHelper
  avoids this by deferring all sibling imports into methods — we can't
  because our imports are used across many methods.
- **Changing a node's `define_schema`** requires users to delete and
  re-add that node in the ComfyUI UI. Slot indices are baked into saved
  workflows at save time; schema edits desync them.

## Testing

67 tests (client 23, media 16, nodes 18, templates 10). Canonical commands
and the ComfyUI-loader verification step live in
`.claude/skills/shrug-test/SKILL.md` — invoke with `/shrug-test` or follow
the steps manually.

Live smoke against a real server:

```
uv run python scripts/smoke.py --base-url https://your-llm-host --model your-model-id
```

Add `--admin-token TOKEN` to also exercise `/v1/cache/clear`.

## Rollback

`git checkout pre-rewrite-snapshot` restores the pre-rewrite state
(33-node version with multi-provider router).

## Code style

- No emojis anywhere.
- No "Enhanced" / "Advanced" / "Ultimate" prefixes.
- `uv` (never pip). `orjson` (never stdlib json). `httpx` (never requests).
- Default to no comments — only write one when the "why" is non-obvious.

# shrug-prompter

ComfyUI custom nodes for [heylookitsanllm](https://github.com/fbjr/heylookitsanllm) — a single-user MLX inference server on macOS.

Ten nodes, ~1,500 lines of Python. No multi-provider abstraction; this package is specifically tuned for heylookitsanllm's API surface (multipart vision upload, batch endpoint, Qwen3 thinking blocks, KV-cache management).

## Install

Clone into `ComfyUI/custom_nodes/`:

```
cd ComfyUI/custom_nodes
git clone <this repo> shrug-prompter
```

Dependencies are declared in `pyproject.toml` and are normally already present in a ComfyUI environment. If not:

```
cd shrug-prompter
uv sync
```

## Nodes

All nodes live in the `shrug` category.

- **Shrug Connection** — base URL, model, optional auth. Builds a `SHRUG_CONN` object every other node consumes.
- **Shrug VLM** — the main chat/vision node. Optional image batch, all sampling params, Qwen3 thinking output, base64 or multipart transport.
- **Shrug VLM Batch** — N prompts (+ optional N images) in one call via `/v1/batch/chat/completions`. 2-4× faster than N sequential calls.
- **Shrug ASR** — speech-to-text from a ComfyUI `AUDIO` input.
- **Shrug Embeddings** — text → tensor via `/v1/embeddings`.
- **Shrug Template** — loads a `.md` file from `templates/` as a prompt. Ships with 250+ style/system-prompt snippets in `templates/styles/` plus a few VLM templates in `templates/vlm/`. See `templates/README.md` for frontmatter format.
- **Shrug Text Cleanup** — `none` / `basic` / `standard` (NFC + collapse blanks) / `strict` (ASCII-only).
- **Shrug Accumulator** — graph-scoped list state (append/reset/read/pick), for loop workflows.
- **Shrug Frame Pair** — frame-pair extractor for video interpolation.
- **Shrug Cache Control** — list or clear the server's KV cache.

## Configuration

`Shrug Connection`:

- `base_url` — e.g. `http://localhost:8080` (same-host) or `https://your-llm-host` (LAN). Caddy does TLS on the LAN; any reverse proxy will do.
- `model` — the `model` widget is populated by JS fetching `/v1/models` on the server. If the fetch fails, the widget falls back to free text.
- `api_key` (optional) — sent as `Authorization: Bearer <key>`. Ignored by vanilla heylookitsanllm; useful for other OpenAI-compatible targets.
- `admin_token` (optional) — sent as `X-Heylook-Admin-Token` on admin endpoints only (currently just `/v1/cache/clear`). Matches the server's `HEYLOOK_ADMIN_TOKEN` env.

## Testing

```
uv run pytest tests/ -v
```

67 tests covering the client (respx-mocked), media codecs, node behavior, and template parsing.

Live smoke test against a running server:

```
uv run python scripts/smoke.py --base-url https://your-llm-host --model your-model-id
```

## Development

See `CLAUDE.md` for architecture notes and conventions.

Repo layout:

```
shrug-prompter/
├── __init__.py              # V3 API probe + /shrug/get_models route
├── client.py                # async httpx client
├── media.py                 # tensor <-> bytes (image, audio)
├── nodes.py                 # 10 ComfyNode classes + extension
├── pyproject.toml
├── templates/               # .md prompt library
├── web/provider.js          # ShrugConnection's model-dropdown widget
├── scripts/smoke.py         # live LAN smoke test
└── tests/                   # pytest
```

## License

MIT.

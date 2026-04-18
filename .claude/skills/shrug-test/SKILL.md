---
name: shrug-test
description: Run the shrug-prompter test suite and verify the ComfyUI V3 loader can import the package.
---

Run the full test suite plus a ComfyUI loader check. The loader check catches
class of bug that unit tests miss: `__init__.py` or `nodes.py` edits that
break the relative-import chain or the V3 extension registration.

Mirrors `coderef/ComfyUI-AudioLoopHelper/.claude/skills/comfyui-test/SKILL.md`.

## Steps

### 1. Run the test suite (from the repo root)

```bash
uv run pytest tests/ -v
```

Expected: 67+ tests pass. The suite covers:

- **test_client.py** (23): httpx-mocked client for every heylookitsanllm endpoint.
- **test_media.py** (16): tensor ↔ JPEG / PNG / WAV conversions.
- **test_nodes.py** (18): node behavior with the `_IOStub` fallback.
- **test_templates.py** (10): frontmatter parser + `ShrugTemplate` outputs.

### 2. Verify ComfyUI can load the extension (only where ComfyUI is installed)

```bash
cd "${COMFYUI_HOME:-$HOME/ComfyUI}" && python -c "
import asyncio, nodes as n
r = asyncio.run(n.load_custom_node('custom_nodes/shrug-prompter', module_parent='custom_nodes'))
print('ComfyUI loader: OK' if r else 'COMFYUI LOADER FAILED')
exit(0 if r else 1)
"
```

This catches:

- `ModuleNotFoundError: client` / `ModuleNotFoundError: media` — `nodes.py`
  sibling imports broke the relative/absolute dual form.
- `AttributeError: comfy_entrypoint` — `__init__.py` guard swallowed a real
  error (check stderr for the actual exception).
- V3 schema errors that only manifest at ComfyUI load time.

### 3. Live smoke against the server (optional)

```bash
uv run python scripts/smoke.py --base-url https://<your-server>/ --model <vision-model-id>
```

Hits every `ShrugClient` method against a real heylookitsanllm. Prints
per-call latency. Skip `/v1/cache/clear` unless `--admin-token` is passed.

## Common failures

- `ModuleNotFoundError: httpx` or `respx` — forgot `uv sync`.
- `async def functions are not natively supported` — `asyncio_mode = "auto"`
  missing from `[tool.pytest.ini_options]` or `pytest-asyncio` not installed.
- `attempted relative import with no known parent package` — pytest picked
  up `__init__.py`. Root `conftest.py` should have
  `collect_ignore = ["__init__.py"]`.
- `comfy_entrypoint not found` when loading in ComfyUI — the
  `try: from comfy_api.latest import ComfyExtension` probe in `__init__.py`
  caught a real error and fell through. Delete the `except: pass` temporarily
  to see the traceback.

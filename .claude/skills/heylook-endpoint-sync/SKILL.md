---
name: heylook-endpoint-sync
description: Diff ShrugClient methods against heylookitsanllm's current FastAPI routes. Flags endpoints added to the server that shrug-prompter hasn't wired up, endpoints ShrugClient calls that no longer exist, and request/response shape drift. Run before a new shrug-prompter release or after pulling heylookitsanllm upstream.
disable-model-invocation: true
---

This is the one durable coupling risk in the project: heylookitsanllm adds
an endpoint, renames a field, or tightens a request schema, and shrug-prompter
silently drifts until a user hits a 404 / 422 mid-workflow.

## Preconditions

- The `heylookitsanllm` repo is checked out somewhere reachable. Use the
  `HEYLOOK_HOME` env var if the path isn't standard (default:
  `$(dirname "$PWD")/heylookitsanllm` — sibling of the shrug-prompter repo).
- That branch is clean (don't mix in-flight local changes into the diff).

## Steps

### 1. Enumerate server routes

Read the FastAPI app + routers under `$HEYLOOK_HOME/src/heylook_llm/`.
Canonical files as of the last check:

- `api.py` — main app, chat / models / capabilities / cache / embeddings / audio routes.
- `messages_api.py` — Anthropic-style `/v1/messages`.
- `api_multipart.py` — `/v1/chat/completions/multipart`.
- `admin_api.py` — `/v1/admin/*`.
- `rlm.py` — `/v1/rlm`.

Grep for `@app.` and `@router.` decorators, list `(method, path)` tuples.

### 2. Enumerate client methods

Open `client.py` at the shrug-prompter repo root. Each public method
hits exactly one endpoint. Build the same `(method, path)` list.

### 3. Diff

Produce three sections in the report:

**Server-only (not wired in client):** Server has it, we don't call it.
Decide per entry: add a client method + node, or ignore (e.g. `/v1/admin/*`
is intentionally out of scope).

**Client-only (server removed/renamed):** Our method's path no longer exists
on the server. This breaks workflows. Hard-blocker to fix.

**Shape drift:** Same path both sides, but the Pydantic request/response
model on the server has fields we don't send/read, or the server field
types changed. Cross-reference `$HEYLOOK_HOME/src/heylook_llm/schema/`
against `tests/test_client.py` fixtures and `client.py` body builders.

### 4. Prioritize

- **Blocker**: client-only paths (our methods that now 404).
- **High**: shape drift on paths we use (breaks real workflows).
- **Medium**: high-value server additions we should surface as new nodes
  (batch endpoint is already wired; look for new ones — e.g. `/v1/health`,
  structured hidden-states, new sampling params).
- **Low**: intentional omissions (`/v1/admin/*` etc.).

### 5. Output

A report with:

```
## Sync report — <date>

### Blockers (client calls paths that no longer exist)
- <method> <path>: <what changed>

### Shape drift (path matches, payload diverges)
- <method> <path>: server added `field`; our client ignores it. Likely harmless / breaking.

### Server additions worth exposing
- <method> <path>: <one-line description>. Suggest: new ShrugX node, ShrugClient.x() method.

### Intentional omissions (document in CLAUDE.md server-feedback section)
- <method> <path>: not needed by shrug-prompter because <reason>.
```

Also update `CLAUDE.md`'s "Server feedback (not yet implemented on the server)"
section if any of our notes (missing `/v1/health`, unversioned `/v1/capabilities`,
etc.) have been addressed upstream.

## Don't

- Don't auto-add client methods without asking. Every new endpoint deserves
  a conversation about whether it belongs in shrug-prompter or somewhere else.
- Don't touch heylookitsanllm's code from this skill — read-only.

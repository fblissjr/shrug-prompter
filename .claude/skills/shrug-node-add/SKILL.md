---
name: shrug-node-add
description: Scaffold a new shrug-prompter ComfyUI V3 node — generates the class skeleton in nodes.py, registration in ShrugExtension.get_node_list, a test stub in tests/test_nodes.py, and a row in CLAUDE.md's node table.
---

Walk the user through adding one new node. The V3 surface has five coupling
points that all have to move together; this skill enforces the order so none
get missed.

## Invariants

- **V3 only**: `io.ComfyNode` subclass, `@classmethod define_schema`, `@classmethod async def execute`, returns `io.NodeOutput(*values)`.
- **No `INPUT_TYPES` / `NODE_CLASS_MAPPINGS`**: we rely on the extension's `get_node_list`.
- **Sibling imports**: if the node needs `ShrugClient` / `ChatMessage` / `media.*`, use the existing imports at the top of `nodes.py` (the `try: from .client ... except: from client ...` dual form). Don't add new module-level sibling imports with a different pattern.
- **Category**: `CATEGORY` constant — always `"shrug"`.
- **Hidden UI slot**: use `hidden=[io.Hidden.unique_id]` only when the node needs graph-scoped state (like `ShrugAccumulator`).

## Steps

### 1. Gather requirements

Ask the user:

1. Node id + display name (e.g. `ShrugThing` / `"Shrug Thing"`).
2. Does it call the server? If yes, which endpoint? (API nodes get `is_api_node=True` on the schema.)
3. Inputs: types, defaults, advanced-vs-basic. Does it take `SHRUG_CONN`?
4. Outputs: types, output-is-list?
5. Is it stateful? (Graph-scoped state = `hidden=[io.Hidden.unique_id]` + class-level dict.)

### 2. Add the class to `nodes.py`

Insert BEFORE `class ShrugExtension(ComfyExtension):` at the bottom. Template:

```python
class ShrugThing(io.ComfyNode):
    """One-line docstring."""

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="ShrugThing",
            display_name="Shrug Thing",
            category=CATEGORY,
            is_api_node=True,  # drop if the node doesn't hit the server
            description="What this does.",
            inputs=[
                io.Custom("SHRUG_CONN").Input("connection"),
                # ... typed inputs
            ],
            outputs=[
                io.String.Output("result"),
            ],
            # hidden=[io.Hidden.unique_id],  # uncomment for graph-scoped state
        )

    @classmethod
    async def execute(cls, connection: ShrugConnection, ...) -> io.NodeOutput:
        # If calling the server, use connection.client.<method>.
        result = ...
        return io.NodeOutput(result)
```

Sync-only node? Drop `async` from `execute`. Mixing is fine — the
runtime `await`s both.

### 3. Register in `ShrugExtension.get_node_list`

Append the class name to the list. Keep alphabetical if easy, otherwise group
by purpose matching the CLAUDE.md table.

### 4. Add a test in `tests/test_nodes.py`

Follow the `TestShrugVLMExecute` pattern for async nodes (uses `AsyncMock`) or
`TestFramePair` for sync tensor nodes. For API-calling nodes:

```python
class TestShrugThing:
    async def test_basic_call(self):
        conn = N.ShrugConnection(client=AsyncMock(), model="m")
        conn.client.some_method = AsyncMock(return_value=...)
        out = await N.ShrugThing.execute(connection=conn, ...)
        assert out[0] == ...
        conn.client.some_method.assert_called_once()
```

Also bump the hardcoded count in `TestExtension.test_comfy_entrypoint_lists_all_ten_nodes`
(rename the test method too — `ten` → `eleven` etc.).

### 5. Document in `CLAUDE.md`

Append a row to the `## Nodes` table:

```markdown
| `ShrugThing` | One-sentence description including endpoint. |
```

### 6. Run the verification (from the repo root)

```bash
uv run pytest tests/ -v
```

All tests green. Then on the 4090 box: run `/shrug-test` to verify ComfyUI
loader still imports everything.

## Schema-change warning — always surface this to the user

When a node's `define_schema` changes (any input/output added, removed, or
reordered), **existing saved workflows that use that node will desync** —
ComfyUI bakes slot indices into the workflow JSON at save time. Users must
delete and re-add the node in the UI. Surface this whenever a schema edit
touches an existing node, not just new ones.

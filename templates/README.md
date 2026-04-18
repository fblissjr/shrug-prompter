# Templates

Markdown files in this directory are surfaced by the `ShrugTemplate` node as a
dropdown. Nested subdirectories are fine — the path (relative to `templates/`)
is the dropdown value.

## Format

Templates may start with a small YAML-ish frontmatter block and end with a body.

```markdown
---
name: short_id
description: one-line human description
category: vlm
system: |
  You are a helpful assistant.
  Be concise.
user: |
  Describe the attached image.
---

Optional notes. Ignored by shrug-prompter, intended for human readers.
```

`ShrugTemplate` emits five outputs:

| output | source |
| --- | --- |
| `system` | frontmatter `system:` block scalar (empty if absent) |
| `user` | frontmatter `user:` block scalar (empty if absent) |
| `body` | everything after the closing `---` (empty if no frontmatter → body is the full file) |
| `description` | frontmatter `description:` (empty if absent) |
| `metadata` | all other frontmatter fields as a JSON string |

## Two conventions

1. **Structured templates** (`vlm/caption.md`): declare `system:` and `user:`
   in frontmatter. Wire the respective outputs to `ShrugVLM`'s inputs. `body`
   is human-readable notes.

2. **Body-as-prompt** (`styles/*.md`): frontmatter has metadata only; the body
   is the system prompt text. Wire `body` → `ShrugVLM.system_prompt`.

## Directories

- `vlm/` — structured VLM templates with explicit system/user prompts.
- `styles/` — 250+ single-purpose style / system-prompt snippets. Each file's
  body is a ready-to-use system prompt. Originally authored for Z-Image but
  useful for any text→image / VLM task.
- `styles/rewriter/` — prompt-rewriter system prompts (expand short user
  prompts into full diffusion-model prompts).

Unsupported frontmatter features: multi-line flow maps, anchors, tags. Inline
lists (`tags: [a, b, c]`) and block scalars (`key: |`) work. That covers every
template in this repo.

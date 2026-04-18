"""Tests for template frontmatter parsing and ShrugTemplate outputs."""

import textwrap
from pathlib import Path

import pytest

from nodes import ShrugTemplate, parse_template


@pytest.fixture
def template_dir(tmp_path, monkeypatch):
    import nodes

    monkeypatch.setattr(nodes, "TEMPLATES_DIR", tmp_path)
    return tmp_path


class TestParseTemplate:
    def test_body_only_no_frontmatter(self):
        raw = "just a plain prompt"
        meta, system, user, body = parse_template(raw)
        assert meta == {}
        assert system == ""
        assert user == ""
        assert body == "just a plain prompt"

    def test_scalar_frontmatter(self):
        raw = textwrap.dedent(
            """\
            ---
            name: caption
            description: Basic image caption
            ---

            Body of the template.
            """
        )
        meta, system, user, body = parse_template(raw)
        assert meta["name"] == "caption"
        assert meta["description"] == "Basic image caption"
        assert body.strip() == "Body of the template."

    def test_block_scalar_system_and_user(self):
        raw = textwrap.dedent(
            """\
            ---
            name: describe
            system: |
              You are a helpful assistant.
              Be concise.
            user: |
              Describe the image in one sentence.
            ---

            Notes here.
            """
        )
        meta, system, user, body = parse_template(raw)
        assert system == "You are a helpful assistant.\nBe concise."
        assert user == "Describe the image in one sentence."
        assert body.strip() == "Notes here."

    def test_missing_closing_delimiter_falls_back_to_body_only(self):
        raw = "---\nname: bad\n\nbody without close"
        meta, system, user, body = parse_template(raw)
        assert meta == {}
        assert body == raw

    def test_preserves_colons_in_values(self):
        raw = "---\ndescription: a: b: c\n---\nbody"
        meta, system, user, body = parse_template(raw)
        assert meta["description"] == "a: b: c"

    def test_list_of_tags(self):
        raw = "---\ntags: [foo, bar, baz]\n---\nbody"
        meta, _, _, _ = parse_template(raw)
        assert meta["tags"] == ["foo", "bar", "baz"]


class TestShrugTemplateNode:
    def test_loads_file_and_returns_all_outputs(self, template_dir):
        path = template_dir / "caption.md"
        path.write_text(textwrap.dedent(
            """\
            ---
            name: caption
            description: A test
            system: |
              You caption.
            user: |
              Describe it.
            ---
            body
            """
        ))
        out = ShrugTemplate.execute(template="caption.md")
        system, user, body, description, metadata = out
        assert system == "You caption."
        assert user == "Describe it."
        assert body.strip() == "body"
        assert description == "A test"

    def test_plain_template_returns_body_as_body(self, template_dir):
        (template_dir / "plain.md").write_text("just text")
        out = ShrugTemplate.execute(template="plain.md")
        system, user, body, description, metadata = out
        assert system == ""
        assert user == ""
        assert body == "just text"
        assert description == ""
        assert metadata == "{}"

    def test_missing_file_returns_empty_strings(self, template_dir):
        out = ShrugTemplate.execute(template="doesnotexist.md")
        assert out == ("", "", "", "", "{}")

    def test_exposes_arbitrary_frontmatter_as_metadata_json(self, template_dir):
        import orjson

        (template_dir / "preset.md").write_text(textwrap.dedent(
            """\
            ---
            name: portrait
            description: Portrait preset
            guidance_scale: 4.0
            steps: 40
            tags: [portrait, photo]
            negative_prompt: |
              plastic skin, doll
            ---

            notes
            """
        ))
        out = ShrugTemplate.execute(template="preset.md")
        _, _, _, _, metadata_json = out
        meta = orjson.loads(metadata_json)
        assert meta["name"] == "portrait"
        assert meta["guidance_scale"] == "4.0"
        assert meta["steps"] == "40"
        assert meta["tags"] == ["portrait", "photo"]
        assert "plastic skin" in meta["negative_prompt"]

from pathlib import Path

import pytest

from visual_underwriting.prompts import load_prompt_template, render_prompt_template


def test_load_prompt_template_reads_markdown(tmp_path: Path) -> None:
    prompt_path = tmp_path / "prompt.md"
    prompt_path.write_text("Assess {{asset_type}}.", encoding="utf-8")

    assert load_prompt_template(prompt_path) == "Assess {{asset_type}}."


def test_load_prompt_template_rejects_empty_markdown(tmp_path: Path) -> None:
    prompt_path = tmp_path / "prompt.md"
    prompt_path.write_text("   ", encoding="utf-8")

    with pytest.raises(ValueError):
        load_prompt_template(prompt_path)


def test_render_prompt_template_substitutes_placeholders() -> None:
    rendered = render_prompt_template(
        "Assess {{asset_type}} with {{metadata_json}} and {{schema_json}}.",
        {
            "asset_type": "shop",
            "metadata_json": "{}",
            "schema_json": '{"type":"object"}',
        },
    )

    assert rendered == 'Assess shop with {} and {"type":"object"}.'

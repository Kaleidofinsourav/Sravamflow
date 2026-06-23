from pathlib import Path

import pytest

from collection_agent.config import CollectionAgentSettings
from collection_agent.prompts import load_prompt


def test_load_prompt_reads_editable_markdown(tmp_path: Path) -> None:
    prompt_path = tmp_path / "prompt.md"
    prompt_path.write_text("Be polite and concise.", encoding="utf-8")

    assert load_prompt(prompt_path) == "Be polite and concise."


def test_load_prompt_rejects_empty_file(tmp_path: Path) -> None:
    prompt_path = tmp_path / "prompt.md"
    prompt_path.write_text("   ", encoding="utf-8")

    with pytest.raises(ValueError):
        load_prompt(prompt_path)


def test_collection_agent_settings_reports_missing_runtime_keys() -> None:
    settings = CollectionAgentSettings(
        livekit_url="",
        livekit_api_key="",
        livekit_api_secret="",
        sarvam_api_key="",
    )

    assert settings.missing_runtime_keys() == [
        "LIVEKIT_URL",
        "LIVEKIT_API_KEY",
        "LIVEKIT_API_SECRET",
        "SARVAM_API_KEY",
    ]

from pathlib import Path


def load_prompt(prompt_path: Path) -> str:
    path = prompt_path
    if not path.is_absolute():
        path = Path.cwd() / path

    if not path.exists():
        raise FileNotFoundError(f"Collection agent prompt file not found: {path}")

    prompt = path.read_text(encoding="utf-8").strip()
    if not prompt:
        raise ValueError(f"Collection agent prompt file is empty: {path}")

    return prompt

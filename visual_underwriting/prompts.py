from pathlib import Path


def load_prompt_template(prompt_path: Path) -> str:
    path = prompt_path
    if not path.is_absolute():
        path = Path.cwd() / path

    if not path.exists():
        raise FileNotFoundError(f"Visual underwriting prompt file not found: {path}")

    prompt = path.read_text(encoding="utf-8").strip()
    if not prompt:
        raise ValueError(f"Visual underwriting prompt file is empty: {path}")

    return prompt


def render_prompt_template(template: str, values: dict[str, str]) -> str:
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    return rendered

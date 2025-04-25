from pathlib import Path

def load_prompts() -> dict[str, str]:
    """Load all .txt prompts from the default prompts directory into a dictionary."""
    prompts_dir = Path(__file__).resolve().parent.parent / 'prompts'
    return {
        file.stem: file.read_text(encoding="utf-8")
        for file in prompts_dir.glob("*.txt")
    }
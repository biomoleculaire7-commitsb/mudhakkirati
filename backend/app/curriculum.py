import json
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).parent / "data" / "curriculum.json"


@lru_cache
def load() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


def get_subject(subject_id: str) -> dict | None:
    return next((s for s in load()["subjects"] if s["id"] == subject_id), None)


def get_level(level_id: int) -> dict | None:
    return next((l for l in load()["levels"] if l["id"] == level_id), None)


def summary() -> dict:
    """Curriculum sent to the frontend (full tree; it is small)."""
    return load()

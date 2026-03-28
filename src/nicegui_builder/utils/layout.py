from __future__ import annotations

from inspect import currentframe
from pathlib import Path

import yaml


def _caller_file() -> Path:
    frame = currentframe()
    for _ in range(3):
        if frame is None or frame.f_back is None:
            return Path.cwd()
        frame = frame.f_back
    return Path(frame.f_code.co_filename).resolve()


def _resolve_base_dir(caller_file: str | Path | None) -> Path:
    if caller_file is None:
        caller_path = _caller_file()
    else:
        caller_path = Path(caller_file).resolve()
    return caller_path if caller_path.is_dir() else caller_path.parent


def _adjacent_candidates(base_dir: Path, requested: Path) -> list[Path]:
    if requested.is_absolute() or requested.parent != Path("."):
        return []
    if requested.suffix:
        return [base_dir / requested.name]
    return [base_dir / f"{requested.name}.yml", base_dir / f"{requested.name}.yaml"]


def load_layout(layout: str | Path, *, caller_file: str | Path | None = None):
    requested = Path(layout)
    base_dir = _resolve_base_dir(caller_file)

    for candidate in _adjacent_candidates(base_dir, requested):
        if candidate.exists():
            with candidate.open(encoding="utf-8") as file:
                return yaml.safe_load(file)

    with requested.open(encoding="utf-8") as file:
        return yaml.safe_load(file)

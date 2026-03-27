from __future__ import annotations

import inspect
from pathlib import Path

import nicegui.ui as nicegui_ui


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "typings" / "nicegui" / "ui.pyi"

ADDED_NAMES = [
    "builder",
    "datetime_input",
    "form_builder",
    "table_builder",
]

ADDED_IMPORTS = [
    "from nicegui_builder import builder as builder",
    "from nicegui_builder import form as form_builder",
    "from nicegui_builder import table as table_builder",
    "from nicegui_builder.core.datetime_inputs import DateTimeInput as datetime_input",
]


def inject_names(source_text: str) -> str:
    marker = "__all__ = ["
    start = source_text.index(marker)
    end = source_text.index("]\n\n", start) + 2
    block = source_text[start:end]
    for name in ADDED_NAMES:
        needle = f"    '{name}',\n"
        if needle not in block:
            block = block[:-2] + needle + "]\n"
    return source_text[:start] + block + source_text[end:]


def inject_imports(source_text: str) -> str:
    marker = "from .context import context\n"
    imports = "\n".join(ADDED_IMPORTS) + "\n\n"
    if imports in source_text:
        return source_text
    position = source_text.index(marker)
    return source_text[:position] + imports + source_text[position:]


def absolutize_relative_imports(source_text: str) -> str:
    lines = []
    for line in source_text.splitlines():
        if line.startswith("from ."):
            lines.append(f"from nicegui{line[5:]}")
            continue
        lines.append(line)
    return "\n".join(lines) + "\n"


def main() -> int:
    source_text = inspect.getsource(nicegui_ui)
    target_text = inject_imports(inject_names(source_text))
    target_text = absolutize_relative_imports(target_text)
    TARGET.write_text(target_text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from nicegui_builder.utils import load_layout


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_load_layout_uses_explicit_path():
    layout_path = FIXTURES_DIR / "festival.yml"
    layout = load_layout(layout_path)

    assert layout[0]["label"]["params"]["text"] == "Hello"


def test_load_layout_prefers_adjacent_yml_of_calling_module():
    module_path = FIXTURES_DIR / "sample_module.py"
    spec = spec_from_file_location("sample_module", module_path)
    module = module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)

    layout = module.build_layout()

    assert layout[0]["label"]["params"]["text"] == "Adjacent"

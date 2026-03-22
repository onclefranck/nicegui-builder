import importlib

import pytest


pandas = pytest.importorskip("pandas")
table_module = importlib.import_module("nicegui_builder.table")

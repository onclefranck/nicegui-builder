from importlib import import_module

import pytest
from fastapi.testclient import TestClient
from nicegui import app
from nicegui import ui

from nicegui_builder.cli import list_examples


def _configure_test_app() -> None:
    app.reset()
    app.config.add_run_config(
        reload=False,
        title="NiceGUI",
        viewport="width=device-width, initial-scale=1",
        favicon=None,
        dark=False,
        language="en-US",
        binding_refresh_interval=0.1,
        reconnect_timeout=3.0,
        message_history_length=1000,
        tailwind=True,
        unocss=None,
        prod_js=True,
        show_welcome_message=False,
    )


@pytest.mark.parametrize("example_name", list_examples())
def test_example_build_ui_returns_http_200(example_name: str) -> None:
    _configure_test_app()

    module = import_module(f"nicegui_builder.examples.{example_name}")
    build_ui = getattr(module, "build_ui", None)

    assert build_ui is not None, f"{example_name} must expose build_ui()"

    ui.page("/")(build_ui)

    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200, example_name

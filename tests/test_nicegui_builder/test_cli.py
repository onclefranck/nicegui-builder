import types
import builtins
from pathlib import Path
import threading

import nicegui_builder.cli as cli


def test_list_examples_includes_known_examples():
    examples = cli.list_examples()

    assert "demo_basic_builder" in examples
    assert "demo_pydantic_builder" in examples
    assert "04_pandas_table_basic" in examples


def test_list_example_specs_include_plugin_groups():
    specs = cli.list_example_specs()
    grouped = {spec.name: spec.group for spec in specs}

    assert grouped["01_basic_builder"] == "core"
    assert grouped["03_pydantic_form_basic"] == "pydantic"
    assert grouped["04_pandas_table_basic"] == "pandas"


def test_load_object_resolves_module_paths():
    target = cli.load_object("nicegui_builder.plugins.pydantic.examples.demo_pydantic_builder:DemoPydanticBuilder")

    assert target.__name__ == "DemoPydanticBuilder"


def test_load_object_rejects_invalid_path():
    try:
        cli.load_object("nicegui_builder.plugins.pydantic.examples.demo_pydantic_builder")
    except ValueError as exc:
        assert "module:object" in str(exc)
    else:
        raise AssertionError("load_object should reject paths without ':'")


def test_resolve_example_name_accepts_full_name(monkeypatch):
    monkeypatch.setattr(
        cli,
        "list_example_specs",
        lambda: [
            cli.ExampleSpec("01_basic_builder", "pkg.core.01_basic_builder", "core"),
            cli.ExampleSpec("03_pydantic_form_basic", "pkg.pydantic.03_pydantic_form_basic", "pydantic"),
        ],
    )

    assert cli.resolve_example_name("01_basic_builder") == "01_basic_builder"


def test_resolve_example_name_accepts_numeric_shortcut(monkeypatch):
    monkeypatch.setattr(
        cli,
        "list_example_specs",
        lambda: [
            cli.ExampleSpec("01_basic_builder", "pkg.core.01_basic_builder", "core"),
            cli.ExampleSpec("03_pydantic_form_basic", "pkg.pydantic.03_pydantic_form_basic", "pydantic"),
        ],
    )

    assert cli.resolve_example_name("01") == "01_basic_builder"


def test_resolve_example_name_accepts_partial_prefix(monkeypatch):
    monkeypatch.setattr(
        cli,
        "list_example_specs",
        lambda: [
            cli.ExampleSpec("01_basic_builder", "pkg.core.01_basic_builder", "core"),
            cli.ExampleSpec("03_pydantic_form_basic", "pkg.pydantic.03_pydantic_form_basic", "pydantic"),
        ],
    )

    assert cli.resolve_example_name("01_") == "01_basic_builder"
    assert cli.resolve_example_name("01_basic") == "01_basic_builder"


def test_resolve_example_name_returns_first_match_for_ambiguous_shortcut(monkeypatch):
    monkeypatch.setattr(
        cli,
        "list_example_specs",
        lambda: [
            cli.ExampleSpec("01_alpha", "pkg.core.01_alpha", "core"),
            cli.ExampleSpec("01_beta", "pkg.pydantic.01_beta", "pydantic"),
        ],
    )

    assert cli.resolve_example_name("01") == "01_alpha"


def test_resolve_example_name_raises_for_unknown_example(monkeypatch):
    monkeypatch.setattr(
        cli,
        "list_example_specs",
        lambda: [cli.ExampleSpec("01_basic_builder", "pkg.core.01_basic_builder", "core")],
    )

    try:
        cli.resolve_example_name("99")
    except LookupError as exc:
        assert "unknown example" in str(exc)
    else:
        raise AssertionError("resolve_example_name should raise for an unknown example")


def test_run_layout_loads_yaml_and_starts_ui(monkeypatch):
    layout_path = Path("tests") / "_cli_layout.yml"
    layout_path.write_text("- label:\n    params:\n      text: Hello\n", encoding="utf-8")

    calls = {}

    class DummyEvent:
        def set(self):
            calls["stopped"] = True

    monkeypatch.setattr(cli, "enable_any_key_shutdown", lambda *args, **kwargs: DummyEvent())
    monkeypatch.setattr(cli, "builder", lambda layout: calls.setdefault("layout", layout))
    def fake_run(**kwargs):
        calls["run_kwargs"] = kwargs
        kwargs["root"]()

    monkeypatch.setattr(cli.ui, "run", fake_run)

    try:
        result = cli.run_layout(str(layout_path), port=9000, host="127.0.0.1", reload=True)

        assert result == 0
        assert calls["layout"][0]["label"]["params"]["text"] == "Hello"
        assert calls["stopped"] is True
        assert calls["run_kwargs"] == {
            "root": calls["run_kwargs"]["root"],
            "port": 9000,
            "host": "127.0.0.1",
            "reload": True,
        }
    finally:
        if layout_path.exists():
            layout_path.unlink()


def test_run_form_loads_source_and_starts_ui(monkeypatch):
    calls = {}

    class DummyEvent:
        def set(self):
            calls["stopped"] = True

    monkeypatch.setattr(cli, "enable_any_key_shutdown", lambda *args, **kwargs: DummyEvent())
    monkeypatch.setattr(cli, "form", lambda source, flavor="": calls.setdefault("form", (source, flavor)))
    def fake_run(**kwargs):
        calls["run_kwargs"] = kwargs
        kwargs["root"]()

    monkeypatch.setattr(cli.ui, "run", fake_run)

    result = cli.run_form(
        "nicegui_builder.plugins.pydantic.examples.demo_pydantic_builder:DemoPydanticBuilder",
        flavor="compact",
        port=8081,
    )

    assert result == 0
    source, flavor = calls["form"]
    assert source.__name__ == "DemoPydanticBuilder"
    assert flavor == "compact"
    assert calls["stopped"] is True
    assert calls["run_kwargs"] == {
        "root": calls["run_kwargs"]["root"],
        "port": 8081,
        "host": None,
        "reload": False,
    }


def test_run_form_actionable_builds_default_action_bar(monkeypatch):
    calls = {}

    class DummyEvent:
        def set(self):
            calls["stopped"] = True

    class FakeHandle:
        def action_bar(self, *args, **kwargs):
            calls["action_bar"] = {"args": args, "kwargs": kwargs}

    monkeypatch.setattr(cli, "enable_any_key_shutdown", lambda *args, **kwargs: DummyEvent())
    monkeypatch.setattr(cli, "form", lambda source, flavor="": FakeHandle())

    def fake_run(**kwargs):
        calls["run_kwargs"] = kwargs
        kwargs["root"]()

    monkeypatch.setattr(cli.ui, "run", fake_run)

    result = cli.run_form(
        "nicegui_builder.examples.models:Contest",
        flavor="actionable",
        port=8082,
    )

    assert result == 0
    assert calls["action_bar"]["args"][0] == "Preview values"
    assert calls["action_bar"]["kwargs"]["live_changed_badge"] is True
    assert calls["action_bar"]["kwargs"]["live_submit_button"] is True
    assert calls["action_bar"]["kwargs"]["live_reset_button"] is True


def test_run_form_actionable_skips_action_bar_when_handle_does_not_support_it(monkeypatch):
    calls = {}

    class DummyEvent:
        def set(self):
            calls["stopped"] = True

    class FakeHandle:
        pass

    monkeypatch.setattr(cli, "enable_any_key_shutdown", lambda *args, **kwargs: DummyEvent())
    monkeypatch.setattr(cli, "form", lambda source, flavor="": FakeHandle())

    def fake_run(**kwargs):
        calls["run_kwargs"] = kwargs
        kwargs["root"]()

    monkeypatch.setattr(cli.ui, "run", fake_run)

    result = cli.run_form(
        "nicegui_builder.examples.models:Contest",
        flavor="actionable",
        port=8083,
    )

    assert result == 0
    assert "stopped" in calls


def test_run_example_invokes_example_main(monkeypatch):
    module = types.SimpleNamespace()
    calls = {}

    def fake_build_ui():
        calls["built"] = True

    module.build_ui = fake_build_ui

    class DummyEvent:
        def set(self):
            calls["stopped"] = True

    monkeypatch.setattr(cli, "enable_any_key_shutdown", lambda *args, **kwargs: DummyEvent())
    monkeypatch.setattr(cli, "resolve_example_spec", lambda name: cli.ExampleSpec("demo", "pkg.demo", "core"))
    monkeypatch.setattr(cli, "import_module", lambda name: module)
    def fake_run(**kwargs):
        calls["run_kwargs"] = kwargs
        kwargs["root"]()

    monkeypatch.setattr(cli.ui, "run", fake_run)

    result = cli.run_example("demo", port=9001, host="0.0.0.0", reload=True)

    assert result == 0
    assert calls["built"] is True
    assert calls["stopped"] is True
    assert calls["run_kwargs"] == {
        "root": fake_build_ui,
        "port": 9001,
        "host": "0.0.0.0",
        "reload": True,
    }


def test_run_example_falls_back_to_main_when_build_ui_is_missing(monkeypatch):
    calls = {}

    def fake_main(**kwargs):
        calls["main_kwargs"] = kwargs
        return 42

    module = types.SimpleNamespace(main=fake_main)

    monkeypatch.setattr(cli, "resolve_example_spec", lambda name: cli.ExampleSpec("demo", "pkg.demo", "core"))
    monkeypatch.setattr(cli, "import_module", lambda name: module)

    result = cli.run_example("demo", port=9002, host="127.0.0.1", reload=True)

    assert result == 42
    assert calls["main_kwargs"] == {
        "port": 9002,
        "host": "127.0.0.1",
        "reload": True,
    }


def test_run_example_raises_when_example_exposes_no_entrypoint(monkeypatch):
    module = types.SimpleNamespace()

    monkeypatch.setattr(cli, "resolve_example_spec", lambda name: cli.ExampleSpec("demo", "pkg.demo", "core"))
    monkeypatch.setattr(cli, "import_module", lambda name: module)

    try:
        cli.run_example("demo")
    except AttributeError as exc:
        assert "does not expose build_ui" in str(exc)
    else:
        raise AssertionError("run_example should require build_ui(...) or main(...)")


def test_run_ui_app_handles_keyboard_interrupt(monkeypatch, capsys):
    calls = {}

    class DummyEvent:
        def set(self):
            calls["stopped"] = True

    monkeypatch.setattr(cli, "enable_any_key_shutdown", lambda *args, **kwargs: DummyEvent())

    def fake_run(**kwargs):
        raise KeyboardInterrupt()

    monkeypatch.setattr(cli.ui, "run", fake_run)

    result = cli.run_ui_app(lambda: None, port=9999)

    assert result == 130
    assert calls["stopped"] is True
    assert "Shutting down..." in capsys.readouterr().out


def test_run_ui_app_returns_zero_on_clean_exit(monkeypatch):
    calls = {}

    class DummyEvent:
        def set(self):
            calls["stopped"] = True

    monkeypatch.setattr(cli, "enable_any_key_shutdown", lambda *args, **kwargs: DummyEvent())
    monkeypatch.setattr(cli.ui, "run", lambda **kwargs: calls.setdefault("run_kwargs", kwargs))

    result = cli.run_ui_app(lambda: None, port=9998, host="127.0.0.1", reload=True)

    assert result == 0
    assert calls["stopped"] is True
    assert calls["run_kwargs"]["port"] == 9998


def test_enable_any_key_shutdown_returns_none_when_not_interactive(monkeypatch):
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr(cli.sys.stdout, "isatty", lambda: False)

    assert cli.enable_any_key_shutdown() is None


def test_enable_any_key_shutdown_returns_none_when_no_watcher_is_available(monkeypatch):
    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(cli.sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr(cli, "_build_keypress_watcher", lambda stop_event, message: None)

    assert cli.enable_any_key_shutdown() is None


def test_enable_any_key_shutdown_starts_background_watcher(monkeypatch):
    calls = {}

    monkeypatch.setattr(cli.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(cli.sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr(cli, "_build_keypress_watcher", lambda stop_event, message: lambda: calls.setdefault("watched", message))

    class DummyThread:
        def __init__(self, *, target, daemon):
            calls["target"] = target
            calls["daemon"] = daemon

        def start(self):
            calls["started"] = True

    monkeypatch.setattr(cli.threading, "Thread", DummyThread)

    stop_event = cli.enable_any_key_shutdown("Press any key...")

    assert stop_event is not None
    assert calls["daemon"] is True
    assert calls["started"] is True


def test_build_keypress_watcher_prefers_windows_watcher(monkeypatch):
    stop_event = threading.Event()
    windows = object()
    posix = object()

    monkeypatch.setattr(cli, "_build_windows_keypress_watcher", lambda event, message: windows)
    monkeypatch.setattr(cli, "_build_posix_keypress_watcher", lambda event, message: posix)

    assert cli._build_keypress_watcher(stop_event, "msg") is windows


def test_build_keypress_watcher_falls_back_to_posix(monkeypatch):
    stop_event = threading.Event()
    posix = object()

    monkeypatch.setattr(cli, "_build_windows_keypress_watcher", lambda event, message: None)
    monkeypatch.setattr(cli, "_build_posix_keypress_watcher", lambda event, message: posix)

    assert cli._build_keypress_watcher(stop_event, "msg") is posix


def test_build_windows_keypress_watcher_handles_import_error(monkeypatch):
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "msvcrt":
            raise ImportError()
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    assert cli._build_windows_keypress_watcher(threading.Event(), "msg") is None


def test_build_windows_keypress_watcher_stops_server_on_keypress(monkeypatch, capsys):
    calls = {}
    stop_event = threading.Event()

    class FakeMsvcrt:
        @staticmethod
        def kbhit():
            return True

        @staticmethod
        def getwch():
            return "x"

    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "msvcrt":
            return FakeMsvcrt
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.setattr(cli.app, "shutdown", lambda: calls.setdefault("shutdown", True))
    monkeypatch.setattr(cli.time, "sleep", lambda _: None)

    watcher = cli._build_windows_keypress_watcher(stop_event, "Press any key")

    assert watcher is not None
    watcher()

    assert stop_event.is_set() is True
    assert calls["shutdown"] is True
    output = capsys.readouterr().out
    assert "Press any key" in output
    assert "Stopping server..." in output


def test_build_windows_keypress_watcher_handles_getwch_error(monkeypatch, capsys):
    stop_event = threading.Event()

    class FakeMsvcrt:
        @staticmethod
        def kbhit():
            return True

        @staticmethod
        def getwch():
            raise OSError()

    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "msvcrt":
            return FakeMsvcrt
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    watcher = cli._build_windows_keypress_watcher(stop_event, "Press any key")

    assert watcher is not None
    watcher()

    assert stop_event.is_set() is False
    assert "Press any key" in capsys.readouterr().out


def test_build_posix_keypress_watcher_returns_none_when_fileno_is_unavailable(monkeypatch):
    class BrokenStdin:
        def fileno(self):
            raise ValueError()

    monkeypatch.setattr(cli.sys, "stdin", BrokenStdin())

    assert cli._build_posix_keypress_watcher(threading.Event(), "msg") is None


def test_build_posix_keypress_watcher_stops_server_on_keypress(monkeypatch, capsys):
    calls = {}
    stop_event = threading.Event()

    class FakeStdin:
        def fileno(self):
            return 7

        def read(self, count):
            calls["read"] = count
            return "x"

    class FakeSelect:
        @staticmethod
        def select(readers, writers, errors, timeout):
            calls["select_timeout"] = timeout
            return ([readers[0]], [], [])

    class FakeTermios:
        TCSADRAIN = 1
        error = OSError

        @staticmethod
        def tcgetattr(fd):
            calls["tcgetattr_fd"] = fd
            return ["attrs"]

        @staticmethod
        def tcsetattr(fd, when, attrs):
            calls["tcsetattr"] = (fd, when, attrs)

    class FakeTty:
        @staticmethod
        def setcbreak(fd):
            calls["setcbreak_fd"] = fd

    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "select":
            return FakeSelect
        if name == "termios":
            return FakeTermios
        if name == "tty":
            return FakeTty
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.setattr(cli.sys, "stdin", FakeStdin())
    monkeypatch.setattr(cli.app, "shutdown", lambda: calls.setdefault("shutdown", True))

    watcher = cli._build_posix_keypress_watcher(stop_event, "Press any key")

    assert watcher is not None
    watcher()

    assert stop_event.is_set() is True
    assert calls["shutdown"] is True
    assert calls["setcbreak_fd"] == 7
    assert calls["tcsetattr"] == (7, 1, ["attrs"])
    output = capsys.readouterr().out
    assert "Press any key" in output
    assert "Stopping server..." in output


def test_build_posix_keypress_watcher_handles_read_error(monkeypatch, capsys):
    calls = {}
    stop_event = threading.Event()

    class FakeStdin:
        def fileno(self):
            return 8

        def read(self, count):
            raise OSError()

    class FakeSelect:
        @staticmethod
        def select(readers, writers, errors, timeout):
            return ([readers[0]], [], [])

    class FakeTermios:
        TCSADRAIN = 1
        error = OSError

        @staticmethod
        def tcgetattr(fd):
            return ["attrs"]

        @staticmethod
        def tcsetattr(fd, when, attrs):
            calls["tcsetattr"] = (fd, when, attrs)

    class FakeTty:
        @staticmethod
        def setcbreak(fd):
            calls["setcbreak_fd"] = fd

    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "select":
            return FakeSelect
        if name == "termios":
            return FakeTermios
        if name == "tty":
            return FakeTty
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.setattr(cli.sys, "stdin", FakeStdin())

    watcher = cli._build_posix_keypress_watcher(stop_event, "Press any key")

    assert watcher is not None
    watcher()

    assert stop_event.is_set() is False
    assert calls["tcsetattr"] == (8, 1, ["attrs"])
    assert "Press any key" in capsys.readouterr().out


def test_cli_main_lists_examples(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "list_examples_grouped",
        lambda: [
            ("core", [cli.ExampleSpec("alpha", "pkg.alpha", "core")]),
            ("pydantic", [cli.ExampleSpec("beta", "pkg.beta", "pydantic")]),
        ],
    )

    result = cli.main(["examples", "list"])

    assert result == 0
    assert capsys.readouterr().out.splitlines() == ["[core]", "alpha", "[pydantic]", "beta"]


def test_cli_main_runs_example(monkeypatch):
    monkeypatch.setattr(cli, "run_example", lambda name, **kwargs: ("example", name, kwargs))

    result = cli.main(["examples", "run", "01", "--port", "9003", "--host", "0.0.0.0", "--reload"])

    assert result == (
        "example",
        "01",
        {"port": 9003, "host": "0.0.0.0", "reload": True},
    )


def test_cli_main_runs_layout(monkeypatch):
    monkeypatch.setattr(cli, "run_layout", lambda path, **kwargs: ("layout", path, kwargs))

    result = cli.main(["layout", "run", "festival.yml", "--port", "9004"])

    assert result == (
        "layout",
        "festival.yml",
        {"port": 9004, "host": None, "reload": False},
    )


def test_cli_main_runs_form(monkeypatch):
    monkeypatch.setattr(cli, "run_form", lambda source, **kwargs: ("form", source, kwargs))

    result = cli.main(["form", "run", "pkg:Contest", "--flavor", "actionable", "--host", "127.0.0.1"])

    assert result == (
        "form",
        "pkg:Contest",
        {"flavor": "actionable", "port": 8080, "host": "127.0.0.1", "reload": False},
    )


def test_cli_main_unknown_command_path(monkeypatch):
    class FakeParser:
        def parse_args(self, argv):
            return types.SimpleNamespace(command="mystery")

        def error(self, message):
            self.message = message

    parser = FakeParser()
    monkeypatch.setattr(cli, "build_parser", lambda: parser)

    result = cli.main([])

    assert parser.message == "unknown command"
    assert result == 2

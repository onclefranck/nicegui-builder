import argparse
from importlib import import_module
from pathlib import Path
import sys
import threading
import time

import yaml
from nicegui import app
from nicegui import ui

from .builder import builder
from .form import form


def _build_windows_keypress_watcher(stop_event: threading.Event, message: str):
    try:
        import msvcrt
    except ImportError:
        return None

    def watch_keyboard() -> None:
        print(message, flush=True)
        while not stop_event.is_set():
            if msvcrt.kbhit():
                try:
                    msvcrt.getwch()
                except OSError:
                    break
                print("\nStopping server...", flush=True)
                app.shutdown()
                stop_event.set()
                break
            time.sleep(0.1)

    return watch_keyboard


def _build_posix_keypress_watcher(stop_event: threading.Event, message: str):
    try:
        import select
        import termios
        import tty
    except ImportError:
        return None

    try:
        fd = sys.stdin.fileno()
        original_attrs = termios.tcgetattr(fd)
    except (AttributeError, OSError, ValueError, termios.error):
        return None

    def watch_keyboard() -> None:
        print(message, flush=True)
        try:
            tty.setcbreak(fd)
            while not stop_event.is_set():
                ready, _, _ = select.select([sys.stdin], [], [], 0.1)
                if not ready:
                    continue
                try:
                    sys.stdin.read(1)
                except OSError:
                    break
                print("\nStopping server...", flush=True)
                app.shutdown()
                stop_event.set()
                break
        finally:
            try:
                termios.tcsetattr(fd, termios.TCSADRAIN, original_attrs)
            except (OSError, termios.error):
                pass

    return watch_keyboard


def _build_keypress_watcher(stop_event: threading.Event, message: str):
    return _build_windows_keypress_watcher(stop_event, message) or _build_posix_keypress_watcher(stop_event, message)


def enable_any_key_shutdown(message: str = "Press any key to stop the server...") -> threading.Event | None:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return None

    stop_event = threading.Event()
    watcher = _build_keypress_watcher(stop_event, message)
    if watcher is None:
        return None

    threading.Thread(target=watcher, daemon=True).start()
    return stop_event


def run_ui_app(root, *, port: int = 8080, host: str | None = None, reload: bool = False) -> int:
    keyboard_shutdown = enable_any_key_shutdown()
    try:
        ui.run(root=root, port=port, host=host, reload=reload)
        return 0
    except KeyboardInterrupt:
        print("\nShutting down...")
        return 130
    finally:
        if keyboard_shutdown is not None:
            keyboard_shutdown.set()


def list_examples() -> list[str]:
    examples_dir = Path(__file__).parent / "examples"
    return sorted(
        path.stem
        for path in examples_dir.glob("*.py")
        if path.name != "__init__.py" and not path.name.startswith("_")
    )


def resolve_example_name(name: str) -> str:
    examples = list_examples()
    if name in examples:
        return name

    for example in examples:
        if example.startswith(name):
            return example

    raise LookupError(f"unknown example: {name}")


def load_object(dotted_path: str):
    if ":" not in dotted_path:
        raise ValueError("source must use the format 'module:object'")

    module_name, object_name = dotted_path.split(":", 1)
    module = import_module(module_name)
    target = module
    for part in object_name.split("."):
        target = getattr(target, part)
    return target


def run_example(name: str, *, port: int = 8080, host: str | None = None, reload: bool = False):
    resolved_name = resolve_example_name(name)

    module = import_module(f"nicegui_builder.examples.{resolved_name}")
    build_ui = getattr(module, "build_ui", None)
    if build_ui is not None:
        return run_ui_app(build_ui, port=port, host=host, reload=reload)

    main = getattr(module, "main", None)
    if main is None:
        raise AttributeError(f"example '{name}' does not expose build_ui(...) or main(...)")

    return main(port=port, host=host, reload=reload)


def run_layout(path: str, *, port: int = 8080, host: str | None = None, reload: bool = False):
    layout_path = Path(path)
    with layout_path.open(encoding="utf-8") as file:
        layout = yaml.safe_load(file)

    def build_ui():
        builder(layout)

    return run_ui_app(build_ui, port=port, host=host, reload=reload)


def run_form(source: str, *, flavor: str = "", port: int = 8080, host: str | None = None, reload: bool = False):
    resolved_source = load_object(source)

    def build_ui():
        handle = form(resolved_source, flavor=flavor)

        if flavor == "actionable" and hasattr(handle, "action_bar"):
            handle.action_bar(
                "Preview values",
                lambda payload: ui.notify(str(payload)),
                show_changed_badge=True,
                live_changed_badge=True,
                live_submit_button=True,
                live_reset_button=True,
                show_when_clean=True,
            )

    return run_ui_app(build_ui, port=port, host=host, reload=reload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nicegui-builder")
    subparsers = parser.add_subparsers(dest="command", required=True)

    examples_parser = subparsers.add_parser("examples", help="list and run bundled examples")
    examples_subparsers = examples_parser.add_subparsers(dest="examples_command", required=True)

    examples_subparsers.add_parser("list", help="list available examples")

    examples_run_parser = examples_subparsers.add_parser("run", help="run a bundled example")
    examples_run_parser.add_argument("name")
    examples_run_parser.add_argument("--port", type=int, default=8080)
    examples_run_parser.add_argument("--host", default=None)
    examples_run_parser.add_argument("--reload", action="store_true")

    layout_parser = subparsers.add_parser("layout", help="render a YAML layout file")
    layout_subparsers = layout_parser.add_subparsers(dest="layout_command", required=True)

    layout_run_parser = layout_subparsers.add_parser("run", help="run a layout file")
    layout_run_parser.add_argument("path")
    layout_run_parser.add_argument("--port", type=int, default=8080)
    layout_run_parser.add_argument("--host", default=None)
    layout_run_parser.add_argument("--reload", action="store_true")

    form_parser = subparsers.add_parser("form", help="render a form from a plugin-supported source")
    form_subparsers = form_parser.add_subparsers(dest="form_command", required=True)

    form_run_parser = form_subparsers.add_parser("run", help="run a form source")
    form_run_parser.add_argument("source", help="Python path in the form module:object")
    form_run_parser.add_argument("--flavor", default="")
    form_run_parser.add_argument("--port", type=int, default=8080)
    form_run_parser.add_argument("--host", default=None)
    form_run_parser.add_argument("--reload", action="store_true")

    return parser


def main(argv: list[str] | None = None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "examples":
        if args.examples_command == "list":
            for example in list_examples():
                print(example)
            return 0

        if args.examples_command == "run":
            return run_example(args.name, port=args.port, host=args.host, reload=args.reload)

    if args.command == "layout" and args.layout_command == "run":
        return run_layout(args.path, port=args.port, host=args.host, reload=args.reload)

    if args.command == "form" and args.form_command == "run":
        return run_form(
            args.source,
            flavor=args.flavor,
            port=args.port,
            host=args.host,
            reload=args.reload,
        )

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

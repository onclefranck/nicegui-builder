"""A very small custom plugin.

Not every source deserves a grand framework.
Sometimes the festival simply needs a special pass for lost socks and visiting confusion.
"""

from dataclasses import dataclass

from nicegui import ui

import nicegui_builder
from nicegui_builder.core.models import FieldSpec, LayoutNode, ResolvedFieldNode, WidgetSpec
from nicegui_builder.plugins import plugin_registry
from nicegui_builder.utils import load_layout


@dataclass
class LostSockPass:
    owner_name: str = "Lucy Lobbyworth"
    sock_description: str = "One striped sock with unreasonable confidence"
    urgent: bool = False


class LostSockPlugin:
    name = "lost_sock"

    def supports(self, source) -> bool:
        if isinstance(source, type):
            return source is LostSockPass
        return isinstance(source, LostSockPass)

    def inspect_fields(self, source) -> list[FieldSpec]:
        instance = source if isinstance(source, LostSockPass) else None
        return [
            FieldSpec(name="owner_name", python_type=str, title="Owner name", default=getattr(instance, "owner_name", "")),
            FieldSpec(
                name="sock_description",
                python_type=str,
                title="Sock description",
                default=getattr(instance, "sock_description", ""),
            ),
            FieldSpec(name="urgent", python_type=bool, title="Urgent", default=getattr(instance, "urgent", False)),
        ]

    def build_layout(self, source, flavor: str = ""):
        del flavor
        return load_layout("26_custom_plugin_minimal")

    def build_field_context(self, model_class, model_instance, fieldname: str) -> dict:
        del model_class
        return {
            "fieldname": fieldname,
            "fieldvalue": getattr(model_instance, fieldname, None) if model_instance is not None else None,
        }

    def resolve_field_node(self, model_class, model_instance, fieldname: str, value: dict | None):
        value = value or {}
        field_ctx = self.build_field_context(model_class, model_instance, fieldname)
        widget = self.resolve_widget(
            next(spec for spec in self.inspect_fields(model_instance or LostSockPass) if spec.name == fieldname),
            variant=value.get("methods", "std"),
        )
        params = {"value": field_ctx["fieldvalue"]}
        if widget.component == "switch":
            params["text"] = fieldname.replace("_", " ").title()
        else:
            params["label"] = fieldname.replace("_", " ").title()
        node = LayoutNode(
            methods=widget.component,
            params=params,
            props=widget.props,
            classes=value.get("classes", widget.classes),
        )
        return ResolvedFieldNode(
            field_ctx=field_ctx,
            default_info={"methods": widget.component},
            node=node,
        )

    def resolve_widget(self, spec: FieldSpec, variant: str = "std") -> WidgetSpec:
        if spec.name == "urgent" or variant == "switch":
            return WidgetSpec(component="switch")
        if spec.name == "sock_description" or variant == "textarea":
            return WidgetSpec(component="textarea")
        return WidgetSpec(component="input")

    def render_form(self, source, flavor: str = ""):
        del source, flavor
        return None


def build_ui():
    plugin_registry.register(LostSockPlugin())

    ui.label("Minimal custom plugin").classes("text-h5")
    ui.label(
        "This tiny plugin handles one whimsical source type and proves the extension point can stay approachable."
    ).classes("text-body2 text-grey-7")

    handle = ui.form_builder(LostSockPass())

    with ui.row().classes("gap-2"):
        ui.button(
            "Show values",
            on_click=lambda: ui.notify(str(handle.get_values())),
        )
        ui.button(
            "Show spec",
            on_click=lambda: ui.notify(f"{handle.spec.plugin_name}: {len(handle.spec.field_specs)} fields"),
        )


def main(*, port: int = 8080, host: str | None = None, reload: bool = False):
    ui.run(root=build_ui, port=port, host=host, reload=reload)


if __name__ in {"__main__", "__mp_main__"}:
    main()

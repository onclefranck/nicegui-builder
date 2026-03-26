from dataclasses import dataclass


@dataclass(slots=True, kw_only=True)
class ViewHandle:
    root_component: object | None = None
    plugin: object | None = None

    @property
    def spec(self):
        raise NotImplementedError("ViewHandle subclasses must expose a spec property")

    @property
    def plugin_name(self) -> str:
        if self.plugin is not None and hasattr(self.plugin, "name"):
            return str(self.plugin.name)

        spec = self.spec
        if hasattr(spec, "plugin_name"):
            return str(spec.plugin_name)

        return ""

    @property
    def spec_type(self) -> str:
        return type(self.spec).__name__

    def describe(self) -> dict[str, object]:
        return {
            "handle_type": type(self).__name__,
            "plugin_name": self.plugin_name,
            "spec_type": self.spec_type,
            "root_component_type": (
                type(self.root_component).__name__ if self.root_component is not None else None
            ),
        }

    def get_component(self, ref: str):
        refs = getattr(self, "component_refs", None)
        if isinstance(refs, dict):
            return refs.get(ref)
        refs = getattr(self.root_component, "component_refs", None)
        if isinstance(refs, dict):
            return refs.get(ref)
        raise AttributeError("component refs are not available on this handle")

    def refresh(self):
        if self.root_component is not None and hasattr(self.root_component, "update"):
            self.root_component.update()
        return self

    def show(self):
        if self.root_component is not None and hasattr(self.root_component, "set_visibility"):
            self.root_component.set_visibility(True)
        elif self.root_component is not None and hasattr(self.root_component, "visible"):
            self.root_component.visible = True
        return self

    def hide(self):
        if self.root_component is not None and hasattr(self.root_component, "set_visibility"):
            self.root_component.set_visibility(False)
        elif self.root_component is not None and hasattr(self.root_component, "visible"):
            self.root_component.visible = False
        return self

    def __getattr__(self, name: str):
        if self.root_component is None:
            raise AttributeError(name)
        return getattr(self.root_component, name)

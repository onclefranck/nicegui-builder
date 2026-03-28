from dataclasses import dataclass, field
import typing as t


JsonDict = dict[str, t.Any]


@dataclass(slots=True)
class FieldSpec:
    name: str
    python_type: t.Any
    required: bool = False
    nullable: bool = False
    default: t.Any = None
    title: str = ""
    description: str = ""
    examples: list[t.Any] = field(default_factory=list)
    choices: list[t.Any] = field(default_factory=list)
    constraints: JsonDict = field(default_factory=dict)
    source_meta: JsonDict = field(default_factory=dict)


@dataclass(slots=True)
class CollectionSpec:
    name: str
    item_type: t.Any = None
    columns: list[FieldSpec] = field(default_factory=list)
    filters: list[FieldSpec] = field(default_factory=list)
    source_meta: JsonDict = field(default_factory=dict)


@dataclass(slots=True)
class WidgetSpec:
    component: str
    variant: str = "std"
    params: JsonDict = field(default_factory=dict)
    props: str = ""
    classes: str = ""
    slots: JsonDict = field(default_factory=dict)


@dataclass(slots=True)
class LayoutNode:
    methods: str
    params: JsonDict = field(default_factory=dict)
    props: str = ""
    classes: str = ""
    ref: str | None = None
    children: list[t.Any] = field(default_factory=list)
    context: JsonDict = field(default_factory=dict)

    @classmethod
    def from_layout_entry(cls, component: JsonDict) -> "LayoutNode":
        key, value = next(iter(component.items()))
        if value is None:
            value = {}

        return cls(
            methods=key,
            params=dict(value.get("params") or {}),
            props=value.get("props", ""),
            classes=value.get("classes", ""),
            ref=value.get("ref"),
            children=[
                cls.from_layout_entry(child)
                if isinstance(child, dict) and "__" not in next(iter(child.keys()))
                else child
                for child in (value.get("children") or [])
            ],
        )

    def to_layout_entry(self) -> JsonDict:
        return {
            self.methods: {
                "params": dict(self.params),
                "props": self.props,
                "classes": self.classes,
                "ref": self.ref,
                "children": [
                    child.to_layout_entry() if isinstance(child, LayoutNode) else child
                    for child in self.children
                ],
            }
        }


@dataclass(slots=True)
class ResolvedFieldNode:
    node: LayoutNode
    field_ctx: JsonDict = field(default_factory=dict)


@dataclass(slots=True)
class FormSpec:
    source_class: type
    field_specs: list[FieldSpec] = field(default_factory=list)
    source_instance: t.Any = None
    layout: t.Any = None
    flavor: str = ""
    plugin_name: str = ""


@dataclass(slots=True)
class TableSpec:
    source_class: type
    collection_spec: CollectionSpec
    source: t.Any = None
    widget_spec: WidgetSpec | None = None
    layout: t.Any = None
    flavor: str = "std"
    plugin_name: str = ""


@dataclass(slots=True)
class ActionSpec:
    name: str
    label: str
    intent: str = "secondary"
    strategy: str = "always"
    confirm_message: str = ""

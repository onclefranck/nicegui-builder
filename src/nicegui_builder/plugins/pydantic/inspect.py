import json
import enum

from flatten_dict import flatten
from pydantic import BaseModel
from pydantic_core import PydanticUndefined

from .mapping import extract_options


def _serialize_field_value(fieldvalue):
    if fieldvalue in (PydanticUndefined, None):
        return fieldvalue

    if isinstance(fieldvalue, enum.Enum):
        return fieldvalue.value

    if isinstance(fieldvalue, BaseModel):
        return json.dumps(fieldvalue.model_dump(), indent=2, ensure_ascii=True)

    if isinstance(fieldvalue, (list, tuple, set, dict)):
        return json.dumps(fieldvalue, indent=2, ensure_ascii=True, default=str)

    return fieldvalue


def build_field_context(model_class, model_instance, fieldname: str) -> dict:
    field_info = model_class.model_fields[fieldname]
    ctx = {
        "fieldname": fieldname,
        "field_info": field_info,
    }
    ctx.update(flatten(field_info.asdict(), "underscore"))

    fieldvalue = getattr(model_instance, fieldname) if model_instance else PydanticUndefined
    if fieldvalue is PydanticUndefined:
        fieldvalue = field_info.default
    if fieldvalue is PydanticUndefined:
        fieldvalue = ""

    ctx["fieldvalue"] = _serialize_field_value(fieldvalue)
    ctx["choices"] = extract_options(field_info)
    return ctx

# -*- coding: utf-8 -*-
"""Default settings specifically for the Google APIs."""

from dataclasses import dataclass, fields
from functools import partial
from importlib import import_module
from types import ModuleType

from marshmallow import EXCLUDE
from marshmallow.fields import (
    Str,
    Int,
    Bool,
    Float,
    DateTime as DateTimeF,
    Dict as DictF,
    List as ListF,
    Raw,
)
from marshmallow_enum import EnumField

from flask_dialogflow.json import (
    ModuleLocalNested, JSONType, JSONTypeSchema
)

_DEFAULT_FIELD_KWARGS = {
    'allow_none': True,
    'required': False
}

Str = partial(Str, **_DEFAULT_FIELD_KWARGS)
Int = partial(Int, **_DEFAULT_FIELD_KWARGS)
Bool = partial(Bool, **_DEFAULT_FIELD_KWARGS, truthy={True}, falsy={False})
Float = partial(Float, **_DEFAULT_FIELD_KWARGS)
DateTimeF = partial(DateTimeF, **_DEFAULT_FIELD_KWARGS)
DictF = partial(DictF, **_DEFAULT_FIELD_KWARGS)
ListF = partial(ListF, **_DEFAULT_FIELD_KWARGS)
ModuleLocalNested = partial(ModuleLocalNested, **_DEFAULT_FIELD_KWARGS)
Raw = partial(Raw, **_DEFAULT_FIELD_KWARGS)
EnumField = partial(EnumField, **_DEFAULT_FIELD_KWARGS)


class GoogleTypeSchema(JSONTypeSchema):

    class Meta:
        unknown = EXCLUDE


@dataclass
class GoogleType(JSONType, schema=GoogleTypeSchema):

    def __post_init__(self):
        for f in fields(self):
            if self.__dict__[f.name] is None and callable(f.default_factory):
                self.__dict__[f.name] = f.default_factory()


def import_dialogflow_api(version: str) -> ModuleType:
    import_path = f'flask_dialogflow.google_apis.dialogflow_{version}'
    return import_module(import_path)

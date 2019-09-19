# -*- coding: utf-8 -*-
"""
    test_google_apis
    ~~~~~~~

    :copyright: (c) 2018 ONSEI GmbH
    :license: Proprietary
"""
import inspect
from dataclasses import is_dataclass, fields
from enum import Enum
from types import ModuleType
from typing import Iterable, Type

import pytest

from flask_dialogflow.agent import DIALOGFLOW_VERSIONS
from flask_dialogflow.google_apis import (
    JSONType,
    JSONTypeSchema,
    actions_on_google_v2,
    dialogflow_v2,
    dialogflow_v2beta1,
    import_dialogflow_api
)
from flask_dialogflow.utils import fqn


def generate_module_classes(module: ModuleType) -> Iterable[Type]:
    for _, cls in inspect.getmembers(module, inspect.isclass):
        if cls.__module__ == module.__name__:
            yield cls


GOOGLE_API_MODULES = (actions_on_google_v2, dialogflow_v2, dialogflow_v2beta1)
GOOGLE_API_MODULE_CLASS = (
    cls for mod in GOOGLE_API_MODULES for cls in generate_module_classes(mod)
)
GOOGLE_API_TYPES = (
    cls for mod in GOOGLE_API_MODULES for cls in generate_module_classes(mod)
    if issubclass(cls, JSONType)
)
GOOGLE_API_TYPE_SCHEMAS = (
    cls for mod in GOOGLE_API_MODULES for cls in generate_module_classes(mod)
    if issubclass(cls, JSONTypeSchema)
)


@pytest.fixture(scope='module', params=GOOGLE_API_MODULE_CLASS, ids=fqn)
def google_api_module_class(request):
    return request.param


def test_class_is_either_type_or_schema_or_enum(google_api_module_class):
    assert issubclass(
        google_api_module_class, (JSONType, JSONTypeSchema, Enum)
    ), (
        'Google API modules should have no classes other than JSONType,'
        'JSONTypeSchema and Enum subclasses.'
    )


@pytest.fixture(scope='module', params=GOOGLE_API_TYPES, ids=fqn)
def google_api_type(request):
    return request.param


def test_type_is_dataclass(google_api_type):
    assert is_dataclass(google_api_type)


@pytest.fixture(scope='module', params=GOOGLE_API_TYPE_SCHEMAS, ids=fqn)
def google_api_type_schema(request):
    return request.param


def test_each_type_field_maps_to_a_schema_field(google_api_type):
    schema = google_api_type.__marshmallow_schema__
    for field in fields(google_api_type):
        assert field.name in _schema_field_names(schema)


def test_each_schema_field_maps_to_a_type_field(google_api_type_schema):
    api_type = google_api_type_schema.__marshmallow_object_class__
    schema = google_api_type_schema
    for field_name, field_obj in schema._declared_fields.items():
        name = field_obj.attribute or field_name
        assert name in _type_field_names(api_type)


def _schema_field_names(schema: JSONTypeSchema) -> Iterable[str]:
    """Return the field names of a Schema.

    If the schema field has an attribute declared use this, otherwise the
    default name (i.e. the variable the field was assigned to).
    """
    return tuple(
        (field_obj.attribute or field_name)
        for field_name, field_obj in schema._declared_fields.items()
    )


def _type_field_names(api_type: JSONType) -> Iterable[str]:
    return tuple(field.name for field in fields(api_type))


@pytest.mark.parametrize('version', DIALOGFLOW_VERSIONS)
def test_import_dialogflow_api(version):
    mod_name = f'flask_dialogflow.google_apis.dialogflow_{version}'
    mod = import_dialogflow_api(version)
    assert isinstance(mod, ModuleType)
    assert mod.__name__ == mod_name

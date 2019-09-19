# -*- coding: utf-8 -*-
"""
    test_json
    ~~~~~~~

    :copyright: (c) 2018 ONSEI GmbH
    :license: Proprietary
"""
from dataclasses import dataclass
from typing import Optional

import pytest
from marshmallow import Schema, fields

from flask_dialogflow.json import JSONType, JSONTypeSchema, ModuleLocalNested


@pytest.fixture
def schema():

    class FooSchema(JSONTypeSchema):
        bar = fields.Str()

    return FooSchema


@pytest.fixture
def cls(schema):

    @dataclass
    class Foo(JSONType, schema=schema):
        bar: Optional[str] = None

    return Foo


class TestJSONTypeSchema:

    def test_schema_subclass(self, schema):
        assert issubclass(schema, Schema)

    def test_has_object_class_attr(self, schema):
        assert hasattr(schema, '__marshmallow_object_class__')

    def test_has_post_load_hook(self, schema):
        """Marshmallows implementation as of v3.0.0rc5, not part of the
        public API.
        """
        assert 'make_obj' in schema._hooks[('post_load', False)]

    def test_make_obj_is_post_load_hook(self, schema, cls):
        """Also as of v3.0.0rc5, not public."""
        assert hasattr(schema.make_obj, '__marshmallow_hook__')
        expected_hook = {('post_load', False): {'pass_original': False}}
        assert schema.make_obj.__marshmallow_hook__ == expected_hook


class TestJSONType:

    def test_immediate_subclasses_must_declare_schema(self):
        with pytest.raises(AttributeError):
            class Foo(JSONType): pass

    def test_indirect_subclasses_can_inherit_schema_from_direct_subclass(
        self, cls
    ):
        class Bar(cls): pass
        assert hasattr(Bar, '__marshmallow_schema__')
        assert Bar.__marshmallow_schema__ == cls.__marshmallow_schema__

    def test_error_when_schema_not_JSONTypeSchema(self):
        with pytest.raises(TypeError):
            class Foo(JSONType, schema=Schema): pass

    def test_has_schema_attr(self, cls):
        assert hasattr(cls, '__marshmallow_schema__')
        assert issubclass(cls.__marshmallow_schema__, JSONTypeSchema)

    def test_from_json(self, schema, cls):
        assert hasattr(cls, 'from_json')
        assert callable(cls.from_json)
        assert cls.from_json({'bar': 'baz'}) == cls('baz')

    def test_from_json_without_object_cls(self, schema, cls):
        schema.__marshmallow_object_class__ = None
        assert cls.from_json({'bar': 'baz'}) == {'bar': 'baz'}

    def test_to_json(self, schema, cls):
        assert hasattr(cls, 'to_json')
        assert callable(cls.to_json)
        assert cls('baz').to_json() == {'bar': 'baz'}


class TestModuleLocalNested:

    def test_with_schema_instance(self):
        res = ModuleLocalNested(Schema())
        assert isinstance(res, fields.Nested)

    def test_with_module_name(mself):
        res = ModuleLocalNested('nested', module_name='foo.bar')
        assert isinstance(res, fields.Nested)
        assert res.nested == 'foo.bar.nested'

    def test_still_works_without_module_name(self):
        res = ModuleLocalNested('nested')
        assert isinstance(res, fields.Nested)
        assert res.nested == 'nested'

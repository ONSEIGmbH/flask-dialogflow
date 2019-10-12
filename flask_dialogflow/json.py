# -*- coding: utf-8 -*-
"""
    json
    ~~~~~~~

    :copyright: (c) 2018 ONSEI GmbH
    :license: Proprietary
"""
from dataclasses import dataclass
from typing import Type, Optional, MutableMapping, Any, Union

from marshmallow import post_load, Schema, EXCLUDE, post_dump
from marshmallow.fields import Nested


# Type alias for all JSONs. Mypy unfortunately doesn't allow recursive types,
# so we can't be any more specific here, but it's at least something. See here
# for details: https://github.com/python/typing/issues/182
JSON = MutableMapping[str, Any]


@dataclass
class JSONType:
    """Mixin class that provides to_json and from_json methods.

    Custom classes can inherit from this class and specify their marshmallow
    schema in the class definition. The schema must be a subclass of
    :class:`.JSONTypeSchema`. This class will then make sure that class
    and schema are linked and add to_json and from_json methods to the class.
    These methods completely abstract the schema and the marshmallow processing
    and allow it convert instances of this class to and from JSON in the
    simplest possible way.

    Classes are defined as normal classes (optionally dataclasses), schemas as
    normal marshmallow schemas.

    Example: ::

        from marshmallow import fields

        class _CustomClassSchema(JSONTypeSchema):
            foo = fields.Str()
            bar = fields.Int()

        @dataclass
        class CustomClass(JSONType, schema=_CustomClassSchema):
            foo: str
            bar: int

    ``CustomClass`` is now linked with its schema and has :meth:`.to_json`
    and :meth:`.from_json` methods. They abstract the de-/serialization,
    the user does not have to care about marshmallow or the schema anymore:

        >>> CustomClass.from_json({'foo': 'baz', 'bar': 42})
        CustomClass(foo='baz', bar=42)
        >>> CustomClass(foo='baz', bar=42).to_json()
        {'foo': 'baz', 'bar': 42}

    This works with all marshmallow features and can thus be used to quickly
    de-/serialize complex class hierarchies (such as
    :class:`.WebhookRequests`). The only caveat is that the result of
    :meth:`.Schema.load` will be spread into the classes init method, i.e. the
    params must map to each other. It is therefore recommend to use plain
    dataclasses as JSONTypes. However, both the to_json and from_json accept
    schema and dump/load kwargs, should further customization be desired.

    Raises:
        AttributeError: When this class was subclassed without specifying a
            schema and a schema could also not be found in a super class.
        TypeError: When the specified schema is not a JSONTypeSchema subclass.
    """

    def __init_subclass__(cls, *args, **kwargs):
        """See if we can find a schema and link it with this subclass."""
        super().__init_subclass__()
        schema = kwargs.pop('schema', None)
        if not schema:  # Try the super classes
            try:
                schema = getattr(cls, '__marshmallow_schema__')
            except AttributeError:
                raise AttributeError(
                    'JSONType declared without a schema and schema also not '
                    'available from superclass.'
                )
        if not issubclass(schema, JSONTypeSchema):
            raise TypeError(
                f'Schema must be a {JSONTypeSchema.__name__} subclass.'
            )
        cls.__marshmallow_schema__ = schema
        schema.__marshmallow_object_class__ = cls

    @classmethod
    def from_json(
        cls: Type['JSONType'], data: JSON, schema_kwargs=None, load_kwargs=None
    ):
        """Instantiate this class from JSON.

        Args:
            data: The data to load.
            schema_kwargs: Kwargs to pass through to this classes schemas init
                method. See :class:`.marshmallow.Schema` for details.
            load_kwargs: Kwargs to pass through to this classes schemas load
                method. See :meth:`.marshmallow.Schema.load` for details.
        """
        schema_kwargs = schema_kwargs or {}
        load_kwargs = load_kwargs or {}
        schema = cls.__marshmallow_schema__(**schema_kwargs)
        return schema.load(data, **load_kwargs)

    def to_json(self: 'JSONType', schema_kwargs=None, dump_kwargs=None):
        """Dump an instance of this class to JSON.

        Args:
            schema_kwargs: Kwargs to pass through to this classes schemas init
                method. See :class:`.marshmallow.Schema` for details.
            dump_kwargs: Kwargs to pass through to this classes schemas dump
                method. See :meth:`.marshmallow.Schema.dump` for details.
        """
        schema_kwargs = schema_kwargs or {}
        dump_kwargs = dump_kwargs or {}
        schema = self.__marshmallow_schema__(**schema_kwargs)
        return schema.dump(self, **dump_kwargs)


class JSONTypeSchema(Schema):
    """Base class for schemas for JSONTypes.

    This class mixes in a make_obj method that is registered as a marshmallow
    post_load hook. This ensures that the data will be loaded into a JSONType
    class instance, not just a dict. The hook is registered here but the actual
    object class is only accessed at runtime, after the schema has been linked
    with its JSONType.

    This class is set to exclude unknown fields by default. This is because one
    of the core use cases of this class are custom context classes, and
    Dialogflow adds its own fields there all the time. This can of course
    always be overridden in subclasses.
    """

    class Meta:
        unknown = EXCLUDE

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.__marshmallow_object_class__ = None

    @post_load
    def make_obj(self, data: JSON):
        if not callable(self.__class__.__marshmallow_object_class__):
            return data
        return self.__class__.__marshmallow_object_class__(**data)

    @post_dump
    def remove_skip_values(self, data):
        data_copy = data.copy()
        for key, value in data_copy.items():
            if value is None:
                del data[key]
            elif type(value) is list and len(value) == 0:
                del data[key]
            elif type(value) is dict and len(value) == 0:
                del data[key]
        return data


class ModuleLocalNested(Nested):
    """Nested field subclass that can be parametrized with the modules `FQN`_.

    .. _FQN: https://docs.python.org/3/glossary.html#term-qualified-name

    Nested marshmallow fields get the name of schema of the nested class as a
    string. This string can be just the schemas name itself, but it is usually
    more robust to give the fully qualified name with the module path. As our
    schemas typically reside in the same module as the object classes we would
    like to have the fully qualified name used automatically. This
    :class:`.fields.Nested` subclass makes this possible by accepting the
    module name as a string and then building the full name for every field
    where it is used.

    Example: ::

        # In some_api_module.py: Parametrize the nested field with the
        # module name by using a partial
        from functoools import partial
        Nested = partial(ModuleLocalNested, module_name=__name__)

        class _SomeSchema(Schema):
            ...

        class _SomeOtherSchema(Schema):
            some_nested_field = Nested('_SomeSchema')

        # The nested schema is now stored as some_api_module._SomeSchema

    """

    def __init__(
        self, nested: Union[str, Schema], module_name: Optional[str] = None, *args, **kwargs
    ):
        if isinstance(nested, str) and module_name:
            nested = module_name + '.' + nested
        super().__init__(nested, *args, **kwargs)

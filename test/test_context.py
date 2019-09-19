# -*- coding: utf-8 -*-
"""
    test_context
    ~~~~~~~

    :copyright: (c) 2018 ONSEI GmbH
    :license: Proprietary
"""
import re
from typing import Iterator

import pytest

from flask_dialogflow.context import (
    Context as Context,
    ContextRegistry,
    ContextRegistryEntry,
    ContextManager,
    make_full_ctx_name,
    _is_full_ctx_name,
    _is_valid_ctx_display_name,
)
from flask_dialogflow.exceptions import ContextNotRegisteredError


class TestContext:

    def test_serialization(self):
        ctx = Context('foo', 5, parameters={'bar': 'baz'})
        expected = {
            'name': 'foo',
            'lifespanCount': 5,
            'parameters': {'bar': 'baz'}
        }
        assert ctx.to_json() == expected

    def test_deserialization(self):
        ctx = {
            'name': 'foo',
            'lifespanCount': 5,
            'parameters': {'bar': 'baz'}
        }
        expected = Context('foo', 5, parameters={'bar': 'baz'})
        assert Context.from_json(ctx) == expected

    @pytest.mark.skip('Dict protocol currently not supported')
    def test_getitem(self):
        ctx = Context('foo', 5, parameters={'bar': 'baz'})
        assert ctx['bar'] == ctx.parameters['bar']

    @pytest.mark.skip('Dict protocol currently not supported')
    def test_setitem(self):
        ctx = Context('foo', 5, parameters={'bar': 'baz'})
        ctx['bar'] = 42
        assert ctx.parameters['bar'] == 42

    @pytest.mark.skip('Dict protocol currently not supported')
    def test_delitem(self):
        ctx = Context('foo', 5, parameters={'bar': 'baz'})
        del ctx['bar']
        assert ctx.parameters == {}

    @pytest.mark.skip('Dict protocol currently not supported')
    def test_len(self):
        ctx = Context('foo', 5, parameters={'bar': 'baz'})
        assert len(ctx) == len(ctx.parameters)

    @pytest.mark.skip('Dict protocol currently not supported')
    def test_iter(self):
        ctx = Context('foo', 5, parameters={'bar': 'baz'})
        ctx_iter = iter(ctx)
        assert isinstance(ctx_iter, Iterator)
        assert next(ctx_iter) == 'bar'
        with pytest.raises(StopIteration):
            _ = next(ctx_iter)

    @pytest.mark.parametrize('name, expected', [
        ('/project/abc/session/xyz/foo', 'foo'),
        ('foo', 'foo'),
        (None, None)
    ])
    def test_display_name(self, name, expected):
        assert Context(name).display_name == expected


class TestContextRegistry:

    def test_empty_init(self):
        ContextRegistry()

    @pytest.fixture
    def registry(self):
        return ContextRegistry()

    def test_name_only_registers_empty_entry(self, registry):
        registry.register('foo')
        assert registry._contexts['foo'] == ContextRegistryEntry('foo')

    def test_update_existing_entry(self, registry):
        def fac1():
            return 42
        registry.register('foo', default_factory=fac1)
        assert registry.get_default_factory('foo') == fac1

        def fac2():
            return 1000
        registry.register('foo', default_factory=fac2)
        assert registry.get_default_factory('foo') == fac2

    def test_contains(self, registry):
        registry.register('foo')
        assert 'foo' in registry

    def test_iter(self, registry):
        assert isinstance(iter(registry), Iterator)

    def test_len(self, registry):
        assert isinstance(len(registry), int)

    def test_get_default_factory(self, registry):
        def fac():
            return 42
        registry.register('foo', default_factory=fac)
        assert registry.get_default_factory('foo') == fac

    def test_have_default_factories(self, registry):
        registry.register('foo', default_factory=lambda: 42)
        registry.register('bar')
        default_factories = registry.have_default_factories()
        assert 'foo' in default_factories
        assert 'bar' not in default_factories

    def test_get_serializer(self, registry):
        serializer = lambda params: 42
        registry.register('foo', serializer=serializer)
        assert registry.get_serializer('foo') == serializer

    def test_get_serializer_key_error_when_not_registered(self, registry):
        with pytest.raises(ContextNotRegisteredError):
            registry.get_serializer('foo')

    def test_get_deserializer(self, registry):
        deserializer = lambda params: 42
        registry.register('foo', deserializer=deserializer)
        assert registry.get_deserializer('foo') == deserializer

    def test_get_deserializer_key_error_when_not_registered(self, registry):
        with pytest.raises(ContextNotRegisteredError):
            registry.get_deserializer('foo')

    def test_unregister(self, registry):
        registry.register('foo', keep_around=True)
        assert registry.should_keep_around('foo') is True
        registry.unregister('foo')
        with pytest.raises(ContextNotRegisteredError):
            registry.should_keep_around('foo')

    def test_unregister_is_no_op_when_not_registered(self, registry):
        assert registry.unregister('foo') is None

    def test_list_entries(self, registry):
        registry.register('foo')
        as_list = registry.list_entries()
        assert hasattr(as_list, '__iter__')
        assert any(ctx.display_name == 'foo' for ctx in as_list)

    def test_repr(self, registry):
        registry.register('foo')
        assert '1' in repr(registry)


class TestContextManager:

    @pytest.fixture
    def ctx_manager(self):
        return ContextManager(session='foo/bar')

    def test_init(self):
        assert isinstance(ContextManager([Context()]), ContextManager)

    def test_emtpy_init(self):
        assert isinstance(ContextManager(), ContextManager)

    def test_get(self):
        ctx = Context('foo')
        ctx_manager = ContextManager([ctx])
        assert ctx_manager.get('foo') == ctx

    def test_get_as_attribute(self):
        ctx = Context('foo')
        ctx_manager = ContextManager([ctx])
        assert ctx_manager.foo == ctx

    def test_set(self, ctx_manager):
        ctx_manager.set('foo', 5, bar='baz')
        assert len(ctx_manager) == 1
        ctx = ctx_manager.get('foo')
        assert ctx.name == 'foo/bar/contexts/foo'
        assert ctx.lifespan_count == 5
        assert ctx.parameters == {'bar': 'baz'}

    def test_set_with_ctx_instance(self, ctx_manager):
        ctx = Context('foo', 5, parameters={'bar': 'baz'})
        ctx_manager.set(ctx)
        assert ctx_manager.get('foo') == ctx

    def test_set_with_ctx_instance_with_full_name(self, ctx_manager):
        ctx = Context(
            name='projects/bar/agent/sessions/baz/contexts/foo',
            lifespan_count=5,
            parameters={'bar': 'baz'})
        ctx_manager.set(ctx)
        assert ctx_manager.get('foo') == ctx

    def test_set_with_ctx_instance_and_params(self, ctx_manager):
        ctx = Context('foo', 5, parameters={'bar': 'baz'})
        with pytest.raises(ValueError):
            ctx_manager.set(ctx, lifespan_count=5)
        with pytest.raises(ValueError):
            ctx_manager.set(ctx, bar='baz')

    def test_set_with_invalid_display_name(self, ctx_manager):
        ctx = Context('föö', 5, parameters={'bar': 'baz'})
        with pytest.raises(ValueError):
            ctx_manager.set(ctx)

    def test_set_make_full_ctx_name(self, ctx_manager):
        ctx_manager.set('baz')
        assert ctx_manager.get('baz').name == 'foo/bar/contexts/baz'

    def test_delete(self):
        ctx_manager = ContextManager([Context('foo')])
        ctx_manager.delete('foo')
        assert 'foo' not in ctx_manager
        assert 'foo' in ctx_manager._marked_for_deletion

    def test_delete_keep_in_registry(self):
        ctx_manager = ContextManager([Context('foo')])
        ctx_manager._context_registry.register('foo', keep_around=True)
        assert ctx_manager._context_registry.should_keep_around('foo')
        ctx_manager.delete('foo', keep_in_registry=True)
        assert 'foo' not in ctx_manager
        assert 'foo' in ctx_manager._marked_for_deletion
        assert ctx_manager._context_registry.should_keep_around('foo')

    def test_delete_dont_keep_in_registry(self):
        ctx_manager = ContextManager([Context('foo')])
        ctx_manager._context_registry.register('foo', keep_around=True)
        assert ctx_manager._context_registry.should_keep_around('foo')
        ctx_manager.delete('foo', keep_in_registry=False)
        assert 'foo' not in ctx_manager
        assert 'foo' in ctx_manager._marked_for_deletion
        with pytest.raises(ContextNotRegisteredError):
            assert ctx_manager._context_registry.should_keep_around('foo')

    def test_delete_as_attribute(self):
        ctx_manager = ContextManager([Context('foo')])
        del ctx_manager.foo
        assert 'foo' not in ctx_manager
        assert 'foo' in ctx_manager._marked_for_deletion

    def test_has(self):
        ctx_manager = ContextManager([Context('foo')])
        assert ctx_manager.has('foo')
        assert not ctx_manager.has('bar')

    def test_in_operator(self):
        ctx_manager = ContextManager([Context('foo')])
        assert 'foo' in ctx_manager
        assert 'bar 'not in ctx_manager

    def test_collection_contains(self):
        ctx_manager = ContextManager([Context('foo')])
        assert 'foo' in ctx_manager
        assert 'bar' not in ctx_manager

    def test_collection_len(self):
        assert len(ContextManager()) == 0

    def test_collection_iter(self):
        ctx = Context('foo')
        ctx_manager = ContextManager([ctx])
        ctx_iter = iter(ctx_manager)
        assert isinstance(ctx_iter, Iterator)
        assert next(ctx_iter) == ctx
        with pytest.raises(StopIteration):
            next(ctx_iter)

    def test_getattr(self):
        ctx = Context('foo')
        ctx_manager = ContextManager([ctx])
        assert ctx_manager.foo == ctx
        with pytest.raises(AttributeError):
            _ = ctx_manager.bar

    @pytest.mark.skip('Dict protocol currently not supported')
    def test_getattr_to_ctx_param(self):
        ctx = Context('foo', parameters={'bar': 'baz'})
        ctx_manager = ContextManager([ctx])
        assert ctx_manager.foo['bar'] == 'baz'

    def test_delattr(self):
        ctx = Context('foo')
        ctx_manager = ContextManager([ctx])
        del ctx_manager.foo
        assert 'foo' not in ctx_manager
        with pytest.raises(AttributeError):
            del ctx_manager.bar

    @pytest.mark.skip('Dict protocol currently not supported')
    def test_delattr_to_ctx_param(self):
        ctx = Context('foo', parameters={'bar': 'baz'})
        ctx_manager = ContextManager([ctx])
        del ctx_manager.foo['bar']
        assert ctx.parameters == {}

    def test_as_list(self):
        contexts = [Context('foo'), Context('bar')]
        ctx_manager = ContextManager(contexts)
        assert ctx_manager.as_list() == contexts

    def test_as_list_with_deleted_ctx(self):
        contexts = [
            Context('foo', lifespan_count=5), Context('bar', lifespan_count=5)
        ]
        ctx_manager = ContextManager(contexts)
        ctx_manager.delete('bar')
        as_list = ctx_manager.as_list()
        assert len(as_list) == 2
        assert as_list[0].lifespan_count == 5
        assert as_list[1].lifespan_count == 0


def test_make_full_ctx_name():
    name = make_full_ctx_name(session='foo/bar', display_name='baz')
    assert name == 'foo/bar/contexts/baz'


@pytest.mark.parametrize('name, pattern, expected', [
    ('projects/abc/agent/sessions/xyz/contexts/foo', None, True),
    ('projects/abc/agent/sessions/xyz/contexts/foo-bar', None, True),
    ('projects/abc/agent/sessions/xyz/contexts/', None, False),
    ('foo', None, False),
    ('sessions/xyz/contexts/foo', None, False),
    ('sessions/xyz/contexts/foo', re.compile(r'.*?'), True)
])
def test_is_full_ctx_name(name, pattern, expected):
    assert _is_full_ctx_name(name, pattern) is expected


@pytest.mark.parametrize('name, pattern, expected', [
    ('foo', None, True),
    ('foo-bar', None, True),
    ('föö', None, False),
    ('foo bar', None, False),
    ('', None, False),
    ('foo', re.compile(r'.*?'), True),
])
def test_is_valid_ctx_display_name(name, pattern, expected):
    assert _is_valid_ctx_display_name(name, pattern) is expected

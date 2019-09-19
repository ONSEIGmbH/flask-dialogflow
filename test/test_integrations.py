# -*- coding: utf-8 -*-
"""
    test_integrations
    ~~~~~~~

    :copyright: (c) 2018 ONSEI GmbH
    :license: Proprietary
"""
import pytest

from flask_dialogflow.exceptions import AmbiguousIntegrationError
from flask_dialogflow.google_apis.dialogflow_v2 import OriginalDetectIntentRequest
from flask_dialogflow.integrations import (
    AbstractIntegrationConversation,
    GenericIntegrationConversation,
    IntegrationRegistry
)


class TestAbstractIntegrationConversation:

    def test_from_webhook_request_payload(self):
        with pytest.raises(NotImplementedError):
            AbstractIntegrationConversation.from_webhook_request_payload({})

    def to_webhook_response_payload(self):
        with pytest.raises(NotImplementedError):
            AbstractIntegrationConversation().to_webhook_response_payload()


class TestGenericIntegrationConversation:

    @pytest.mark.parametrize('payload, expected_data', [
        (None, {}),
        ({}, {}),
        ({'foo': 'bar', 'baz': 42}, {'foo': 'bar', 'baz': 42})])
    def test_from_webhook_request_payload(self, payload, expected_data):
        conv = GenericIntegrationConversation.from_webhook_request_payload(
            payload
        )
        assert isinstance(conv, AbstractIntegrationConversation)
        assert conv._data == expected_data

    @pytest.fixture
    def conv(self):
        return GenericIntegrationConversation.from_webhook_request_payload(
            {'foo': 'bar', 'baz': 42}
        )

    def test_getitem(self, conv):
        assert conv['foo'] == conv._data['foo']

    def test_setitem(self, conv):
        conv['baz'] = 1000
        assert conv._data['baz'] == 1000

    def test_delitem(self, conv):
        del conv['baz']
        assert 'baz' not in conv._data

    def test_len(self, conv):
        assert len(conv) == len(conv._data)

    def test_iter(self, conv):
        assert list(iter(conv)) == list(iter(conv._data))

    def test_to_webhook_response_payload(self, conv):
        assert conv.to_webhook_response_payload() == conv._data


class TestIntegrationRegistry:

    def test_init(self):
        reg = IntegrationRegistry()
        assert (
            reg.default_integration_conv_cls == GenericIntegrationConversation
        )
        assert reg._integrations == {}

    @pytest.fixture
    def registry(self):
        return IntegrationRegistry()

    def test_register(self, registry):
        registry.register('foo', object, 'bar')
        assert registry._integrations[('foo', 'bar')] == (object, {})

    def test_error_on_duplicate_registration(self, registry):
        registry.register('foo', object, 'bar')
        with pytest.raises(AmbiguousIntegrationError):
            registry.register('foo', object, 'bar')

    def test_lookup(self, registry):
        registry.register('foo', object, 'bar')
        assert registry.lookup('foo', 'bar') == (object, {})

    def test_lookup_source_only(self, registry):
        registry.register('foo', object)
        assert registry.lookup('foo') == (object, {})

    def test_lookup_non_registered(self, registry):
        assert registry.lookup('foo') is None

    def test_unregister(self, registry):
        registry.register('foo', object)
        assert registry.lookup('foo') is not None
        registry.unregister('foo')
        assert registry.lookup('foo') is None

    def test_unregister_does_nothing_when_not_registered(self, registry):
        registry.unregister('foo')

    @pytest.fixture
    def odir(self):
        return OriginalDetectIntentRequest(
            source='foo',
            version='bar',
            payload={'baz': 42}
        )

    def test_init_integration_convs_with_custom_conv(self, registry, odir):
        class FooConv(GenericIntegrationConversation):
            pass
        registry.register('foo', FooConv, 'bar')
        convs = registry.init_integration_convs(odir)
        assert isinstance(convs['foo'], FooConv)
        assert isinstance(
            convs['foobarbaz'], GenericIntegrationConversation
        )

    def test_init_integration_convs_without_custom_conv(self, registry, odir):
        convs = registry.init_integration_convs(odir)
        assert isinstance(convs['foo'], GenericIntegrationConversation)
        assert isinstance(
            convs['foobarbaz'], GenericIntegrationConversation
        )

    def test_list_entries(self, registry):
        registry.register('foo', object)
        entries = list(registry.list_entries())
        assert entries == [('foo', None, object, {})]

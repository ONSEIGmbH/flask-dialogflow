# -*- coding: utf-8 -*-
"""
    test_exceptions
    ~~~~~~~

    :copyright: (c) 2018 ONSEI GmbH
    :license: Proprietary
"""
from flask_dialogflow.exceptions import (
    DialogflowAgentError,
    AmbiguousHandlerError,
    AmbiguousIntegrationError,
    ContextNotRegisteredError,
    ContextClassNotSerializableError,
)
from flask_dialogflow.integrations import GenericIntegrationConversation


def test_DialogflowAgentError():
    assert 'foo' in str(DialogflowAgentError('foo'))


def test_AmbiguousHandlerError():
    def handler():
        return
    err = AmbiguousHandlerError(intent='FooIntent', existing_handler=handler)
    assert 'FooIntent' in str(err)
    assert __name__ + '.handler' in str(err)


def test_AmbiguousIntegrationError():
    err = AmbiguousIntegrationError(
        source='foo', existing_cls=GenericIntegrationConversation, version='2'
    )
    assert 'foo' in str(err)
    assert str(GenericIntegrationConversation) in str(err)
    assert '2' in str(err)


def test_ContextNotRegisteredError():
    assert 'foo' in str(ContextNotRegisteredError(display_name='foo'))


def test_ContextClassNotSerializableError():
    class Foo:
        pass
    err = ContextClassNotSerializableError(Foo)
    assert 'JSONType' in str(err)
    assert str(Foo) in str(err)

# -*- coding: utf-8 -*-
"""
    test_agent
    ~~~~~~~

    :copyright: (c) 2018 ONSEI GmbH
    :license: Proprietary
"""
import logging
from dataclasses import dataclass, asdict
from typing import Optional
from unittest.mock import Mock

import pytest
from flask import Flask
from flask.logging import has_level_handler
from jinja2 import ChoiceLoader
from marshmallow.fields import Int, Str

from flask_dialogflow.agent import (
    DIALOGFLOW_VERSIONS,
    _validate_dialogflow_version,
    build_webhook_request,
    DialogflowAgent,
    TestWebhookResponse,
    _create_default_handler,
)
from flask_dialogflow.context import (
    SessionContext,
    CTX_KEEP_AROUND_LIFESPAN
)
from flask_dialogflow.exceptions import (
    DialogflowAgentError,
    AmbiguousHandlerError,
    ContextClassNotSerializableError
)
from flask_dialogflow.google_apis.dialogflow_v2 import (
    WebhookRequest,
    WebhookResponse,
    Context,
)
from flask_dialogflow.integrations import (
    AbstractIntegrationConversation
)
from flask_dialogflow.json import JSONType, JSONTypeSchema, JSON
from flask_dialogflow.templating import YamlLoaderWithRandomization


def test_validate_dialogflow_version_valid_version():
    valid_version = DIALOGFLOW_VERSIONS.copy().popitem()[0]
    assert _validate_dialogflow_version(valid_version) is None


def test_validate_dialogflow_version_invalid_version():
    invalid_version = DIALOGFLOW_VERSIONS.copy().popitem()[0] + 'foobar123'
    with pytest.raises(ValueError):
        _validate_dialogflow_version(invalid_version)


class TestDialogflowAgent:

    # @pytest.mark.parametrize('version', DIALOGFLOW_VERSIONS)
    # def test_basic_functionality(self, templates_file, version):
    #     """End-to-end test of the request handling."""
    #     app = Flask(__name__)
    #     agent = DialogflowAgent(
    #         app, templates_file=templates_file, version=version
    #     )
    #
    #     @agent.handle('Test')
    #     def handler(conv):
    #         conv.ask('Hello world!')
    #         return conv
    #
    #     request = {
    #         'queryResult': {
    #             'intent': {
    #                 'displayName': 'Test'
    #             }
    #         },
    #         'originalDetectIntentRequest': {
    #             'source': 'test'
    #         },
    #         'session': 'project/test/agent/sessions/foobar'
    #     }
    #
    #     with app.test_client() as client:
    #         rv = client.post('/', json=request)
    #         resp = rv.get_json()
    #
    #     text = resp['fulfillmentMessages'][0]['text']['text'][0]
    #     assert text == 'Hello world!'

    @pytest.mark.parametrize('version', DIALOGFLOW_VERSIONS)
    def test_basic_context_functionality(self, templates_file, version):
        """End-to-end test of the context registration and handling.

        This is a long test of two consecutive requests through Flask and the
        agent. It verifies that the registration of custom context classes
        works as expected. The scenario is a game state context, which is used
        as an example in the documentation.

        Note that this is obviously not meant to replace the tests of the
        individual parts of the context system, see
        TestDialogflowAgentContextAPI and the test_context module for them.
        """
        # Setup a new Flask app and an agent
        app = Flask(__name__)
        agent = DialogflowAgent(
            app, templates_file=templates_file, version=version
        )

        # Schema for the custom context class
        class _GameStateSchema(JSONTypeSchema):
            questions_answered = Int()
            last_answer = Str()

        # Implement and register the custom context class. Serialization should
        # be completely hidden behind the scenes.
        @agent.context('game_state', keep_around=True)
        @dataclass
        class GameState(JSONType, schema=_GameStateSchema):
            questions_answered: int = 0
            last_answer: Optional[str] = None

        # # Now a handler that works with the context class
        # @agent.handle('CorrectAnswer')
        # def handler(conv):
        #     # Assert that the context has been properly initialized if
        #     # necessary
        #     assert 'game_state' in conv.contexts
        #     assert isinstance(conv.contexts.game_state.parameters, GameState)
        #     conv.contexts.game_state.parameters.questions_answered += 1
        #     conv.contexts.game_state.parameters.last_answer = 'foo bar'
        #     return conv
        #
        # # Setup a minimal request as it would come from Dialogflow
        # request = {
        #     'queryResult': {
        #         'intent': {
        #             'displayName': 'CorrectAnswer'
        #         }
        #     },
        #     'originalDetectIntentRequest': {
        #         'source': 'test'
        #     },
        #     'session': 'project/test/agent/sessions/foobar'
        # }
        #
        # # Send it via Flasks test client to ensure that this really is
        # # end-to-end
        # with app.test_client() as client:
        #     rv = client.post('/', json=request)
        #     response = rv.get_json()
        #
        # # Now examine the response
        # # First: The game_state ctx should be there
        # assert any(
        #     ctx['name'].endswith('game_state')
        #     for ctx in response['outputContexts']
        # )
        # game_state_ctx = [
        #     ctx for ctx in response['outputContexts']
        #     if ctx['name'].endswith('game_state')
        # ][0]
        # # Next: It should have a long remaining lifespan
        # assert game_state_ctx['lifespanCount'] == CTX_KEEP_AROUND_LIFESPAN
        # # And: Its params should be what we set them to
        # expected = {
        #     'questions_answered': 1,
        #     'last_answer': 'foo bar'
        # }
        # assert game_state_ctx['parameters'] == expected
        #
        # # Now prepare a second request, were the context is already present
        # second_request = request.copy()
        # existing_context = game_state_ctx['parameters'].copy()
        # del request, response, expected, game_state_ctx
        # # To make it more realistic: Add random noise to the context
        # existing_context.update(
        #     {'hi-im-dialogflow': 'i-add-my-own-fields-to-your-data'}
        # )
        # second_request['queryResult']['outputContexts'] = [
        #     {
        #         'name': 'game_state',
        #         'lifespanCount': CTX_KEEP_AROUND_LIFESPAN - 1,
        #         'parameters': existing_context
        #     }
        # ]
        #
        # # Second request via Flask
        # with app.test_client() as client:
        #     rv = client.post('/', json=second_request)
        #     response = rv.get_json()
        #
        # # Context should still be there ...
        # assert any(
        #     ctx['name'].endswith('game_state')
        #     for ctx in response['outputContexts']
        # )
        # game_state_ctx = [
        #     ctx for ctx in response['outputContexts']
        #     if ctx['name'].endswith('game_state')
        # ][0]
        # # ... should have the default lifespan again ...
        # assert game_state_ctx['lifespanCount'] == CTX_KEEP_AROUND_LIFESPAN
        # # ... and should have its counter increased once more
        # expected = {
        #     'questions_answered': 2,
        #     'last_answer': 'foo bar'
        # }
        # assert game_state_ctx['parameters'] == expected

    def test_test_request(self, agent):

        @agent.handle('TestTest')
        def handler(conv):
            conv.ask('Hello world!')
            return conv

        resp = agent.test_request('TestTest')
        assert isinstance(resp, WebhookResponse)
        assert resp.fulfillment_messages[0].text.text[0] == 'Hello world!'

    def test_debug_mode_sets_debug_logging_level(self, templates_file):
        agent = DialogflowAgent(debug=True)
        assert agent.logger.getEffectiveLevel() == logging.DEBUG

    def test_debug_mode_adds_handler(self, templates_file):
        agent = DialogflowAgent(debug=True)
        assert has_level_handler(agent.logger)

    def test_repr(self, agent):
        assert agent.__class__.__name__ in repr(agent)


class TestDialogflowAgentInitFlaskApp:

    @pytest.fixture(params=DIALOGFLOW_VERSIONS)
    def uninitialized_agent(self, templates_file):
        return DialogflowAgent(templates_file=templates_file)

    def test_init_app_called_when_app_passed_to_constructor(
            self, app, templates_file, monkeypatch
    ):
        init_app_mock = Mock()
        agent = DialogflowAgent(app, templates_file=templates_file)
        monkeypatch.setattr(agent, 'init_app', init_app_mock)
        init_app_mock.called_once_with(app)

    def test_init_app_not_called_when_no_app_passed_to_constructor(
            self, uninitialized_agent, monkeypatch
    ):
        init_app_mock = Mock()
        monkeypatch.setattr(uninitialized_agent, 'init_app', init_app_mock)
        init_app_mock.assert_not_called()

    def test_init_app_adds_route(
        self, uninitialized_agent, app, templates_file
    ):
        uninitialized_agent.init_app(app)
        url_rule = [
            rule for rule in app.url_map.iter_rules()
            if rule.rule == uninitialized_agent.route
        ]
        assert len(url_rule) == 1
        rule = url_rule[0]
        assert 'POST' in rule.methods
        assert rule.endpoint == uninitialized_agent._flask_view_func.__name__

    def test_init_app_sets_ChoiceLoader(self, uninitialized_agent, app):
        original_loader = app.jinja_loader
        uninitialized_agent.init_app(app)
        assert isinstance(app.jinja_loader, ChoiceLoader)
        assert app.jinja_loader.loaders[0] == original_loader, \
            'Original loader should have been kept as first choice'
        loader = app.jinja_loader.loaders[1]
        assert isinstance(loader, YamlLoaderWithRandomization)
        assert loader.path == uninitialized_agent.templates_file

    def test_init_app_sets_auto_reload(self, uninitialized_agent, app):
        app.debug = False
        assert app.jinja_env.auto_reload is False, \
            'Should have been off when not in debug'
        uninitialized_agent.init_app(app)
        assert app.jinja_env.auto_reload is True

    def test_init_app_adds_reference_to_agent(self, uninitialized_agent, app):
        uninitialized_agent.init_app(app)
        assert app.extensions['flask_dialogflow'] == uninitialized_agent

    def test_init_app_creates_extensions_dict_when_necessary(
            self, uninitialized_agent, app
    ):
        del app.extensions
        uninitialized_agent.init_app(app)
        assert app.extensions['flask_dialogflow'] == uninitialized_agent, \
            'Doing this is recommended by Flask'

    def test_flask_shell_context_processor(self, agent):
        assert agent._flask_shell_context_processor() == {'agent': agent}

    def test_init_app_adds_shell_context_processor(
        self, uninitialized_agent, app
    ):
        uninitialized_agent.init_app(app)
        assert (
            uninitialized_agent._flask_shell_context_processor
            in app.shell_context_processors
        )


class TestDialogflowAgentHandlerAPI:

    def test_registered_handler_is_called(self, agent):
        handler_was_called = False

        def handler(conv):
            nonlocal handler_was_called
            handler_was_called = True
            return conv

        agent.register_handler('HandlerTest', handler)
        agent.test_request('HandlerTest')
        assert handler_was_called

    def test_handle_decorator(self, agent):
        handler_was_called = False

        @agent.handle('HandlerTest')
        def handler(conv):
            nonlocal handler_was_called
            handler_was_called = True
            return conv

        agent.test_request('HandlerTest')
        assert handler_was_called

    def test_double_registration_raises_error(self, agent):
        agent.register_handler('Foo', lambda conv: conv)
        with pytest.raises(AmbiguousHandlerError):
            agent.register_handler('Foo', lambda conv: conv)

    def test_error_when_no_handler_matched(self, agent):
        with pytest.raises(DialogflowAgentError):
            agent.test_request('FooBarIntent')

    def test_list_handler(self, agent):
        handler = lambda conv: conv
        agent.register_handler('HandlerTest', handler)
        assert ('HandlerTest', handler) in agent.list_handler()


class TestDialogflowAgentIntegrationsAPI:
    """Test the handling of integration convs on the agent level."""

    @pytest.fixture
    def foo_conv(self):
        class FooConv(AbstractIntegrationConversation):

            @classmethod
            def from_webhook_request_payload(
                cls, payload: Optional[JSON] = None, **options
            ) -> 'AbstractIntegrationConversation':
                return cls()

            def to_webhook_response_payload(self) -> JSON:
                return {'foo': 'bar', 'baz': 42}

        return FooConv

    def test_register_integration(self, agent, foo_conv):
        agent.register_integration('foo', foo_conv)
        resp = agent.test_request('Test', source='foo')
        assert resp.payload['foo'] == {'foo': 'bar', 'baz': 42}

    def test_integration_decorator(self, agent, foo_conv):
        agent.integration('foo')(foo_conv)
        resp = agent.test_request('Test', source='foo')
        assert resp.payload['foo'] == {'foo': 'bar', 'baz': 42}

    def test_aog_integration_cls_registered_by_default(self, agent):
        aog = ('google', '2')
        assert any(integ[:2] == aog for integ in agent.list_integrations())

    def test_list_integrations(self, agent):
        agent.register_integration('foo', object)
        entries = list(agent.list_integrations())
        assert ('foo', None, object, {}) in entries


class TestDialogflowAgentContextAPI:
    """Test the context handling on the agent level."""

    def test_register_ctx_without_params_does_nothing(self, agent):
        agent.register_context('foo')
        resp = agent.test_request('Test')
        assert not resp.has_context('foo')

    def test_register_ctx_keep_around_resets_lifespan(self, agent):
        agent.register_context('foo', keep_around=True)
        resp = agent.test_request('Test', contexts=[Context('foo', 1)])
        assert resp.has_context('foo')
        assert resp.context('foo').lifespan_count == CTX_KEEP_AROUND_LIFESPAN

    def test_keep_around_lifespan_is_reset_before_handler(self, agent):
        agent.register_context('foo', keep_around=True)
        incoming_ctx = Context('foo', lifespan_count=1)

        @agent.handle('CtxTest')
        def handler(conv):
            assert conv.contexts.foo.lifespan_count == CTX_KEEP_AROUND_LIFESPAN
            return conv

        agent.test_request('CtxTest', contexts=[incoming_ctx])

    def test_register_ctx_default_factory_is_called(self, agent):
        def default():
            return {'foo': 'bar'}
        agent.register_context('foo', default_factory=default)
        resp = agent.test_request('Test')
        assert resp.has_context('foo')
        assert resp.context('foo').parameters == default()

    def test_register_JSONType_context_class(self, agent):
        class FooSchema(JSONTypeSchema):
            bar = Int()

        @agent.context('foo')
        @dataclass
        class Foo(JSONType, schema=FooSchema):
            bar: int

        @agent.handle('CtxTest')
        def handler(conv):
            assert isinstance(conv.contexts.foo.parameters, Foo)
            assert conv.contexts.foo.parameters.bar == 1000
            conv.contexts.foo.parameters.bar = 42
            return conv

        incoming_ctx = Context('foo', parameters={'bar': 1000})
        resp = agent.test_request('CtxTest', contexts=[incoming_ctx])
        assert resp.has_context('foo')
        assert resp.context('foo').parameters == {'bar': 42}

    def test_register_class_with_custom_serializer(self, agent):
        serializer = lambda foo: asdict(foo)
        deserializer = lambda params: Foo(**params)

        @agent.context(
            'foo', serializer=serializer, deserializer=deserializer
        )
        @dataclass
        class Foo:
            bar: int

        @agent.handle('CtxTest')
        def handler(conv):
            assert isinstance(conv.contexts.foo.parameters, Foo)
            assert conv.contexts.foo.parameters.bar == 1000
            conv.contexts.foo.parameters.bar = 42
            return conv

        incoming_ctx = Context('foo', parameters={'bar': 1000})
        resp = agent.test_request('CtxTest', contexts=[incoming_ctx])
        assert resp.has_context('foo')
        assert resp.context('foo').parameters == {'bar': 42}

    def test_error_on_class_registration_without_serializer(self, agent):
        with pytest.raises(ContextClassNotSerializableError):
            @agent.context('foo')
            class Foo:
                pass

    def test_list_contexts(self, agent):
        agent.register_context('foo')
        assert any(ctx.display_name == 'foo' for ctx in agent.list_contexts())


class TestDialogflowAgentSessionContext:

    def test_session_context_gets_set(self, agent):
        resp = agent.test_request('Test')
        assert resp.has_context('_session_context')
        expected = SessionContext().to_json()
        assert resp.context('_session_context').parameters == expected

    def test_fallback_level_increased_on_fallback_intent(self, agent):
        resp = agent.test_request('Test', is_fallback=True)
        session_ctx = resp.context('_session_context')
        fallback_level = session_ctx.parameters['fallback_level']
        assert fallback_level == 1

    def test_fallback_level_increased_on_repeated_fallback_intent(self, agent):
        session_ctx_before = Context(
            '_session_context', parameters={'fallback_level': 2}
        )
        resp = agent.test_request(
            'Test', contexts=[session_ctx_before], is_fallback=True
        )
        session_ctx = resp.context('_session_context')
        fallback_level = session_ctx.parameters['fallback_level']
        assert fallback_level == 3

    def test_fallback_level_reset_on_non_fallback_intent(self, agent):
        session_ctx_before = Context(
            '_session_context', parameters={'fallback_level': 2}
        )
        resp = agent.test_request('Test', contexts=[session_ctx_before])
        session_ctx = resp.context('_session_context')
        fallback_level = session_ctx.parameters['fallback_level']
        assert fallback_level == 0


def test_create_default_handler():
    handler = _create_default_handler()
    assert isinstance(handler, logging.Handler)
    assert isinstance(handler.formatter, logging.Formatter)


def test_build_webhook_request():
    assert isinstance(build_webhook_request(), WebhookRequest)


class TestTestWebhookResponse:

    def test_is_WebhookResponse(self):
        assert issubclass(TestWebhookResponse, WebhookResponse)

    def test_test_request_returns_TestWebhookResponse(self, agent):
        resp = agent.test_request('Test')
        assert isinstance(resp, TestWebhookResponse)

    def test_text_responses(self, agent):

        @agent.handle('TextTest')
        def handler(conv):
            conv.ask('foo')
            conv.show_card(None)
            conv.ask('bar')
            return conv

        resp = agent.test_request('TextTest')
        assert 'foo' in resp.text_responses()
        assert 'bar' in resp.text_responses()
        assert 'baz' not in resp.text_responses()

    def test_has_context(self, agent):
        resp = agent.test_request('Test', contexts=[Context('foo')])
        assert resp.has_context('foo')

    def test_context(self, agent):
        ctx = Context('foo')
        resp = agent.test_request('Test', contexts=[ctx])
        assert resp.context('foo').to_json() == ctx.to_json()

    def test_nonexistent_context(self, agent):
        resp = agent.test_request('Test')
        with pytest.raises(ValueError):
            resp.context('foobar123')

# -*- coding: utf-8 -*-
"""
    flask_dialogflow.agent
    ~~~~~~~~~~~~~~~~~~

    This module contains everything related to the Dialogflow agent as a whole.

    :copyright: (c) 2018 ONSEI GmbH
    :license: Proprietary
"""

import json
import logging
import os
from typing import (
    Callable,
    Optional,
    Tuple,
    Type,
    Mapping,
    Any,
    Iterable,
    MutableMapping,
    Dict,
    MutableSequence,
    Union,
)

from flask import Flask, jsonify, request
from jinja2.loaders import ChoiceLoader

from flask_dialogflow.context import (
    CTX_KEEP_AROUND_LIFESPAN,
    CtxT,
    Context,
    ContextRegistry,
    ContextRegistryEntry,
    ContextDefaultFactory,
    ContextDeserializer,
    ContextSerializer,
    ContextManager,
    SessionContext,
    make_full_ctx_name,
)
from flask_dialogflow.conversation import (
    V2DialogflowConversation,
    V2beta1DialogflowConversation,
)
from flask_dialogflow.exceptions import (
    DialogflowAgentError,
    AmbiguousHandlerError,
    ContextClassNotSerializableError
)
from flask_dialogflow.google_apis import (
    dialogflow_v2, dialogflow_v2beta1, import_dialogflow_api
)
from flask_dialogflow.integrations import (
    AbstractIntegrationConversation,
    IntegrationRegistry,
    IntegrationRegistryEntry
)
from flask_dialogflow.integrations.actions_on_google import (
    V2ActionsOnGoogleDialogflowConversation,
    UserStorageDefaultFactory,
    UserStorageDeserializer,
    UserStorageSerializer,
)
from flask_dialogflow.json import JSONType
from flask_dialogflow.templating import YamlLoaderWithRandomization


DIALOGFLOW_VERSIONS = {
    'v2': V2DialogflowConversation,
    'v2beta1': V2beta1DialogflowConversation,
}

# Types
DialogflowConversation = Union[
    V2DialogflowConversation, V2beta1DialogflowConversation
]
ConversationHandler = Callable[
    [DialogflowConversation], DialogflowConversation
]
WebhookRequest = Union[
    dialogflow_v2.WebhookRequest, dialogflow_v2beta1.WebhookRequest
]
WebhookResponse = Union[
    dialogflow_v2.WebhookResponse, dialogflow_v2beta1.WebhookResponse
]


def _validate_dialogflow_version(version: str) -> None:
    if version not in DIALOGFLOW_VERSIONS:
        raise ValueError(
            f'Invalid Dialogflow version `{version}` '
            f'(valid: {DIALOGFLOW_VERSIONS.keys()}).'
        )


class DialogflowAgent:
    """Dialogflow agent.

    This is the central object that represents the Dialogflow agent and
    integrates this library with Flask. It keeps track of registered intent
    handlers, contexts and integrations and handles requests behind the scenes.
    It initializes a :class:`.DialogflowConversation` for each requests and
    hands it over to the corresponding handler, which does the actual business
    logic needed to fulfill the request.

    Args:
        app: The Flask app to initialize this agent with.
        version: The version of the Dialogflow API to use. Defaults to
            v2beta1, which despite its name appears to be a superset of v2
            (i.e. is completely compatible with it).
        route: The URL endpoint under which this agent will be served. Will be
            registered on the Flask app to accept POST requests.
        templates_file: A single YAML file with the Jinja templates. See
            `templating`_ for details. The path must be relative to the Flask
            apps root_path.
        debug: Debug mode for the agent. If on, every request and response will
            be logged as prettified JSON. Can be set via the ONSEI_GOOGLE_DEBUG
            environment variable.
        aog_user_storage_default_factory: The default factory to use for the
            user_storage of the AoG integration.
        aog_user_storage_deserializer: The function to deserialize the
            user_storage of the AoG integration.
        aog_user_storage_serializer: The function to serialize the user_storage
            of the AoG integration.
        aog_text_to_speech_as_ssml: Whether to send text responses for Actions
            on Google as SSML by default. This makes it possible to use SSML
            directives in templates without additional setup.
    """

    def __init__(
        self,
        app: Optional[Flask] = None,
        version: Optional[str] = 'v2beta1',
        route: Optional[str] = '/',
        templates_file: Optional[str] = 'templates.yaml',
        debug: Optional[bool] = False,
        aog_user_storage_default_factory: Optional[
            UserStorageDefaultFactory
        ] = dict,
        aog_user_storage_deserializer: Optional[
            UserStorageDeserializer
        ] = json.loads,
        aog_user_storage_serializer: Optional[
            UserStorageSerializer
        ] = json.dumps,
        aog_text_to_speech_as_ssml: Optional[bool] = True,
    ) -> None:
        _validate_dialogflow_version(version)
        self._conv_cls = DIALOGFLOW_VERSIONS[version]
        self._df = import_dialogflow_api(version)

        self.app = app
        self.route = route
        self.templates_file = templates_file

        self.debug = debug or os.getenv('ONSEI_GOOGLE_DEBUG')
        self.logger = logging.getLogger('dialogflow.agent')
        self.logger.addHandler(_create_default_handler())
        if self.debug:
            self.logger.setLevel(logging.DEBUG)
        self._handler_registry: MutableMapping[str, 'ConversationHandler'] = {}

        self._integration_registry = IntegrationRegistry()
        self.register_integration(
            source='google',
            integration_conv_cls=V2ActionsOnGoogleDialogflowConversation,
            version='2',
            integration_conv_cls_kwargs={
                'user_storage_serializer': aog_user_storage_serializer,
                'user_storage_deserializer': aog_user_storage_deserializer,
                'user_storage_default_factory':
                    aog_user_storage_default_factory,
                'text_to_speech_as_ssml': aog_text_to_speech_as_ssml
            }
        )

        self._context_registry = ContextRegistry()

        # Register private session context for backend features
        self.context(
            '_session_context',
            keep_around=True,
            default_factory=SessionContext
        )(SessionContext)

        if app is not None:
            self.init_app(app=app)

    def init_app(
        self,
        app: Flask,
        route: Optional[str] = None,
        templates_file: Optional[str] = None
    ) -> None:
        """Initialize a Flask app.

        This can be used to manually initialize a Flask app when it wasn't
        passed to init. Adds the route, the template loader and a shell context
        processor. Sets auto_reload to True on the Jinja env.

        Args:
            app: The Flask app to initialize with this agent.
            route: The URL endpoint for this agent. If None, defaults to the
                agents route.
            templates_file: The YAML templates file. If None, defaults to the
                agents template file.

        Returns:
            None
        """
        app.add_url_rule(
            route or self.route,
            view_func=self._flask_view_func,
            methods=['POST'],
        )

        # Add the YamlLoader, but keep the original one
        templates_file = templates_file or self.templates_file
        templates_path = os.path.join(app.root_path, templates_file)
        app.jinja_loader = ChoiceLoader(
            [app.jinja_loader, YamlLoaderWithRandomization(templates_path)]
        )
        app.jinja_env.auto_reload = True

        # Store a reference to the agent so that we can refer to it from an
        # app context
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['flask_dialogflow'] = self

        # Make the agent available in a flask shell
        app.shell_context_processor(self._flask_shell_context_processor)

    def register_handler(
        self, intent: str, handler: 'ConversationHandler'
    ) -> None:
        """Register a conversation handler.

        Takes the name of an intent (the display_name, i.e. the name it was
        given in the Dialogflow console) and registers a handler function for
        it. All requests to this intent will then be routed to this handler.

        Args:
            intent: The intent to register the handler for.
            handler: The conversation handler for this intent.

        Returns:
            None
        """
        if intent in self._handler_registry:
            raise AmbiguousHandlerError(intent, self._handler_registry[intent])
        self._handler_registry[intent] = handler

    def handle(self, intent: str):
        """Decorator to register conversation handlers.

        Example:

        .. code-block:: python

            @agent.handle('HelloWorld')
            def hello_world_handler(conv):
                # This handler will be called for requests to
                # the HelloWorld intent
                conv.ask('Hello world!')
                return conv

        Args:
            intent: The intent to register the handler for.

        Returns:
            The decorator to be applied to a conversation handler.
        """

        def decorator(f):
            self.register_handler(intent, handler=f)
            return f

        return decorator

    def register_integration(
        self,
        source: str,
        integration_conv_cls: Type['AbstractIntegrationConversation'],
        version: Optional[str] = None,
        integration_conv_cls_kwargs: Optional[Mapping] = None,
    ) -> None:
        """Register an integration conversation class.

        This can be used to register conversation classes for custom
        integrations, i.e. subclasses of
        :class:`.AbstractIntegrationConversation`. The class will then be
        available via the standard DialogflowConversation. Should the webhook
        request from this integration carry custom payload it too will be
        available via conversation object.

        Example:

        Assume you want to integrate your Dialogflow agent with a custom
        speaker that has a blinking light that can be controlled via the
        webhook. You could then write a custom conversation class that
        abstracts this functionality:

        .. code-block:: python

            from flask_dialogflow.integrations import GenericIntegrationConversation

            class BlinkingLightSpeakerConv(GenericIntegrationConversation):
                # Subclass the generic conv to get the usual dict behavior

                def blink(times=1):
                    # Build the JSON payload that makes the light blink
                    self['blink'] = times

            agent.register_integration(
                source='blink_speaker',
                integration_conv_cls=BlinkingLightSpeakerConv
            )

        Now, every DialogflowConversation passed to a handler will have an
        instance of this special conversation object that can be used to make
        the light blink:

        .. code-block:: python

            @agent.handle('BlinkTwice')
            def blink_twice_handler(conv):
                conv.blink_speaker.blink(times=2)
                # ... other response parts as usual
                return conv

        The speaker could carry data when calling Dialogflow (via the
        :attr:`.OriginaDetectIntentRequest.payload`), which can be made
        available via the conversation class. Let's assume the speaker would
        tell the webhook whether the light is currently on or off by sending
        ``{'light_on': True}`` in the payload. The conversation class could
        then make this info available like this:

        .. code-block:: python

            from flask_dialogflow.integrations import GenericIntegrationConversation

            class BlinkingLightSpeakerConv(GenericIntegrationConversation):

                @property
                def light_on(self) -> bool:
                    # The GenericIntegrationConversation is already a dict, we
                    # simply expose this attribute as a property for
                    # convenience
                    return self['light_on']

                def turn_light_off(self):
                    # Method to turn the light off (assuming the speaker
                    # handles this)
                    self['light_on'] = False

        This can now be used in handler functions as well:

        .. code-block:: python

            @agent.handle('TurnLightOff')
            def turn_light_off_handler(conv):
                if conv.blink_speaker.light_on:
                    conv.blink_speaker.turn_light_off()
                return conv

        Args:
            source: The integration platform to use this conversation for.
            integration_conv_cls: The conversation class to use for this
                integration.
            version: Optional version qualifier for the source.
            integration_conv_cls_kwargs: Kwargs to pass to the conversations
                from_webhook_request_payload method.

        Returns:
            None
        """
        self._integration_registry.register(
            source=source,
            integration_conversation=integration_conv_cls,
            version=version,
            integration_conversation_kwargs=integration_conv_cls_kwargs
        )

    def integration(
        self,
        source: str,
        version: Optional[str] = None,
        **kwargs
    ):
        """Decorator version of :meth:`.register_integration`.

        Args:
            source: The integration platform to use this conversation for.
            version: Optional version qualifier for the source.
            **kwargs: Kwargs to pass to the conversations
                from_webhook_request_payload method.
        """

        def decorator(
            cls: Type['AbstractIntegrationConversation']
        ) -> Type['AbstractIntegrationConversation']:
            self.register_integration(source, cls, version, kwargs)
            return cls

        return decorator

    def register_context(
        self,
        display_name: str,
        keep_around: Optional[bool] = False,
        default_factory: Optional[ContextDefaultFactory] = None,
        deserializer: Optional[ContextDeserializer] = None,
        serializer: Optional[ContextSerializer] = None,
    ) -> None:
        """Register a context.

        Registering a context abstracts certain parts of context handling,
        making them easier to work with. Most importantly, it makes it possible
        to represent the parameters of a context as a class instead of a plain
        dictionary and have de-/serialization handled behind the scenes.

        Args:
            display_name: The display name of the context to register.
            keep_around: Ensure that this context never expires by resetting
                its lifespan to a high value on each request. This happens
                before the handler is called, meaning the context can still be
                expired manually. This does not create a context when it
                doesn't already exist, use default_factory for that.
            default_factory: A factory to initialize a context when it is not
                present in a request. This function must only return the
                context parameters (either a dict or a class instance), it will
                be wrapped in a :class:`.Context` object automatically. Setting
                this in combination with keep_around ensures that a context
                will always be present, i.e. that ``conv.contexts.some_ctx``
                never raises an AttributeError.
            deserializer: Function to deserialize the context parameters with.
                Context params will be deserialized with json.load, this
                function can be used to deserialize them further into a class.
                This makes it possible to work with context params as class
                instances instead of dicts and to implement custom context
                classes with additional business logic. Care has to be taken
                though because Dialogflow adds its own fields to contexts,
                the deserializer has to be able to ignore them.
            serializer: Function with which the context params will be
                serialized to JSON.

        Returns:
            None
        """
        self._context_registry.register(
            display_name=display_name,
            keep_around=keep_around,
            default_factory=default_factory,
            deserializer=deserializer,
            serializer=serializer,
        )

    def context(
        self, display_name: str, **kwargs
    ) -> Callable[[Type[CtxT]], Type[CtxT]]:
        """Decorator version of register_context.

        This decorator can be applied to :class:`.JSONType` classes which have
        de-/serialization built in and set the correct deserializer/serializer
        functions automatically. For details on how the JSONTypes work see the
        section on `JSON handling`_. Here is an example how one could realize
        a game state context with this:

        .. code-block:: python

            # Implement the game state class and schema
            from marshmallow.fields import Int, Str
            from flask_dialogflow.json import JSONType, JSONTypeSchema

            class _GameStateSchema(JSONTypeSchema):
                questions_answered = Int()
                last_answer = Str()

            @agent.context('game_state', keep_around=True)
            @dataclass
            class GameState(JSONType, schema=_GameStateSchema):
                questions_answered: int = 0
                last_answer: Optional[str] = None

        This ensures that:
            * The ``game_state`` context will always be present.
            * It will be correctly initialized if necessary.
            * Its lifespan never expires.
            * The :attr:`.Context.parameters` are an instance of the GameState
              class, not a dict.

        In a handler this context could be used like this:

        .. code-block:: python

            @agent.handle('CorrectAnswer')
            def handle_correct_answer(conv):
                conv.contexts.game_state.parameters.questions_answered += 1
                conv.contexts.game_state.parameters.last_answer = ...
                return conv

        Applying this decorator to a non-JSONType class requires that the
        deserializer and serializer are provided manually, which is the same as
        calling :meth:`.register_context` directly.

        Args:
            display_name: The display name of the context to register.
            **kwargs: The same kwargs that :meth:`.register_context` takes.

        Returns:
            A class decorator for JSONType subclasses.
        """

        def decorator(cls: Type[CtxT]):
            if issubclass(cls, JSONType):
                kwargs['serializer'] = kwargs.get('serializer', cls.to_json)
                kwargs['deserializer'] = kwargs.get(
                    'deserializer', cls.from_json
                )
                kwargs['default_factory'] = kwargs.get('default_factory', cls)
            if not (kwargs.get('serializer') and kwargs.get('deserializer')):
                raise ContextClassNotSerializableError(cls)
            self.register_context(display_name, **kwargs)
            return cls

        return decorator

    def list_handler(self) -> Iterable[Tuple[str, ConversationHandler]]:
        """List all registered handlers.

        Yields:
            Tuples of (intent name, handler function).
        """
        yield from self._handler_registry.items()

    def list_integrations(self) -> Iterable[IntegrationRegistryEntry]:
        """List all registered integrations.

        Yields:
            Tuples of (source, integration conv class, version, kwargs).
        """
        yield from self._integration_registry.list_entries()

    def list_contexts(self) -> Iterable['ContextRegistryEntry']:
        """List all registered contexts.

        Yields:
            ContextRegistryEntry objects that contain information about the
            contexts.
        """
        yield from self._context_registry.list_entries()

    def test_request(self, *args, **kwargs) -> 'TestWebhookResponse':
        """Make a test request.

        This builds a :class:`.WebhookRequest` from the passed parameters and
        processes it like a normal request. Everything that happens between the
        deserialization of a requests POST payload and the serialization of
        the handlers response will also happen during this test request. It can
        thus be used to quickly test the agents request handling end-to-end.

        Example:

        .. code-block:: python

            resp = agent.test_request('HelloWorld')
            # Builds a request for the 'HelloWorld' intent and passes it
            # through the agent. resp is now the webhook response that would be
            # send back to Dialogflow.

        This does not involve Flask and does thus also not need an active app
        or request context.

        Args:
            args, kwargs: The arguments are the same that
                :func:`.build_webhook_request` takes. The first one is the
                intent name.

        Returns:
            An instance of :class:`.TestWebhookResponse`, a
            :class:`.WebhookRequest` subclass that offers some additional
            methods to make assertions about the response.
        """
        webhook_request = build_webhook_request(*args, **kwargs)
        webhook_response = self._handle_request(webhook_request)
        return TestWebhookResponse.from_webhook_response(webhook_response)

    def _flask_view_func(self, *args, **kwargs):
        """The Flask view func."""
        request_payload = request.get_json()
        self._log_json(request_payload)
        webhook_request = self._df.WebhookRequest.from_json(request_payload)
        webhook_response = self._handle_request(webhook_request)
        response_body = webhook_response.to_json()
        self._log_json(response_body)
        return jsonify(response_body)

    def _lookup_conversation_handler(
        self, conv: DialogflowConversation
    ) -> 'ConversationHandler':
        """Match a conversation to the right handler.

        Raises:
            DialogflowAgentError: When the intent does not match any handler.
        """
        intent = conv.webhook_request.query_result.intent.display_name
        try:
            handler = self._handler_registry[intent]
        except KeyError:
            raise DialogflowAgentError(
                f'No conversation handler matched for intent `{intent}`.'
            )
        return handler

    def _handle_request(
        self, webhook_request: WebhookRequest
    ) -> WebhookResponse:
        """Handle a WebhookRequest and produce a WebhookResponse."""
        conv = self._initialize_conversation(webhook_request)
        handler = self._lookup_conversation_handler(conv)
        conv = handler(conv)
        self._serialize_context_params(conv.contexts)
        webhook_response = conv.to_webhook_response()
        return webhook_response

    def _initialize_conversation(
        self, webhook_request: WebhookRequest
    ) -> DialogflowConversation:
        """Initialize the conversation object from a WebhookRequest."""
        contexts = [
            Context.from_context(ctx) for ctx in
            webhook_request.query_result.output_contexts
        ]
        self._deserialize_context_params(contexts)
        self._initialize_default_contexts(contexts, webhook_request.session)
        self._reset_lifespan_of_keep_around_contexts(contexts)
        context_manager = ContextManager(
            contexts=contexts,
            session=webhook_request.session,
            context_registry=self._context_registry
        )
        integration_convs = self._integration_registry.init_integration_convs(
            webhook_request.original_detect_intent_request
        )
        return self._conv_cls(
            webhook_request,
            context_manager=context_manager,
            integration_convs=integration_convs,
        )

    def _initialize_default_contexts(
        self, contexts: MutableSequence['Context'], session: str
    ) -> None:
        """Initialize contexts that have a default but are not present."""
        present = set(ctx.display_name for ctx in contexts)
        missing = self._context_registry.have_default_factories() - present
        for name in missing:
            default_factory = self._context_registry.get_default_factory(name)
            parameters = default_factory()
            ctx_name = make_full_ctx_name(session, name)
            ctx = Context(ctx_name, parameters=parameters)
            contexts.append(ctx)

    def _reset_lifespan_of_keep_around_contexts(
        self, contexts: Iterable['Context']
    ) -> None:
        """Set lifespan of keep_around contexts to a high value."""
        for ctx in contexts:
            name = ctx.display_name
            if (
                name in self._context_registry
                and self._context_registry.should_keep_around(name)
            ):
                ctx.lifespan_count = CTX_KEEP_AROUND_LIFESPAN

    def _serialize_context_params(
        self, contexts: Iterable['Context']
    ) -> None:
        """Serialize the parameters dict of a context."""
        for ctx in contexts:
            if ctx.display_name in self._context_registry:
                serializer = self._context_registry.get_serializer(
                    ctx.display_name
                )
                if serializer:
                    ctx.parameters = serializer(ctx.parameters)

    def _deserialize_context_params(
        self, contexts: Iterable['Context']
    ) -> None:
        """Deserialize the parameters dict of a context."""
        for ctx in contexts:
            if ctx.display_name in self._context_registry:
                deserializer = self._context_registry.get_deserializer(
                    ctx.display_name
                )
                if deserializer:
                    ctx.parameters = deserializer(ctx.parameters)

    def _log_json(
        self,
        json_data,
        level: Optional[int] = logging.DEBUG,
        header: Optional[str] = None,
        indent: Optional[int] = 4,
        ensure_ascii: Optional[bool] = False,
    ) -> None:
        """Log a JSON object, prettified with an optional header."""
        header = f'{header}\n' if header else ''
        msg = json.dumps(json_data, indent=indent, ensure_ascii=ensure_ascii)
        self.logger.log(level, header + msg)

    def _flask_shell_context_processor(self):
        """The shell context processor for Flask.

        Makes the agent available in a Flask shell.
        """
        return {'agent': self}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} '{self.__module__}'>"


def _create_default_handler() -> logging.Handler:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(asctime)s]: %(message)s'))
    return handler


def build_webhook_request(
    intent: Optional[str] = 'Default Welcome Intent',
    action: Optional[str] = None,
    source: Optional[str] = None,
    session: Optional[str] = 'projects/foo/agent/sessions/bar',
    parameters: Optional[Dict[str, Any]] = None,
    contexts: Optional[Iterable[Context]] = None,
    payload: Optional[Dict[str, Any]] = None,
    is_fallback: Optional[bool] = False,
    dialogflow_version: Optional[str] = 'v2beta1',
) -> WebhookRequest:
    """Factory function to build a :class:`.WebhookRequest`.

    Params not explicitly given are set to sensible defaults, allowing for
    request construction with minimal effort. This functions will rarely be
    used explicitly, but powers other test helpers under the hood, especially
    :meth:`.DialogflowAgent.test_request`, which accepts the same kwargs as
    this function.

    Examples: ::

        # This builds a valid request to the FooIntent
        build_webhook_request('FooIntent')

        # A slighly more complex request with params and context
        from flask_dialogflow.google_apis.dialogflow_v2 import Context

        build_webhook_request(
            intent='FooIntent',
            parameters={'some-date': '2018-10-02T19:30:26Z'},
            contexts=[
                Context('foo_context', parameters={'foo': 'bar'})
            ]
        )

    Args:
        intent: The requests intents display name.
        action: The requests action.
        source: The source from where this request was send to Dialogflow.
        session: The requests session. Must conform to the session str format.
        parameters: The dict of params parsed from the input text.
        contexts: An iterable of :class:`.Context`. Defaults to an empty list
            when not given.
        payload: The platform-specific request payload.
        is_fallback: Whether this intent is a fallback intent.
        dialogflow_version: The Dialogflow version to use. Defaults to v2beta1,
            which has all features.
    """
    _validate_dialogflow_version(dialogflow_version)
    df = import_dialogflow_api(dialogflow_version)
    return df.WebhookRequest(
        session=session,
        query_result=df.QueryResult(
            intent=df.Intent(
                display_name=intent,
                is_fallback=is_fallback
            ),
            action=action,
            parameters=parameters,
            output_contexts=list(contexts or [])
        ),
        original_detect_intent_request=df.OriginalDetectIntentRequest(
            source=source,
            payload=payload
        )
    )


class TestWebhookResponse(dialogflow_v2beta1.WebhookResponse):
    """Response class returned from :meth:`DialogflowAgent.test_request`.

    This is a subclass of :class:`.WebhookRequest` with a few extra methods
    that help in making assertions against the response.
    """

    __test__ = False  # Marker so that pytest doesn't think this is a test cls

    @classmethod
    def from_webhook_response(cls, webhook_response: WebhookResponse):
        """Classmethod to instantiate this from a normal WebhookResponse.

        Used internally, should not be used by users.

        Args:
            webhook_response: The normal :class:`.WebhookResponse` that should
                be converted to this class.
        """
        return cls.from_json(webhook_response.to_json())

    def text_responses(self) -> Iterable[str]:
        """Get an iterable of all individual text responses.

        Note that this yields only the generic Dialogflow responses, i.e.
        responses set via conv.ask, not conv.google.ask.

        Yields:
            The individual text responses.
        """
        for msg in (self.fulfillment_messages or []):
            if msg.text:
                yield from msg.text.text

    def has_context(self, display_name: str) -> bool:
        """Check whether the response has a certain context set.

        This does not check the lifespan of the context because None is a valid
        lifespan that defaults to Dialogflows default lifespan.

        Args:
            display_name: The display name to check for (i.e. the context name
                without the session id).
        """
        return any(
            ctx.name.endswith(display_name) for ctx in self.output_contexts
        )

    def context(self, display_name: str) -> Context:
        """Get a context by its display name.

        Returns the :class:`.Context` object when it is part of this response.
        Throws a ValueError when it is not.

        Args:
            display_name: The display name to get (i.e. the context name
                without the session id).

        Raises:
            ValueError: When the context is not part of the response.
        """
        try:
            return [
                ctx for ctx in self.output_contexts
                if ctx.name.endswith(display_name)
            ][0]
        except IndexError:
            raise ValueError(f'Context `{display_name}` not in this response!')

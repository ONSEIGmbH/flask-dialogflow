# -*- coding: utf-8 -*-
"""
    flask_dialogflow.integrations
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Package for all integration-specific conversation objects.

    :copyright: (c) 2018 ONSEI GmbH
    :license: Proprietary
"""
from abc import abstractmethod
from collections import defaultdict
from collections.abc import MutableMapping
from typing import (
    Optional, Iterator, Type, Mapping, Tuple, DefaultDict, Iterable
)

from flask_dialogflow.exceptions import AmbiguousIntegrationError
from flask_dialogflow.google_apis.dialogflow_v2 import OriginalDetectIntentRequest
from flask_dialogflow.json import JSON


class AbstractIntegrationConversation:
    """Interface for integration-specific conversation objects.

    This interface mandates methods to initialize a conversation from a webhook
    request payload and to render it to JSON for the webhook response. All
    custom integration convs must implement this interface.
    """

    @classmethod
    @abstractmethod
    def from_webhook_request_payload(
        cls, payload: Optional[JSON] = None, **kwargs
    ) -> 'AbstractIntegrationConversation':
        """Initialize this conversation from the webhook request payload.

        Webhook requests contain platform-specific payload. This payload should
        be exposed by the conversation class. This method mandates that the
        conv can be instantiated from the payload (optionally with additional
        kwargs). The payload may be None or an empty dict, implementations
        should be able to handle this.

        Args:
            payload: The webhook request payload for this integration.
            **kwargs: Additional kwargs, which can be set when registering this
                integration with an agent.

        Returns:
            An instance of this conversation, which will be available via the
            :class:`.DialogflowConversation`.
        """
        raise NotImplementedError

    @abstractmethod
    def to_webhook_response_payload(self) -> JSON:
        """Render this conversation back to JSON.

        This method must render the handled conversation back to JSON to be
        included as the integration payload in the webhook response.

        Returns:
            The fully processed conversation.
        """
        raise NotImplementedError  # pragma: no cover


class GenericIntegrationConversation(
    AbstractIntegrationConversation, MutableMapping
):
    """Generic integration conversation.

    This is the default conversation used for all integrations that don't have
    a custom conversation registered. It implements the MutableMapping ABC,
    which means it can be treated as a dict.
    """

    def __init__(self, data: Optional[JSON] = None) -> None:
        self._data = data or {}

    def __setitem__(self, k, v) -> None:
        return self._data.__setitem__(k, v)

    def __delitem__(self, v) -> None:
        return self._data.__delitem__(v)

    def __getitem__(self, k):
        return self._data.__getitem__(k)

    def __len__(self) -> int:
        return self._data.__len__()

    def __iter__(self) -> Iterator:
        return self._data.__iter__()

    @classmethod
    def from_webhook_request_payload(
        cls, payload: Optional[JSON] = None, **kwargs
    ) -> 'GenericIntegrationConversation':
        return cls(payload)

    def to_webhook_response_payload(self) -> JSON:
        return self._data


IntegrationRegistryEntry = Tuple[
    str, Optional[str], 'AbstractIntegrationConversation', Optional[Mapping]
]


class IntegrationRegistry:
    """The registry for integrations on a :class:`.DialogflowAgent`.

    This registry is an implementation detail that end users don't have to
    interact with directly. Instead they should use the
    :meth:`.DialogflowAgent.register_integration` method.

    The registry is basically a dict of (source, version) -> (integration conv,
    kwargs) tuples, wrapped in a nicer API. It is also responsible for
    initializing the integrations dict of a :class:`.DialogflowConversation`,
    which it will do on behalf of the DialogflowAgent.
    """

    def __init__(
        self,
        default_integration_conv_cls: Optional[
            'AbstractIntegrationConversation'
        ] = GenericIntegrationConversation
    ):
        """Initialize the registry with a default integration conv class.

        Args:
            default_integration_conv_cls: The conversation class to use for all
                integrations that do not have a special class registered.
                Defaults to :class:`.GenericIntegrationConversation`, but may
                be replaced with a more elaborate class.
        """
        self.default_integration_conv_cls = default_integration_conv_cls
        self._integrations = {}

    def register(
        self,
        source: str,
        integration_conversation: Type['AbstractIntegrationConversation'],
        version: Optional[str] = None,
        integration_conversation_kwargs: Optional[Mapping] = None
    ) -> None:
        """Register an integration.

        Integrations are identified by their source and optionally a version.
        Both strings are set by Dialogflow servers and send in the webhook
        request, but may be customized when working with the raw Dialogflow
        API. The registered integration conv must implement the
        :class:`.AbstractIntegrationConversation` interface.

        Args:
            source: The source for which this integration conv should be used.
            integration_conversation: The AbstractIntegrationConversation
                subclass to use for conversations with this integration.
            version: Optional version qualifier of the source.
            integration_conversation_kwargs: Kwargs to pass to
                from_webhook_Request_payload when initializing the conversation
                class.

        Returns:
            None

        Raises:
            AmbiguousIntegrationError: When the same (source, version) pair is
                registered twice.
        """
        key = (source, version)
        if key in self._integrations:
            existing_cls, _ = self._integrations[key]
            raise AmbiguousIntegrationError(source, existing_cls, version)
        val = (integration_conversation, integration_conversation_kwargs or {})
        self._integrations[key] = val

    def lookup(
        self, source: str, version: Optional[str] = None
    ) -> Optional[AbstractIntegrationConversation]:
        """Lookup the registered conversation for an integration.

        Args:
            source: The source to lookup the conv for.
            version: Optional version qualifier for the source.

        Returns:
            The AbstractIntegrationConversation subclass registered for this
            integration or None if no class registered.
        """
        return self._integrations.get((source, version))

    def unregister(self, source: str, version: Optional[str] = None) -> None:
        """Unregister an integration conversation class.

        Does nothing if the integration is not registered.

        Args:
            source: The source to unregister the conv for.
            version: Optional version qualifier for the source.

        Returns:
            None
        """
        key = (source, version)
        if key in self._integrations:
            del self._integrations[key]

    def init_integration_convs(
        self, odir: OriginalDetectIntentRequest
    ) -> DefaultDict[str, 'AbstractIntegrationConversation']:
        """Initialize the defaultdict of all registered conversations.

        Takes the :class:`.OriginalDetectIntentRequest` from a webhook request
        (which contains the integration source and the payload) and build the
        defaultdict of integration conversations that can then be passed to the
        :class:`.DialogflowConversation`.

        Args:
            odir: The OriginalDetectIntentRquest of a WebhookRequest,
                containing the integration source and payload.

        Returns:
            A defaultdict of instances of all registered integration convs,
            with the default conv as the dict default.
        """
        integrations = defaultdict(self.default_integration_conv_cls)
        key = (odir.source, odir.version)
        conv_cls = self.lookup(odir.source, odir.version)
        cls, kwargs = conv_cls or (self.default_integration_conv_cls, {})
        integrations[odir.source] = cls.from_webhook_request_payload(
            odir.payload, **kwargs
        )
        for other_key in (set(self._integrations) - set(key)):
            if other_key != key:
                cls, kwargs = self._integrations[other_key]
                integrations[other_key[0]] = cls.from_webhook_request_payload(
                    **kwargs
                )
        return integrations

    def list_entries(self) -> Iterable[IntegrationRegistryEntry]:
        """List all registered integrations convs.

        Yields:
            Tuples of (source, version, integration conv class, integration
            conv kwargs).
        """
        for k, v in self._integrations.items():
            yield k[0], k[1], v[0], v[1]

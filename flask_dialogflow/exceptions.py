# -*- coding: utf-8 -*-
"""
    exceptions
    ~~~~~~~

    :copyright: (c) 2018 ONSEI GmbH
    :license: Proprietary
"""
import inspect
from typing import Type, Optional, TYPE_CHECKING

from flask_dialogflow.json import JSONType

if TYPE_CHECKING:  # pragma: no cover
    from flask_dialogflow.agent import ConversationHandler
    from flask_dialogflow.integrations import AbstractIntegrationConversation


class DialogflowAgentError(Exception):
    """Generic error on a Dialogflow agent."""


class AmbiguousHandlerError(DialogflowAgentError):
    """Exception when trying to register two handlers for the same intent."""

    def __init__(self, intent: str, existing_handler: 'ConversationHandler'):
        handler_path = (
            inspect.getmodule(existing_handler).__name__
            + '.'
            + existing_handler.__name__
        )
        msg = (
            f'Intent `{intent}` already has this handler registered: '
            f'`{handler_path}`'
        )
        super().__init__(msg)


class AmbiguousIntegrationError(DialogflowAgentError):
    """When trying to register two payload classes for the same integration."""

    def __init__(
        self,
        source: str,
        existing_cls: Type['AbstractIntegrationConversation'],
        version: Optional[str] = None,
    ) -> None:
        msg = (
            f"The integration payload (source='{source}', version='{version}'"
            f") already has a cls registered: {existing_cls}."
        )
        super().__init__(msg)


class ContextNotRegisteredError(DialogflowAgentError):
    """Errors on the registry."""

    def __init__(self, display_name: str):
        super().__init__(f'Context `{display_name}` not registered.')


class ContextClassNotSerializableError(DialogflowAgentError):
    """User tried to register a class that needs serializers without them."""

    def __init__(self, cls):
        msg = (
            f'A registered class must either be a '
            f'`{JSONType.__name__}`` subclass or have explicit'
            f' serializer and deserializer, `{cls}` is/does have neither'
        )
        super().__init__(msg)

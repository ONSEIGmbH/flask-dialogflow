# -*- coding: utf-8 -*-
"""
    flask_dialogflow.context
    ~~~~~~~~~~~~~~~~~~~~

    Everything related to context handling.

    :copyright: (c) 2018 ONSEI GmbH
    :license: Proprietary
"""
import re
from dataclasses import dataclass
from functools import wraps
from typing import (
    TypeVar,
    Generic,
    Callable,
    Union,
    Optional,
    Collection,
    MutableMapping,
    Iterator,
    Set,
    Iterable,
    List,
    Pattern,
)

from marshmallow.fields import Int

from flask_dialogflow.exceptions import ContextNotRegisteredError
from flask_dialogflow.google_apis.dialogflow_v2 import Context as Context_
from flask_dialogflow.json import JSON, JSONTypeSchema, JSONType

CTX_KEEP_AROUND_LIFESPAN = 99

CtxT = TypeVar('CtxT')


@dataclass
class Context(Context_, Generic[CtxT]):
    """A wrapper around the API context.

    Adds a display_name property and is parametrizable to give accurate type
    hints when using anything else but a dict for the parameters attribute
    (i.e. when registering this display name with a context class). Otherwise
    exactly the same as the API Context object.
    """

    parameters: CtxT = None

    @property
    def display_name(self):
        """Get the contexts display name, i.e. without the session id."""
        if self.name is None or '/' not in self.name:
            return self.name
        return self.name.rsplit('/')[-1]

    @classmethod
    def from_context(cls, ctx: Context_):
        """Initialize this class from an API context."""
        return cls(
            name=ctx.name,
            lifespan_count=ctx.lifespan_count,
            parameters=ctx.parameters
        )


ContextSerializer = Callable[[CtxT], JSON]
ContextDeserializer = Callable[[JSON], CtxT]
ContextDefaultFactory = Callable[[], CtxT]


@dataclass
class ContextRegistryEntry:
    """Class that holds information about a registered context."""
    display_name: str
    keep_around: Optional[bool] = False
    default_factory: Optional[ContextDefaultFactory] = None
    serializer: Optional[ContextSerializer] = None
    deserializer: Optional[ContextDeserializer] = None


def _except_not_registered(f):
    """Decorator to catch queries for an unregistered context."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except KeyError:
            raise ContextNotRegisteredError(kwargs.get('display_name'))

    return wrapper


class ContextRegistry(Collection[ContextRegistryEntry]):
    """The context registry used to store information about contexts.

    This is an internal class that users do not have to interact with directly.
    """

    def __init__(self):
        self._contexts: MutableMapping[str, ContextRegistryEntry] = {}

    def register(self, display_name: str, **kwargs) -> None:
        if display_name in self._contexts:
            self._update_registry_entry(display_name, **kwargs)
        else:
            self._contexts[display_name] = ContextRegistryEntry(
                display_name, **kwargs
            )

    def _update_registry_entry(self, display_name: str, **kwargs) -> None:
        for k, v in kwargs.items():
            setattr(self._contexts[display_name], k, v)

    def __contains__(self, display_name: str) -> bool:
        return display_name in self._contexts

    def __iter__(self) -> Iterator[ContextRegistryEntry]:
        return iter(self._contexts.values())

    def __len__(self) -> int:
        return len(self._contexts)

    @_except_not_registered
    def should_keep_around(self, display_name: str) -> bool:
        return self._contexts[display_name].keep_around

    def have_default_factories(self) -> Set[str]:
        """Set of all contexts that have defaults."""
        return set(
            ctx.display_name for ctx in self._contexts.values()
            if ctx.default_factory
        )

    @_except_not_registered
    def get_default_factory(self, display_name: str) -> ContextDefaultFactory:
        return self._contexts[display_name].default_factory

    @_except_not_registered
    def get_serializer(self, display_name: str) -> ContextSerializer:
        return self._contexts[display_name].serializer

    @_except_not_registered
    def get_deserializer(self, display_name: str) -> ContextDeserializer:
        return self._contexts[display_name].deserializer

    def unregister(self, display_name: str) -> None:
        """Removes the ctx from the registry, does nothing if not in there."""
        if display_name in self._contexts:
            del self._contexts[display_name]

    def list_entries(self) -> Iterable[ContextRegistryEntry]:
        yield from self._contexts.values()

    def __repr__(self):
        return f'<{self.__class__.__name__} ({len(self._contexts)} contexts)>'


class ContextManager(Collection):
    """Interface to the collections of contexts on a conversation.

    Contexts are server-side state that have to be managed from the client,
    i.e. this agent. This class represents the collection of contexts of a
    Dialogflow conversation and presents a set of methods to manage them in
    a predictable way.

    This object is what is returned by
    :attr:`.V2DialogflowConversation.contexts`.

    Args:
        contexts: An iterable of incoming contexts.
        session: This requests session id. Required to build full context
            names.
        context_registry: A reference to the context_registry of an agent.
    """

    def __init__(
        self,
        contexts: Optional[Iterable[Context]] = None,
        session: Optional[str] = '',
        context_registry: Optional[ContextRegistry] = None,
    ):
        if contexts is None:
            contexts = []
        self._active_contexts = {ctx.display_name: ctx for ctx in contexts}
        self._marked_for_deletion = {}
        self._context_registry = context_registry or ContextRegistry()
        self.session = session

    def get(self, display_name: str) -> Context:
        """Get a context by its display name.

        A shorter way to do this is via attribute access:

        .. code-block:: python

            # These two are equivalent:
            conv.contexts.get('foo_context')
            conv.contexts.foo_context

        Returns:
            The complete context object, if present.

        Raises:
            KeyError: When the context is not present.
        """
        return self._active_contexts[display_name]

    def set(
        self,
        display_name_or_ctx_instance: Union[str, Context],
        lifespan_count: Optional[int] = None,
        **parameters,
    ) -> None:
        """Set a context.

        Args:
            display_name_or_ctx_instance: Either the display name of the new
                context (will be concatenated with the session id) or a
                complete :class:`.Context` instance.
            lifespan_count: The lifespan of the new context. None defaults to
                Dialogflows default, currently 5.
            parameters: Params for this context, i.e. the context data.

        Returns:
            None

        Raises:
            ValueError: If either a context instance was given and the a
                separate lifespan or params set or the display name is invalid.
        """
        if isinstance(display_name_or_ctx_instance, Context):
            if lifespan_count is not None or parameters:
                raise ValueError(
                    'Can\'t specify lifespan_count and parameters separately '
                    'when setting a Context instance, set them on the '
                    'instance instead.'
                )
            name = display_name_or_ctx_instance.display_name
            ctx = display_name_or_ctx_instance
        else:
            name = display_name_or_ctx_instance
            ctx = Context(name, lifespan_count, parameters)
        if not _is_valid_ctx_display_name(name):
            raise ValueError(
                f'Invalid context name, must match this pattern: '
                f'{VALID_DISPLAY_NAME_PATTERN}'
            )
        if not _is_full_ctx_name(ctx.name):
            ctx.name = make_full_ctx_name(self.session, ctx.name)
        self._active_contexts[name] = ctx

    def delete(
        self, display_name: str, keep_in_registry: Optional[bool] = True
    ) -> None:
        """Delete a context.

        Deleting a context means settings its lifespan to zero, which will
        cause Dialogflow to delete them server side. This is why deleted
        contexts will still be included in the next webhook response (with
        lifespan 0).

        This too works via attribute access:

        .. code-block:: python

            # These two are equivalent:
            conv.contexts.delete('foo_context')
            del conv.contexts.foo_context

        Args:
            display_name: The display_name of the context to delete.
            keep_in_registry: Keep the context in the agents context registry,
                should it have been in there.

        Returns:
            None

        Raises:
            KeyError: If a context with this name doesn't exist.
        """
        ctx = self._active_contexts[display_name]
        ctx.lifespan_count = 0
        self._marked_for_deletion[display_name] = ctx
        del self._active_contexts[display_name]
        if not keep_in_registry:
            self._context_registry.unregister(display_name)

    def has(self, display_name: str) -> bool:
        """Check whether a context is present.

        This does not include deleted contexts, even though they will still be
        included in the next webhook response (to set their lifespan to 0).

        A shorter version of this is the ``in`` operator:

        .. code-block:: python

            # These two are equivalent:
            conv.contexts.has('foo_context')
            'foo_context' in conv.contexts

        Returns:
            True if it is present, false if not.
        """
        return display_name in self._active_contexts

    def __contains__(self, display_name: str) -> bool:
        return self.has(display_name)

    def __iter__(self) -> Iterator[Context]:
        return iter(self._active_contexts.values())

    def __len__(self) -> int:
        return len(self._active_contexts)

    def __getattr__(self, attr_or_display_name):
        try:
            return self.get(attr_or_display_name)
        except KeyError:
            raise AttributeError(
                f"'{self.__class__.__name__}' has neither an attribute "
                f"'{attr_or_display_name}' nor a context with that display "
                f"name."
            )

    def __delattr__(self, display_name):
        try:
            return self.delete(display_name)
        except KeyError:
            raise AttributeError(
                f"'{self.__class__.__name__}' has no context with "
                f"display_name '{display_name}'."
            )

    def as_list(self) -> List[Context]:
        """Render the current collection of contexts as a list.

        This will we called automatically to add the contexts to the
        WebhookResponse. Contexts should not be modified after this has been
        called.

        Returns:
            A list of context objects.
        """
        contexts = list(self._active_contexts.values())
        marked_for_deletion = list(self._marked_for_deletion.values())
        return contexts + marked_for_deletion


# Source for the pattern is the Dialogflow Discovery File.
VALID_DISPLAY_NAME_PATTERN = re.compile(r'[a-zA-Z0-9_\-%]+')
# This does not validate the display name as this would be trying to do two
# things at once.
FULL_CTX_NAME_PATTERN = re.compile(
    r'projects/\w+/agent/sessions/\w+/contexts/.+'
)


def _is_valid_ctx_display_name(
    name: str, pattern: Optional[Pattern] = None
) -> bool:
    if pattern is None:
        pattern = VALID_DISPLAY_NAME_PATTERN
    return bool(pattern.fullmatch(name))


def _is_full_ctx_name(name: str, pattern: Optional[Pattern] = None) -> bool:
    if pattern is None:
        pattern = FULL_CTX_NAME_PATTERN
    return bool(pattern.fullmatch(name))


def make_full_ctx_name(session: str, display_name: str) -> str:
    return session + '/contexts/' + display_name


class _SessionContextSchema(JSONTypeSchema):
    """Schema for the session context."""

    fallback_level = Int()


@dataclass
class SessionContext(JSONType, schema=_SessionContextSchema):
    """Private context used to implement backend features."""

    fallback_level: int = 0

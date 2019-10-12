# -*- coding: utf-8 -*-
"""
    flask_dialogflow.integrations.actions_on_google
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The integration conversation class for the Actions-on-Google integration.

    :copyright: (c) 2018 ONSEI GmbH
    :license: Proprietary
"""
import json
from datetime import datetime, timedelta, timezone
from typing import (
    Optional,
    Sequence,
    MutableSequence,
    TypeVar,
    Callable,
    List,
    Generic,
)

from flask_dialogflow.google_apis.actions_on_google_v2 import (
    Suggestion,
    UserProfile,
    AppRequest,
    User,
    Input,
    BasicCard,
    TableCard,
    MediaResponse,
    CarouselBrowse,
    OrderUpdate,
    StructuredResponse,
    UrlTypeHint,
    LinkOutSuggestion,
    OpenUrlAction,
    Permission,
    PermissionValueSpec,
    ConfirmationValueSpec,
    ConfirmationDialogSpec,
    SignInValueSpec,
    DateTimeValueSpec,
    DateTimeDialogSpec,
    NewSurfaceValueSpec,
    DialogSpec,
    LinkValueSpec,
    SimpleSelect,
    ListSelect,
    CarouselSelect,
    CollectionSelect,
    DeliveryAddressValueSpec,
    AddressOptions,
    OrderOptions,
    PaymentOptions,
    TransactionRequirementsCheckSpec,
    ProposedOrder,
    PresentationOptions,
    TransactionDecisionValueSpec,
    Item,
    SimpleResponse,
    OptionValueSpec,
    RichResponse,
    ImageDisplayOptions,
    Image,
    PackageEntitlement,
)
from flask_dialogflow.integrations import AbstractIntegrationConversation
from flask_dialogflow.json import JSON


T = TypeVar('T')
UserStorageDefaultFactory = Callable[[], T]
UserStorageDeserializer = Callable[[str], T]
UserStorageSerializer = Callable[[T], str]


class UserFacade(Generic[T]):
    """A facade to the user object.

    This wraps the :class:`.User` object and adds some additional features,
    most notably the handling of the user storage de-/serialization. This class
    is what is returned by
    :attr:`.V2ActionsOnGoogleDialogflowConversation.user`.
    """

    def __init__(
        self,
        user: Optional[User] = None,
        user_storage_default_factory: UserStorageDefaultFactory = dict,
        user_storage_deserializer: Optional[
            UserStorageDeserializer
        ] = json.loads,
        user_storage_serializer: Optional[UserStorageSerializer] = json.dumps,
    ) -> None:
        """Initialize this facade from a normal User object.

        Args:
            user: The User object to wrap. Its attributes are accessible on
                this facade.
            user_storage_default_factory: Default factory to initialize the
                user storage when it is empty.
            user_storage_deserializer: Function to deserialize the user storage
                with.
            user_storage_serializer: Function to serialize the user storage
                with.
        """
        self._user = user or User()
        self._user_storage_default_factory = user_storage_default_factory
        self._deserializer = user_storage_deserializer
        self._serializer = user_storage_serializer

        if self._user.user_storage:
            self._user_storage = self._deserializer(self._user.user_storage)
        else:
            self._user_storage = user_storage_default_factory()

    @property
    def user_id(self) -> Optional[str]:
        """The :attr:`.User.user_id`."""
        return self._user.user_id

    @property
    def id_token(self) -> Optional[str]:
        """The :attr:`.User.id_token`."""
        return self._user.id_token

    @property
    def profile(self) -> Optional['UserProfile']:
        """The :class:`.UserProfile`."""
        return self._user.profile

    @property
    def access_token(self) -> Optional[str]:
        """The :attr:`.User.access_token`."""
        return self._user.access_token

    @property
    def permissions(self) -> List['Permission']:
        """The list of :class:`.Permissions`."""
        return self._user.permissions

    @property
    def locale(self) -> Optional[str]:
        """The :attr:`.User.locale`."""
        return self._user.locale

    @property
    def last_seen(self) -> datetime:
        """When this user was last seen as a datetime object."""
        return self._user.last_seen

    @property
    def last_seen_before(self) -> timedelta:
        """The amount of time since the user was last seen as a timedelta."""
        return datetime.now(timezone.utc) - self._user.last_seen

    @property
    def package_entitlements(self) -> List['PackageEntitlement']:
        """The list of :class:`.PackageEntitlements` of this user."""
        return self._user.package_entitlements

    @property
    def user_storage(self) -> T:
        """The deserialized :attr:`.User.user_storage`.

        Deleting the user_storage resets it to the default factory. To ensure
        that we don't send and empty dictionary back to Google the user_storage
        is set to None when it evaluates to False during serialization. Before
        the next request it will then again be initialized with the default
        factory, thus keeping the type consistent.
        """
        return self._user_storage

    @user_storage.deleter
    def user_storage(self) -> None:
        self._user_storage = self._user_storage_default_factory()

    def _serialize_user_storage(self) -> Optional[str]:
        """Serialize the user_storage."""
        if not self._user_storage:
            return None
        return self._serializer(self.user_storage)


class V2ActionsOnGoogleDialogflowConversation(
    Generic[T], AbstractIntegrationConversation
):
    """Conversation class for the Actions on Google integration.

    This class implements all AoG specific features. It is registered as the
    integration class for AoG by default and available via the
    :attr:`.DialogflowConversation.google` attribute. It exposes AoG specific
    request attributes and offers methods to build AoG responses. It also
    handles the de-/serialization of the AoG user storage.

    When a Dialogflow agent is only meant to be used via Actions on Google, all
    responses can simply be set on this class. It is however perfectly possible
    to use this next to another integration class to realize agents for
    multiple platforms.
    """

    def __init__(
        self,
        app_request: Optional['AppRequest'] = None,
        user_storage_default_factory: UserStorageDefaultFactory = dict,
        user_storage_deserializer: Optional[
            UserStorageDeserializer
        ] = json.loads,
        user_storage_serializer: Optional[UserStorageSerializer] = json.dumps,
        text_to_speech_as_ssml: Optional[bool] = True
    ):
        """Initialize this conversation from an :class:`.AppRequest.

        AppRequest is AoGs request class and is what the platform payload comes
        in. The user storage in its default configuration behaves like a dict,
        which means that all attributes must be serializable with json.dumps.
        It is possible to use a custom storage class in the same way as for
        :class:`.DialogflowAgent.contexts`.

        Args:
            app_request: Incoming request data.
            user_storage_default_factory: Default factory to initialize the
                user storage when it is empty.
            user_storage_deserializer: Function to deserialize the user storage
                with.
            user_storage_serializer: Function to serialize the user storage
                with.
            text_to_speech_as_ssml: Send all text responses as SSML. This is on
                by default and means that all text responses will be wrapped in
                <ssml> tags and set on the :attr:`.SimpleResponse.ssml`
                attribute. This means that the response strings can contain
                SSML directives. It is the users responsibility to properly
                    escape them.
        """
        self._app_request = app_request or AppRequest(user=User())
        self._expect_user_response = None
        self._rich_response = RichResponse()
        self._system_intent = None
        self._user = UserFacade(
            self._app_request.user,
            user_storage_deserializer=user_storage_deserializer,
            user_storage_serializer=user_storage_serializer,
            user_storage_default_factory=user_storage_default_factory,
        )
        self.text_to_speech_as_ssml = text_to_speech_as_ssml

    @classmethod
    def from_webhook_request_payload(
        cls, payload: Optional[JSON] = None, **kwargs
    ) -> 'V2ActionsOnGoogleDialogflowConversation':
        """Initialize this conversation from a webhook request payload.

        Parses the payload to an :class:`.AppRequest` and initializes the conv.

        Args:
            payload: The :attr:`.OriginalDetectIntentRequest.payload` of a
                webhook request from AoG.
            **kwargs: Kwargs that init takes.
        """
        if payload:
            app_request = AppRequest.from_json(payload)
        else:
            app_request = AppRequest()
        return cls(app_request, **kwargs)

    @property
    def app_request(self) -> AppRequest:
        """The underlying :class:`.AppRequest`.

        Should usually not be needed, but might be useful to access the raw
        request data.
        """
        return self._app_request

    @property
    def user(self) -> 'UserFacade[T]':
        """The :class:`.User` of this AppRequest.

        This returns a special :class:`.UserFacade` object, which wraps the
        original User object and adds some more features.
        """
        return self._user

    @property
    def inputs(self) -> Sequence['Input']:
        """The sequence of :class:`.Inputs` of this request."""
        return self.app_request.inputs

    @property
    def surface(self) -> Sequence[str]:
        """The surface :class:`.Capabilities` as a sequence of strings.

        I.e. something like ``('actions.capability.SCREEN_OUTPUT',
        'actions.capability.AUDIO_OUTPUT')``. See `Surface capabilities`_ for
        more details.

        .. _Surface capabilities: https://developers.google.com/actions/assistant/surface-capabilities
        """
        if self.app_request.surface is None:
            return tuple()
        return tuple(cap.name for cap in self.app_request.surface.capabilities)

    @property
    def has_screen(self) -> bool:
        """Whether this request has the SCREEN_OUTPUT capability."""
        return 'actions.capability.SCREEN_OUTPUT' in self.surface

    @property
    def available_surfaces(self) -> Sequence[str]:
        """The available surface capabilities that can be handed off to.

        Returns a sequence of the capabilities name, just like
        :attr:`.surface`.
        """
        surfaces = self.app_request.available_surfaces
        if surfaces is None:
            return tuple()
        return tuple(cap.name for sf in surfaces for cap in sf.capabilities)

    @property
    def is_in_sandbox(self) -> Optional[bool]:
        """Whether this is a sanbox request."""
        return self.app_request.is_in_sandbox

    # ----- RESPONSE ---------------------------------------------------------

    def ask(self, *texts: str) -> None:
        """Ask the user something.

        This implies that the session is kept open. Multiple texts will be
        concatenated wit a space and end up in one speech bubble. Call this
        method multiple times to produce multiple bubbles, but beware that
        there is currently a limit of two bubbles.

        Args:
            texts: The texts to speak.
        """
        self._add_text_response(*texts, ssml=self.text_to_speech_as_ssml)
        self._expect_user_response = True

    def ask_ssml(self, *texts: str) -> None:
        """Explicitly ask something in SSML.

        This can be used to force SSML when the ssml-by-default option is
        turned off. Wraps the text in <speak> tags automatically.

        Args:
            texts: The texts to speak.
        """
        self._add_text_response(*texts, ssml=True)
        self._expect_user_response = True

    def tell(self, *texts: str) -> None:
        """Tell the user something.

        This implies that the session will be closed. Other behavior is the
        same as for :meth:`.ask`.

        Args:
            texts: The texts to speak.
        """
        self._add_text_response(*texts, ssml=self.text_to_speech_as_ssml)
        self._expect_user_response = False

    def tell_ssml(self, *texts: str) -> None:
        """Explicitly tell something in SSML.

        Equivalent of :meth:`.ask_ssml`, session will be closed.

        Args:
            texts: The texts to speak.
        """
        self._add_text_response(*texts, ssml=True)
        self._expect_user_response = False

    def display(self, *texts: str):
        """Set a separate display text on the last text response.

        The spoken and the displayed text should normally not diverge too much,
        but there might be cases were the spoken text is very colloquical and
        a separate display text is desired. This adds a separate display text
        to the last text response. Can be used after ask, ask_ssml, tell and
        tell_ssml.

        Args:
            texts: The texts to display.

        Raises:
            ValueError: If no text response has been set yet.
        """
        text = ' '.join(texts)
        for item in reversed(self._rich_response.items):
            if item.simple_response is not None:
                item.simple_response.display_text = text
                break
        else:
            raise ValueError(
                'No SimpleResponse found where this display_text could be '
                'set. You should call ask() or tell() first to set a '
                'text_to_speech (and implicitly create a SimpleResponse), '
                'then call display() to set a different display_text on that '
                'SimpleResponse.'
            )

    def suggest(self, *suggestions: str) -> None:
        """Display suggestion chips.

        Can be called once with multiple suggestions or multiple times in a
        row or both. Suggestions are kept in the order they are set, but are
        not de-duplicated.

        Args:
            suggestions: The suggestions to display.
        """
        self._rich_response.suggestions.extend(
            Suggestion(title=sug) for sug in suggestions
        )

    def show_basic_card(self, basic_card: BasicCard) -> None:
        """Show a :class:`.BasicCard`.

        Args:
            basic_card: The card to show.
        """
        self._add_rich_response_item(basic_card=basic_card)

    def show_image(
        self,
        url: str,
        accessibility_text: str,
        height: Optional[float] = None,
        width: Optional[float] = None,
        image_display_options: Optional[ImageDisplayOptions] = None,
    ):
        """Show an image.

        A plain image can be show as a basic card without title or description.
        This is therefore simply a wrapper around :meth:`.show_basic_card`.

        Args:
            url: The images URL. Must be HTTPS.
            accessibility_text: The images accessibilitiy text.
            height: The images height.
            width: The images width.
            image_display_options: More detailes :class:`.ImageDisplayOptions`.
        """
        self.show_basic_card(
            BasicCard(
                image=Image(url, accessibility_text, height, width),
                image_display_options=image_display_options
            )
        )

    def show_table_card(self, table_card: TableCard) -> None:
        """Show a :class:`.TableCard`.

        Args:
            table_card: The card to show.
        """
        self._add_rich_response_item(table_card=table_card)

    def play_media_response(self, media_response: MediaResponse) -> None:
        """Play a :class:`.MediaResponse`.

        Args:
            media_response: The media response to play.
        """
        self._add_rich_response_item(media_response=media_response)

    def show_carousel_browse(
        self, carousel_browse: CarouselBrowse
    ) -> None:
        """Show a :class:`.CarouselBrowse`.

        Args:
            carousel_browse: The carousel to show.
        """
        self._add_rich_response_item(carousel_browse=carousel_browse)

    def show_order_update(self, order_update: OrderUpdate) -> None:
        """Show an :class:`.OrderUpdate`.

        Args:
            order_update: The order update to show.
        """
        self._add_rich_response_item(
            structured_response=StructuredResponse(order_update=order_update)
        )

    def suggest_link_out(
        self,
        destination_name: str,
        url: str,
        url_type_hint: Optional['UrlTypeHint'] = None,
    ) -> None:
        """Suggest a (web or Android app) link.

        Args:
            destination_name: The title to show on the button.
            url: The URL.
            url_type_hint: Optional hint for the URL, to be used when it is an
                Android link.
        """
        self._rich_response.link_out_suggestion = LinkOutSuggestion(
            destination_name=destination_name,
            open_url_action=OpenUrlAction(
                url=url, url_type_hint=url_type_hint
            ),
        )

    def ask_for_permission(self, reason: str, *permissions: Permission):
        """Ask for permissions.

        Args:
            reason: The reason for the request.
            permissions: The permissions to request.
        """
        value_spec = PermissionValueSpec(
            opt_context=reason, permissions=list(permissions)
        )
        self._set_system_intent('actions.intent.PERMISSION', value_spec)

    def ask_for_confirmation(self, request_confirmation_text: str) -> None:
        """Ask for a confirmation.

        Args:
            request_confirmation_text: The text to confirm.
        """
        value_spec = ConfirmationValueSpec(
            dialog_spec=ConfirmationDialogSpec(
                request_confirmation_text=request_confirmation_text
            )
        )
        self._set_system_intent('actions.intent.CONFIRMATION', value_spec)

    def ask_for_sign_in(self, reason: str) -> None:
        """Ask for sign in to link an OAuth account.

        Args:
            reason: The reason for the request.
        """
        value_spec = SignInValueSpec(opt_context=reason)
        self._set_system_intent('actions.intent.SIGN_IN', value_spec)

    def ask_for_datetime(self, request_text: str) -> None:
        """ASk for a datetime.

        Args:
            request_text: The request text.
        """
        self._ask_for_datetime(request_datetime_text=request_text)

    def ask_for_date(self, request_text: str) -> None:
        """ASk for a date.

        Args:
            request_text: The request text.
        """
        self._ask_for_datetime(request_date_text=request_text)

    def ask_for_time(self, request_text: str) -> None:
        """ASk for a time.

        Args:
            request_text: The request text.
        """
        self._ask_for_datetime(request_time_text=request_text)

    def _ask_for_datetime(self, **request_text_param_and_val) -> None:
        value_spec = DateTimeValueSpec(
            dialog_spec=DateTimeDialogSpec(**request_text_param_and_val)
        )
        self._set_system_intent('actions.intent.DATETIME', value_spec)

    def ask_for_screen_surface(
        self, context: str, notification_title: str
    ) -> None:
        """Ask to hand the conversation over to a screen surface.

        This wraps :meth:`.ask_for_new_surface` for screen surfaces.

        Args:
            context: The context that will be picked up on the new surface.
            notification_title: The title of the notification on the new
                device.
        """
        self.ask_for_new_surface(
            capabilities=['actions.capabilities.SCREEN'],
            context=context,
            notification_title=notification_title
        )

    def ask_for_new_surface(
        self,
        capabilities: MutableSequence[str],
        context: str,
        notification_title: str,
    ):
        """Ask to hand the conversation over to a specific surface.

        Use :meth:`.ask_for_screen_surface` if you want to hand off to a
        screen.

        Args:
            capabilities: Capabilities that the new surface must have.
            context: The context that will be picked up on the new surface.
            notification_title: The title of the notification on the new
                device.
        """
        value_spec = NewSurfaceValueSpec(
            capabilities=list(capabilities),
            context=context,
            notification_title=notification_title,
        )
        self._set_system_intent('actions.intent.NEW_SURFACE', value_spec)

    def ask_for_link(
        self,
        open_url_action: OpenUrlAction,
        dialog_spec: Optional[DialogSpec] = None
    ) -> None:
        """Ask for a link.

        Unclear what this is for.

        Args:
            open_url_action: The URL action to perform.
            dialog_spec: The dialog spec to use (unspecified).
        """
        value_spec = LinkValueSpec(
            open_url_action=open_url_action,
            dialog_spec=dialog_spec or DialogSpec()
        )
        self._set_system_intent('actions.intent.LINK', value_spec)

    def ask_for_simple_selection(self, simple_select: SimpleSelect):
        """Ask for a simple selection.

        Args:
            simple_select: The selection options.
        """
        self._set_option_system_intent(simple_select=simple_select)

    def ask_for_list_selection(self, list_select: ListSelect):
        """Ask for a selection from a list.

        Args:
            list_select: The list with the selection options.
        """
        self._set_option_system_intent(list_select=list_select)

    def ask_for_carousel_selection(self, carousel_select: CarouselSelect):
        """Ask for a selection from a carousel.

        Args:
            carousel_select: The carousel with the selection options.
        """
        self._set_option_system_intent(carousel_select=carousel_select)

    def ask_for_collection_selection(
        self, collection_select: CollectionSelect
    ) -> None:
        """Ask for a selection from a collection.

        Args:
            collection_select: The collection with the selection options.
        """
        self._set_option_system_intent(collection_select=collection_select)

    def ask_for_delivery_address(self, reason: str) -> None:
        """Ask for a delivery address.

        Args:
            reason: The reason for this request.
        """
        value_spec = DeliveryAddressValueSpec(
            address_options=AddressOptions(reason=reason)
        )
        self._set_system_intent('actions.intent.DELIVERY_ADDRESS', value_spec)

    def ask_for_transaction_requirements_check(
        self, order_options: OrderOptions, payment_options: PaymentOptions
    ) -> None:
        """Ask for the transactions requirements check.

        Args:
            order_options: The order options to check.
            payment_options: The payment options to check.
        """
        value_spec = TransactionRequirementsCheckSpec(
            order_options=order_options, payment_options=payment_options
        )
        self._set_system_intent(
            'actions.intent.TRANSACTION_REQUIREMENTS_CHECK', value_spec
        )

    def ask_for_transaction_decision(
        self,
        proposed_order: ProposedOrder,
        order_options: OrderOptions,
        payment_options: PaymentOptions,
        presentation_options: PresentationOptions,
    ) -> None:
        """Ask for a transaction decision.

        Args:
            proposed_order: The order to propose.
            order_options: The order options to propose.
            payment_options: The payment options to propose.
            presentation_options: The presentation options to propose.
        """
        value_spec = TransactionDecisionValueSpec(
            proposed_order=proposed_order,
            order_options=order_options,
            payment_options=payment_options,
            presentation_options=presentation_options,
        )
        self._set_system_intent(
            'actions.intent.TRANSACTION_DECISION', value_spec
        )

    def _add_text_response(
        self, *texts: str, ssml: Optional[bool] = None
    ) -> None:
        text = ' '.join(texts)
        if ssml:
            sr = SimpleResponse(ssml=ssmlify(text))
        else:
            sr = SimpleResponse(text_to_speech=text)
        self._add_rich_response_item(simple_response=sr)

    def _add_rich_response_item(self, **name_and_item):
        self._rich_response.items.append(Item(**name_and_item))

    def _set_system_intent(self, intent: str, value_spec):
        value_spec_namespace = 'type.googleapis.com/google.actions.v2.'
        value_spec_type = value_spec.__class__.__name__
        self._system_intent = {
            'intent': intent,
            'data': {
                '@type': value_spec_namespace + value_spec_type,
                **value_spec.to_json(),
            },
        }

    def _set_option_system_intent(self, **name_and_value_spec):
        value_spec = OptionValueSpec(**name_and_value_spec)
        self._set_system_intent('actions.intent.OPTION', value_spec=value_spec)

    def to_webhook_response_payload(self) -> JSON:
        """Render this conversation to the webhook response payload.

        The response payload is not a :class:`.AppResponse`, but a custom,
        Dialogflow-specific format.

        Returns:
            A dict with the necessary response data.
        """
        response = dict()

        if self._user._serialize_user_storage() is not None:
            response['userStorage'] = self._user._serialize_user_storage()
        if self._expect_user_response is not None:
            response['expectUserResponse'] = self._expect_user_response
        if self._rich_response.to_json()is not None:
            response['richResponse'] = self._rich_response.to_json()
        if self._system_intent is not None:
            response['systemIntent'] = self._system_intent
        return response


def ssmlify(text: str) -> str:
    return f'<speak>{text}</speak>'

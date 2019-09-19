# -*- coding: utf-8 -*-
"""
    flask_dialogflow.conversation
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    The core Dialogflow Conversation classes.

    :copyright: (c) 2018 ONSEI GmbH
    :license: Proprietary
"""
from collections import defaultdict
from typing import Optional, Mapping, Any, DefaultDict, List

from flask_dialogflow.context import ContextManager, SessionContext, Context
from flask_dialogflow.google_apis import import_dialogflow_api
from flask_dialogflow.integrations import (
    AbstractIntegrationConversation, GenericIntegrationConversation
)
from flask_dialogflow.integrations.actions_on_google import (
    V2ActionsOnGoogleDialogflowConversation
)


class V2DialogflowConversation:
    """The core Dialogflow Conversation object.

    This object is the heart of this library. It represents a single turn in a
    Dialogflow conversation and is the interface to both the incomint request
    data as well as to the response construction methods. This object is
    instantiated by ONSEI_Google automatically and then passed to the handler
    function matched to this request. The handler function will usually
    inspect the request data in more detail, perform some business logic,
    maybe update the server-side state (contexts, user storage) and then build
    a response before returning the conversation object back to the library.
    It will then be rendered into a webhook response and serialized to JSON
    behind the scenes.

    This class is specific to v2 of the Dialogfow API. There is a corresponding
    :class:`.V2beta1DialogflowConversation` for v2beta1. These two are
    currently the only supported Dialogflow versions. (v2beta1 appears, despite
    its name, to be a superset of v2, there is thus no harm in always using it,
    which is why it is the default conversation class.)

    The DialogflowConversation does also carry integration-specific
    conversation classes to implement features specific to individual
    integrations. The most important of them is
    :class:`.V2ActionOnGoogleDialogflowConversation` for the Actions on Google
    integration. It is registered on the agent by default and always available
    under the :attr:`.google` attribute. See `Integrations`_ for details.
    
    Note that the response methods on this class refer to the generic
    Dialogflow responses. Some integrations, particularly Actions on Google,
    have their own set of much more elaborate responses. The methods here
    should thus only be used when cross-platform compatibility is desired. For
    agents that are only used with Actions on Google one should always use the
    :attr:`.V2DialogflowConversation.google` methods exclusively. The other
    integration convs are currently :class:`.GenericIntegrationConversations`,
    which behave like dicts. Users can implement their own conversation classes
    and register them on the agent to support custom features.
    """

    _df = import_dialogflow_api('v2')

    def __init__(
        self,
        webhook_request: Optional[_df.WebhookRequest] = None,
        context_manager: Optional['ContextManager'] = None,
        integration_convs: Optional[
            Mapping[str, AbstractIntegrationConversation]
        ] = None,
    ) -> None:
        """Initialize a conversation.

        This is not supposed to be done by the user, several steps usually
        preceed the initialization to set the conversation up correctly.

        Args:
            webhook_request: The :class:`.WebhookRequest` that this
                conversation represents.
            context_manager: The :class:`.ContextManager` that handles the
                contexts.
            integration_convs: The mapping of integration conversations.
        """
        if webhook_request is None:
            odir = self._df.OriginalDetectIntentRequest()
            webhook_request = self._df.WebhookRequest(
                query_result=self._df.QueryResult(intent=self._df.Intent()),
                original_detect_intent_request=odir,
            )
        self._webhook_request = webhook_request
        self._contexts = context_manager or ContextManager(
            contexts=[
                Context('_session_context', parameters=SessionContext())
            ]
        )
        self._integration_convs: DefaultDict[
            str, AbstractIntegrationConversation
        ] = defaultdict(GenericIntegrationConversation)
        if integration_convs:
            self._integration_convs.update(integration_convs)

        self._session_ctx = self.contexts.get('_session_context').parameters
        self._webhook_response = self._df.WebhookResponse()

        if self.webhook_request.query_result.intent.is_fallback:
            self._session_ctx.fallback_level += 1
        else:
            self._session_ctx.fallback_level = 0

    @property
    def webhook_request(self) -> _df.WebhookRequest:
        """The :class:`.WebhookRequest` that this conversation represents.

        It is usually not necessary and not recommended to interact with this
        directly, it is offered as a fallback option to give access to the raw
        request data. Modyfing this is highly discouraged and may lead to
        unexpected results.
        """
        return self._webhook_request

    @property
    def session(self) -> Optional[str]:
        """This requests session id."""
        return self.webhook_request.session

    @property
    def response_id(self) -> Optional[str]:
        """This requests response id."""
        return self.webhook_request.response_id

    # ------ QUERY RESULT ----------------------------------------------------
    # QueryResult attrs that are already filled when calling the webhook

    @property
    def query_text(self) -> Optional[str]:
        """This requests query text (i.e. the text spoken by the user)."""
        return self.webhook_request.query_result.query_text

    @property
    def language_code(self) -> Optional[str]:
        """This requests language code."""
        return self.webhook_request.query_result.language_code

    @property
    def intent(self) -> str:
        """This requests intent (display name)."""
        return self.webhook_request.query_result.intent.display_name

    @property
    def action(self) -> Optional[str]:
        """This requests action."""
        return self.webhook_request.query_result.action

    @property
    def contexts(self) -> 'ContextManager':
        """This requests incoming contexts.

        This returns a special :class:`.ContextManager` object that provides a
        simple API to manage the conversations context state. See its
        documentation for details.
        """
        return self._contexts

    @property
    def parameters(self) -> Mapping[str, Any]:
        """This requests parameters."""
        return self.webhook_request.query_result.parameters

    @property
    def all_required_params_present(self) -> Optional[bool]:
        """Whether all required parameters for this intent are present."""
        return self.webhook_request.query_result.all_required_params_present

    @property
    def fallback_level(self) -> int:
        """This requests fallback level.

        Default is 0, the first fallback intent gets level 1. If this is
        immediately followed by another fallback intent (i.e. the user was
        still not understood) the level is 2 and so on. The next non-fallback
        intent resets the level to 0.

        It is good design practice to handle the levels differently, see the
        `Design guidelines`_ for details.

        .. _Design guidelines: https://designguidelines.withgoogle.com/conversation/conversational-components/errors.html#errors-no-match
        """
        return self._session_ctx.fallback_level

    @property
    def diagnostic_info(self) -> Mapping[str, Any]:
        """This requests diagnostic info."""
        return self.webhook_request.query_result.diagnostic_info

    @property
    def intent_detection_confidence(self) -> Optional[float]:
        """This requests intent detection confidence."""
        return self.webhook_request.query_result.intent_detection_confidence

    @property
    def speech_recognition_confidence(self) -> Optional[float]:
        """This requests speech recognition confidence."""
        return self.webhook_request.query_result.speech_recognition_confidence

    @property
    def sentiment(self) -> Optional[_df.Sentiment]:
        """This requests sentiment."""
        res = self.webhook_request.query_result.sentiment_analysis_result
        return res.query_text_sentiment if res else None

    # ----- ORIGINAL DETECT INTENT REQUEST -----------------------------------

    @property
    def source(self) -> str:
        """This requests source (i.e. the integration platform)."""
        return self.webhook_request.original_detect_intent_request.source

    @property
    def version(self) -> Optional[str]:
        """This requests source version (usually only set for AoG)."""
        return self.webhook_request.original_detect_intent_request.version

    @property
    def payload(self) -> Mapping[str, Any]:
        """This requests integration payload.
        
        This platform-specific payload will be used to initialize the
        integration convs. Users should typically access these directly (via
        :attr:`.V2DialogflowConversation.google` etc.), the raw data is only
        included as a fallback option. Modifying it is highly discouraged.
        """
        return self.webhook_request.original_detect_intent_request.payload

    @property
    def integrations(
        self
    ) -> DefaultDict[str, 'AbstractIntegrationConversation']:
        """The dictionary of integration convs.
        
        The default integrations (AoG, Facebook, Slack ectc) have their own
        properties and do not need to access their convs via this dictionary,
        but custom integration platforms will. It is a default dict that
        returns a :class:`.GenericIntegrationConversation` by default, which
        means that new platforms can be used without additional setup.

        This class implements a __getattr__ method that looks up attributes in
        the integrations mapping. These two lines are therefore equivalent:

        .. code-block:: python

            conv.integrations['foobar']
            conv.foobar  # Same thing
        """
        return self._integration_convs

    # ----- RESPONSE ---------------------------------------------------------

    def ask(self, *texts: str) -> None:
        """Ask the user something.
        
        The v2 has no endInteraction field, which probably implies that the
        session can not be closed manually. v2beta1 has a separate tell()
        function that does end the interaction.
        
        Args:
            texts: The texts to speak.
        """
        self._add_fulfillment_message(text=self._df.Text(list(texts)))

    def show_quick_replies(
        self, *quick_replies: str, title: Optional[str] = None
    ) -> None:
        """Show quick replies.
        
        Args:
            quick_replies: The replies to suggest.
            title: The title of the replies collection.
        """
        self._add_fulfillment_message(
            quick_replies=self._df.QuickReplies(
                title=title, quick_replies=list(quick_replies)
            )
        )

    def show_card(self, card: _df.Card) -> None:
        """Show a card.
        
        Args:
            card: The card to show.
        """
        self._add_fulfillment_message(card=card)

    def show_image(self, image: _df.Image) -> None:
        """Show an image.
        
        Args:
            image: The image to show.
        """
        self._add_fulfillment_message(image=image)

    def _add_fulfillment_message(self, **name_and_message):
        self._webhook_response.fulfillment_messages.append(
            self._df.Message(**name_and_message)
        )

    # ----- DEFAULT INTEGRATIONS ---------------------------------------------

    @property
    def google(self) -> V2ActionsOnGoogleDialogflowConversation:
        """The Actions on Google conversation object.

        This objects abstracts all AoG-specific features. When AoG is the only
        integration where an agent is used it is perfectly fine to use this
        exclusively.
        """
        return self._integration_convs['google']

    @property
    def facebook(self) -> GenericIntegrationConversation:
        """The Facbook integration conv."""
        return self._integration_convs['facebook']

    @property
    def slack(self) -> GenericIntegrationConversation:
        """The Slack integration conv."""
        return self._integration_convs['slack']

    @property
    def telegram(self) -> GenericIntegrationConversation:
        """The Telegram integration conv."""
        return self._integration_convs['telegram']

    @property
    def kik(self) -> GenericIntegrationConversation:
        """The Kik integration conv."""
        return self._integration_convs['kik']

    @property
    def skype(self) -> GenericIntegrationConversation:
        """The Skype integration conv."""
        return self._integration_convs['skype']

    @property
    def twilio(self) -> GenericIntegrationConversation:
        """The Twilio integration conv."""
        return self._integration_convs['twilio']

    @property
    def twilio_ip(self) -> GenericIntegrationConversation:
        """The TwilioIP integration conv."""
        return self._integration_convs['twilio-ip']

    @property
    def line(self) -> GenericIntegrationConversation:
        """The Line integration conv."""
        return self._integration_convs['line']

    @property
    def spark(self) -> GenericIntegrationConversation:
        """The Spark integration conv."""
        return self._integration_convs['spark']

    @property
    def tropo(self) -> GenericIntegrationConversation:
        """The Tropo integration conv."""
        return self._integration_convs['tropo']

    @property
    def viber(self) -> GenericIntegrationConversation:
        """The Viber integration conv."""
        return self._integration_convs['viber']

    def __getattr__(self, item) -> AbstractIntegrationConversation:
        return self._integration_convs[item]

    def to_webhook_response(self) -> _df.WebhookResponse:
        """Render the :class:`.WebhookResponse` for this conversation.

        This is the last step during conversation handling and is usually done
        automatically by the framework. Modifying the conversation after the
        response has been rendered may lead to unexpected results.

        Returns:
            A complete Dialogflow WebhookResponse that can be serialized to
            JSON.
        """
        self._webhook_response.output_contexts = self._contexts.as_list()
        for integration, integration_conv in self._integration_convs.items():
            self._webhook_response.payload[integration] = \
                integration_conv.to_webhook_response_payload()
        return self._webhook_response


class V2beta1DialogflowConversation(V2DialogflowConversation):
    """The v2beta1 version of the DialogflowConversation.

    This has a few additional features, but is otherwise completely identical
    to the :class:`.V2DialogflowConversation`.
    """

    _df = import_dialogflow_api('v2beta1')

    def tell(self, *texts: str) -> None:
        """Like :meth:`ask<V2beta1DialogflowConversation.ask>`, but the
        interaction is ended after it."""
        self.ask(*texts)
        self._webhook_response.end_interaction = True

    @property
    def alternative_query_results(self) -> List[_df.QueryResult]:
        """Alternative :class:`.QueryResults` from knowledge connectors."""
        return self.webhook_request.alternative_query_results

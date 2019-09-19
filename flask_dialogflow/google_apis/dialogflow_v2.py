# -*- coding: utf-8 -*-
"""
    dialogflow
    ~~~~~~~~~~

    :copyright: (c) 2018 ONSEI GmbH
    :license: Proprietary
"""
# pylint: disable=missing-docstring

from enum import Enum
from functools import partial
from typing import Optional, Any, Dict, List

from dataclasses import dataclass, field

from flask_dialogflow.google_apis import (
    GoogleType,
    GoogleTypeSchema,
    Str,
    Int,
    ModuleLocalNested,
    Bool,
    Float,
    ListF,
    DictF,
    EnumField,
    Raw,
)

Nested = partial(ModuleLocalNested, module_name=__name__)


class _WebhookRequestSchema(GoogleTypeSchema):
    session = Str()
    responseId = Str(attribute='response_id')
    queryResult = Nested('_QueryResultSchema', attribute='query_result')
    originalDetectIntentRequest = Nested(
        '_OriginalDetectIntentRequestSchema',
        attribute='original_detect_intent_request',
    )


@dataclass
class WebhookRequest(GoogleType, schema=_WebhookRequestSchema):
    session: Optional[str] = None
    response_id: Optional[str] = None
    query_result: Optional['QueryResult'] = None
    original_detect_intent_request: Optional[
        'OriginalDetectIntentRequest'
    ] = None


class _QueryResultSchema(GoogleTypeSchema):
    intent = Nested('_IntentSchema')
    languageCode = Str(attribute='language_code')
    allRequiredParamsPresent = Bool(attribute='all_required_params_present')
    queryText = Str(attribute='query_text')
    speechRecognitionConfidence = Float(
        attribute='speech_recognition_confidence'
    )
    action = Str()
    parameters = DictF()
    fulfillmentText = Str(attribute='fulfillment_text')
    fulfillmentMessages = ListF(
        Nested('_MessageSchema'), attribute='fulfillment_messages'
    )
    webhookSource = Str(attribute='webhook_source')
    webhookPayload = DictF(attribute='webhook_payload')
    outputContexts = ListF(
        Nested('_ContextSchema'), attribute='output_contexts'
    )
    intentDetectionConfidence = Float(attribute='intent_detection_confidence')
    diagnosticInfo = DictF(attribute='diagnostic_info')
    sentimentAnalysisResult = Nested(
        '_SentimentAnalysisResultSchema', attribute='sentiment_analysis_result'
    )


@dataclass
class QueryResult(GoogleType, schema=_QueryResultSchema):
    intent: 'Intent'
    language_code: Optional[str] = None
    all_required_params_present: Optional[bool] = None
    query_text: Optional[str] = None
    speech_recognition_confidence: Optional[float] = None
    action: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    fulfillment_text: Optional[str] = None
    fulfillment_messages: List['Message'] = field(default_factory=list)
    webhook_source: Optional[str] = None
    webhook_payload: Dict[str, Any] = field(default_factory=dict)
    output_contexts: List['Context'] = field(default_factory=list)
    intent_detection_confidence: Optional[float] = None
    diagnostic_info: Dict[str, Any] = field(default_factory=dict)
    sentiment_analysis_result: Optional['SentimentAnalysisResult'] = None


class WebhookState(Enum):
    WEBHOOK_STATE_UNSPECIFIED = 'WEBHOOK_STATE_UNSPECIFIED'
    WEBHOOK_STATE_ENABLED = 'WEBHOOK_STATE_ENABLED'
    WEBHOOK_STATE_ENABLED_FOR_SLOT_FILLING = (
        'WEBHOOK_STATE_ENABLED_FOR_SLOT_FILLING'
    )


class _IntentSchema(GoogleTypeSchema):
    name = Str()
    displayName = Str(attribute='display_name')
    isFallback = Bool(attribute='is_fallback')
    webhookState = EnumField(WebhookState, attribute='webhook_state')


@dataclass
class Intent(GoogleType, schema=_IntentSchema):
    name: Optional[str] = None
    display_name: Optional[str] = None
    is_fallback: Optional[bool] = None
    webhook_state: Optional['WebhookState'] = None


class _ContextSchema(GoogleTypeSchema):
    name = Str()
    lifespanCount = Int(attribute='lifespan_count')
    parameters = DictF(keys=Str(), values=Raw())


@dataclass
class Context(GoogleType, schema=_ContextSchema):
    name: Optional[str] = None
    lifespan_count: Optional[int] = None
    parameters: Dict[str, Any] = field(default_factory=dict)


class _SentimentAnalysisResultSchema(GoogleTypeSchema):
    queryTextSentiment = Nested(
        '_SentimentSchema', attribute='query_text_sentiment'
    )


@dataclass
class SentimentAnalysisResult(
    GoogleType, schema=_SentimentAnalysisResultSchema
):
    query_text_sentiment: 'Sentiment'


class _SentimentSchema(GoogleTypeSchema):
    score = Float()
    magnitude = Float()


@dataclass
class Sentiment(GoogleType, schema=_SentimentSchema):
    score: Optional[float] = None
    magnitude: Optional[float] = None


class Platform(Enum):
    """Dialogflow integration platforms.

    Taken from the Dialogflow Discovery Document and the integrations page of
    the Dialogflow documentation. Value taken from Dialogflow examples when
    available, with link to source.
    """
    # pylint: disable=line-too-long
    PLATFORM_UNSPECIFIED = None
    FACEBOOK = 'facebook'  # https://github.com/dialogflow/dialogflow-nodejs-client/blob/1abd5f123ed8fcd507fa600f3af2d5ed55cedc47/samples/facebook/src/app.js#L326
    SLACK = 'slack'
    TELEGRAM = 'telegram'  # https://github.com/dialogflow/dialogflow-nodejs-client/blob/1abd5f123ed8fcd507fa600f3af2d5ed55cedc47/samples/telegram/src/telegrambot.js#L53
    KIK = 'kik'
    SKYPE = 'skype'  # https://github.com/dialogflow/dialogflow-nodejs-client/blob/1abd5f123ed8fcd507fa600f3af2d5ed55cedc47/samples/skype/skypebot.js#L61
    TWILIO = 'twilio'  # https://github.com/dialogflow/dialogflow-nodejs-client/blob/1abd5f123ed8fcd507fa600f3af2d5ed55cedc47/samples/twilio/ip-messaging/src/twiliobot.js#L58
    TWILIO_IP = 'twilio-ip'  # https://github.com/dialogflow/dialogflow-nodejs-client/blob/1abd5f123ed8fcd507fa600f3af2d5ed55cedc47/samples/twilio/ip-messaging/src/twiliobot.js#L58
    LINE = 'line'  # https://github.com/dialogflow/dialogflow-nodejs-client/blob/1abd5f123ed8fcd507fa600f3af2d5ed55cedc47/samples/line/src/linebot.js#L81
    SPARK = 'spark'  # https://github.com/dialogflow/dialogflow-nodejs-client/blob/1abd5f123ed8fcd507fa600f3af2d5ed55cedc47/samples/spark/src/sparkbot.js#L54
    TROPO = 'tropo'  # https://github.com/dialogflow/dialogflow-nodejs-client/blob/1abd5f123ed8fcd507fa600f3af2d5ed55cedc47/samples/tropo/src/tropobot.js#L53
    VIBER = 'viber'
    ACTIONS_ON_GOOGLE = 'google'


class _MessageSchema(GoogleTypeSchema):
    platform = EnumField(Platform)
    text = Nested('_TextSchema')
    suggestions = Nested('_SuggestionsSchema')
    listSelect = Nested('_ListSelectSchema', attribute='list_select')
    carouselSelect = Nested(
        '_CarouselSelectSchema', attribute='carousel_select'
    )
    image = Nested('_ImageSchema')
    quickReplies = Nested('_QuickRepliesSchema', attribute='quick_replies')
    card = Nested('_CardSchema')
    basicCard = Nested('_BasicCardSchema', attribute='basic_card')
    linkOutSuggestion = Nested(
        '_LinkOutSuggestionSchema', attribute='link_out_suggestion'
    )
    simpleResponses = Nested(
        '_SimpleResponsesSchema', attribute='simple_responses'
    )
    payload = DictF(keys=Str(), values=Raw())


@dataclass
class Message(GoogleType, schema=_MessageSchema):
    platform: Optional[str] = None
    text: Optional['Text'] = None
    suggestions: Optional['Suggestions'] = None
    list_select: Optional['ListSelect'] = None
    carousel_select: Optional['CarouselSelect'] = None
    image: Optional['Image'] = None
    quick_replies: Optional['QuickReplies'] = None
    card: Optional['Card'] = None
    basic_card: Optional['BasicCard'] = None
    link_out_suggestion: Optional['LinkOutSuggestion'] = None
    simple_responses: Optional['SimpleResponses'] = None
    payload: Dict[str, Any] = field(default_factory=dict)


# ---------- DEFAULT MESSAGE OBJECTS -----------------------------------------
# https://dialogflow.com/docs/reference/message-objects#default_message_objects


class _TextSchema(GoogleTypeSchema):
    text = ListF(Str())


@dataclass
class Text(GoogleType, schema=_TextSchema):
    text: List[str] = field(default_factory=list)


# ---------- ONE-CLICK INTEGRATION MESSAGE OBJECTS ---------------------------
# https://dialogflow.com/docs/reference/message-objects#one-click_integration_message_objects


class _ImageSchema(GoogleTypeSchema):
    imageUri = Str(attribute='image_uri')
    accessibilityText = Str(attribute='accessibility_text')


@dataclass
class Image(GoogleType, schema=_ImageSchema):
    image_uri: Optional[str] = None
    accessibility_text: Optional[str] = None


class _CardSchema(GoogleTypeSchema):
    title = Str()
    buttons = ListF(Nested('_CardButtonSchema'))
    subtitle = Str()
    imageUri = Str(attribute='image_uri')


@dataclass
class Card(GoogleType, schema=_CardSchema):
    title: Optional[str] = None
    buttons: List['CardButton'] = field(default_factory=list)
    subtitle: Optional[str] = None
    image_uri: Optional[str] = None


class _CardButtonSchema(GoogleTypeSchema):
    text = Str()
    description = Str()


@dataclass
class CardButton(GoogleType, schema=_CardButtonSchema):
    text: Optional[str] = None
    description: Optional[str] = None


class _QuickRepliesSchema(GoogleTypeSchema):
    title = Str()
    quickReplies = ListF(Str(), attribute='quick_replies')


@dataclass
class QuickReplies(GoogleType, schema=_QuickRepliesSchema):
    title: Optional[str] = None
    quick_replies: List[str] = field(default_factory=list)


# ---------- AOG MESSAGE OBJECTS ---------------------------------------------
# https://dialogflow.com/docs/reference/message-objects#actions_on_google_message_objects
#
# Don't use these, use the types from the actions_on_google module instead and
# include them as WebhookResponse.payload


class _SimpleResponsesSchema(GoogleTypeSchema):
    simpleResponses = ListF(
        Nested('_SimpleResponseSchema'), attribute='simple_responses'
    )


@dataclass
class SimpleResponses(GoogleType, schema=_SimpleResponsesSchema):
    simple_responses: List['SimpleResponse'] = field(default_factory=list)


class _SimpleResponseSchema(GoogleTypeSchema):
    textToSpeech = Str(attribute='text_to_speech')
    ssml = Str()
    displayText = Str(attribute='display_text')


@dataclass
class SimpleResponse(GoogleType, schema=_SimpleResponseSchema):
    text_to_speech: Optional[str] = None
    ssml: Optional[str] = None
    display_text: Optional[str] = None


class _BasicCardSchema(GoogleTypeSchema):
    title = Str()
    subtitle = Str()
    formattedText = Str(attribute='formatted_text')
    buttons = ListF(Nested('_BasicCardButtonSchema'))
    image = Nested('_ImageSchema')


@dataclass
class BasicCard(GoogleType, schema=_BasicCardSchema):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    formatted_text: Optional[str] = None
    buttons: List['BasicCardButton'] = field(default_factory=list)
    image: Optional['Image'] = None


class _BasicCardButtonSchema(GoogleTypeSchema):
    title = Str()
    openUriAction = Nested('_OpenUriActionSchema', attribute='open_uri_action')


@dataclass
class BasicCardButton(GoogleType, schema=_BasicCardButtonSchema):
    title: Optional[str] = None
    open_uri_action: Optional['OpenUriAction'] = None


class _OpenUriActionSchema(GoogleTypeSchema):
    uri = Str()


@dataclass
class OpenUriAction(GoogleType, schema=_OpenUriActionSchema):
    uri: Optional[str] = None


class _ListSelectSchema(GoogleTypeSchema):
    items = ListF(Nested('_ListSelectItemSchema'))
    title = Str()


@dataclass
class ListSelect(GoogleType, schema=_ListSelectSchema):
    items: List['ListSelectItem'] = field(default_factory=list)
    title: Optional[str] = None


class _ListSelectItemSchema(GoogleTypeSchema):
    title = Str()
    info = Nested('_SelectItemInfoSchema')
    image = Nested('_ImageSchema')
    description = Str()


@dataclass
class ListSelectItem(GoogleType, schema=_ListSelectItemSchema):
    title: str
    info: 'SelectItemInfo'
    image: Optional['Image'] = None
    description: Optional[str] = None


class _SelectItemInfoSchema(GoogleTypeSchema):
    key = Str()
    synonyms = ListF(Str())


@dataclass
class SelectItemInfo(GoogleType, schema=_SelectItemInfoSchema):
    key: str
    synonyms: List[str] = field(default_factory=list)


class _SuggestionsSchema(GoogleTypeSchema):
    items = ListF(Nested('_SuggestionSchema'))


@dataclass
class Suggestions(GoogleType, schema=_SuggestionsSchema):
    items: List['Suggestion'] = field(default_factory=list)


class _SuggestionSchema(GoogleTypeSchema):
    title = Str()


@dataclass
class Suggestion(GoogleType, schema=_SuggestionSchema):
    title: str


class _CarouselSelectSchema(GoogleTypeSchema):
    items = ListF(Nested('_CarouselSelectItemSchema'))


@dataclass
class CarouselSelect(GoogleType, schema=_CarouselSelectSchema):
    items: List['CarouselSelectItem']


class _CarouselSelectItemSchema(GoogleTypeSchema):
    title = Str()
    info = Nested('_SelectItemInfoSchema')
    image = Nested('_ImageSchema')
    description = Str()


@dataclass
class CarouselSelectItem(GoogleType, schema=_CarouselSelectItemSchema):
    title: str
    info: 'SelectItemInfo'
    image: Optional['Image'] = None
    description: Optional[str] = None


class _LinkOutSuggestionSchema(GoogleTypeSchema):
    destinationName = Str(attribute='destination_name')
    uri = Str()


@dataclass
class LinkOutSuggestion(GoogleType, schema=_LinkOutSuggestionSchema):
    destination_name: str
    uri: str


# ---------- OTHER -----------------------------------------------------------


class _OriginalDetectIntentRequestSchema(GoogleTypeSchema):
    source = Str()
    version = Str()
    payload = DictF(keys=Str(), values=Raw())


@dataclass
class OriginalDetectIntentRequest(
    GoogleType, schema=_OriginalDetectIntentRequestSchema
):
    source: Optional[str] = None
    version: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)


class _WebhookResponseSchema(GoogleTypeSchema):
    followupEventInput = Nested(
        '_EventInputSchema', attribute='followup_event_input'
    )
    outputContexts = ListF(
        Nested('_ContextSchema'), attribute='output_contexts'
    )
    fulfillmentText = Str(attribute='fulfillment_text')
    fulfillmentMessages = ListF(
        Nested('_MessageSchema'), attribute='fulfillment_messages'
    )
    payload = DictF(keys=Str(), values=Raw())
    source = Str()


@dataclass
class WebhookResponse(GoogleType, schema=_WebhookResponseSchema):
    followup_event_input: Optional['EventInput'] = None
    output_contexts: List['Context'] = field(default_factory=list)
    fulfillment_text: Optional[str] = None
    fulfillment_messages: List['Message'] = field(default_factory=list)
    payload: Dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None


class _EventInputSchema(GoogleTypeSchema):
    languageCode = Str(attribute='language_code')
    name = Str()
    parameters = DictF(keys=Str(), values=Raw())


@dataclass
class EventInput(GoogleType, schema=_EventInputSchema):
    language_code: str
    name: str
    parameters: Dict[str, Any] = field(default_factory=dict)

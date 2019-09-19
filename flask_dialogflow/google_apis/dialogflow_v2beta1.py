# -*- coding: utf-8 -*-
"""
    dialogflow_v2beta1
    ~~~~~~

    :copyright: (c) 2018 ONSEI GmbH
    :license: Proprietary
"""
# pylint: disable=protected-access, wildcard-import, unused-wildcard-import
# pylint: disable=function-redefined, too-many-ancestors, missing-docstring
from flask_dialogflow.google_apis.dialogflow_v2 import *
from flask_dialogflow.google_apis.dialogflow_v2 import (
    _WebhookRequestSchema,
    _WebhookResponseSchema,
    _MessageSchema,
    _QueryResultSchema,
)

Nested = partial(ModuleLocalNested, module_name=__name__)


# ---------- WEBHOOK REQUEST -------------------------------------------------


class _WebhookRequestSchema(_WebhookRequestSchema):
    alternativeQueryResults = ListF(
        Nested('_QueryResultSchema'), attribute='alternative_query_results'
    )


@dataclass
class WebhookRequest(WebhookRequest, schema=_WebhookRequestSchema):
    alternative_query_results: List['QueryResult'] = field(
        default_factory=list
    )


class _MessageSchema(_MessageSchema):
    telephonyPlayAudio = Nested(
        '_TelephonyPlayAudioSchema', attribute='telephony_play_audio'
    )
    telephonySynthesizeSpeech = Nested(
        '_TelephonySynthesizeSpeechSchema',
        attribute='telephony_synthesize_speech'
    )
    telephonyTransferCall = Nested(
        '_TelephonyTransferCallSchema', attribute='telephony_transfer_call'
    )


@dataclass
class Message(Message, schema=_MessageSchema):
    telephony_play_audio: Optional['TelephonyPlayAudio'] = None
    telephony_synthesize_speech: Optional['TelephonySynthesizeSpeech'] = None
    telephony_transfer_call: Optional['TelephonyTransferCall'] = None


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
    TELEPHONY = 'telephony'
    GOOGLE_HANGOUTS = 'google_hangouts'


class _QueryResultSchema(_QueryResultSchema):
    knowledgeAnswers = Nested(
        '_KnowledgeAnswersSchema', attribute='knowledge_answers'
    )


@dataclass
class QueryResult(QueryResult, schema=_QueryResultSchema):
    knowledge_answers: List['KnowledgeAnswers'] = field(default_factory=list)


# ---------- TELEPHONY -------------------------------------------------------


class _TelephonyPlayAudioSchema(GoogleTypeSchema):
    audioUri = Str(attribute='audio_uri')


@dataclass
class TelephonyPlayAudio(GoogleType, schema=_TelephonyPlayAudioSchema):
    audio_uri: str


class _TelephonySynthesizeSpeechSchema(GoogleTypeSchema):
    text = Str()
    ssml = Str()


@dataclass
class TelephonySynthesizeSpeech(
    GoogleType, schema=_TelephonySynthesizeSpeechSchema
):
    text: Optional[str] = None
    ssml: Optional[str] = None


class _TelephonyTransferCallSchema(GoogleTypeSchema):
    phoneNumber = Str(attribute='phone_number')


@dataclass
class TelephonyTransferCall(GoogleType, schema=_TelephonyTransferCallSchema):
    phone_number: str


# ---------- KNOWLEDGE ANSWERS -----------------------------------------------


class _KnowledgeAnswersSchema(GoogleTypeSchema):
    answers = ListF(Nested('_AnswerSchema'))


@dataclass
class KnowledgeAnswers(GoogleType, schema=_KnowledgeAnswersSchema):
    answers: List['Answer'] = field(default_factory=list)


class MatchConfidenceLevel(Enum):
    MATCH_CONFIDENCE_LEVEL_UNSPECIFIED = 'MATCH_CONFIDENCE_LEVEL_UNSPECIFIED'
    HIGH = 'HIGH'
    MEDIUM = 'MEDIUM'
    LOW = 'LOW'


class _AnswerSchema(GoogleTypeSchema):
    source = Str()
    answer = Str()
    faqQuestion = Str(attribute='faq_question')
    matchConfidenceLevel = EnumField(
        MatchConfidenceLevel, attribute='match_confidence_level'
    )
    matchConfidence = Float(attribute='match_confidence')


@dataclass
class Answer(GoogleType, schema=_AnswerSchema):
    source: Optional[str] = None
    answer: Optional[str] = None
    faq_question: Optional[str] = None
    match_confidence_level: Optional['MatchConfidenceLevel'] = None
    match_confidence: Optional[float] = None


# ---------- WEBHOOK RESPONSE ------------------------------------------------


class _WebhookResponseSchema(_WebhookResponseSchema):
    endInteraction = Bool(attribute='end_interaction')


@dataclass
class WebhookResponse(WebhookResponse, schema=_WebhookResponseSchema):
    end_interaction: Optional[bool] = None

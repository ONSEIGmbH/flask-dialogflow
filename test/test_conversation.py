# -*- coding: utf-8 -*-
"""
    test_conversation
    ~~~~~~~

    :copyright: (c) 2018 ONSEI GmbH
    :license: Proprietary
"""
import pytest

from flask_dialogflow.agent import DialogflowConversation
from flask_dialogflow.context import ContextManager
from flask_dialogflow.conversation import (
    V2DialogflowConversation, V2beta1DialogflowConversation
)
from flask_dialogflow.google_apis.dialogflow_v2 import Sentiment
from flask_dialogflow.integrations import GenericIntegrationConversation
from flask_dialogflow.integrations.actions_on_google import (
    V2ActionsOnGoogleDialogflowConversation
)


class TestDialogflowConversation:

    @pytest.mark.parametrize('conv_cls', [
        V2DialogflowConversation, V2beta1DialogflowConversation
    ])
    def test_empty_init(self, conv_cls):
        conv = conv_cls()
        assert isinstance(conv.webhook_request, conv._df.WebhookRequest)
        assert isinstance(conv.contexts, ContextManager)
        assert isinstance(
            conv.integrations['foo'], GenericIntegrationConversation
        )
        assert isinstance(conv.to_webhook_response(), conv._df.WebhookResponse)

    @pytest.fixture
    def conv(self, agent) -> DialogflowConversation:
        df = agent._df
        webhook_request = df.WebhookRequest(
            session='foo/bar',
            query_result=df.QueryResult(
                intent=df.Intent(display_name='TestIntent'),
                query_text='hello world',
                language_code='en',
                all_required_params_present=True,
                intent_detection_confidence=0.9,
                speech_recognition_confidence=0.8,
                sentiment_analysis_result=df.SentimentAnalysisResult(
                    df.Sentiment(0.1, 0.2)
                ),
                output_contexts=[df.Context('foo_ctx')]
            ),
            original_detect_intent_request=df.OriginalDetectIntentRequest(
                source='google', version='2'
            )
        )
        return agent._initialize_conversation(webhook_request)

    def test_webhook_request(self, conv):
        assert isinstance(conv.webhook_request, conv._df.WebhookRequest)

    @pytest.mark.parametrize('attr, expected', [
        ('session', 'foo/bar'),
        ('response_id', None),
        ('query_text', 'hello world'),
        ('language_code', 'en'),
        ('intent', 'TestIntent'),
        ('action', None),
        ('parameters', {}),
        ('all_required_params_present', True),
        ('fallback_level', 0),
        ('diagnostic_info', {}),
        ('intent_detection_confidence', 0.9),
        ('speech_recognition_confidence', 0.8),
        ('sentiment', Sentiment(0.1, 0.2)),
        ('source', 'google'),
        ('version', '2'),
        ('payload', {}),
    ])
    def test_conv_attrs(self, conv, attr, expected):
        assert getattr(conv, attr) == expected

    @pytest.mark.parametrize('source, integration_conv', [
        ('google', V2ActionsOnGoogleDialogflowConversation),
        ('facebook', GenericIntegrationConversation),
        ('slack', GenericIntegrationConversation),
        ('telegram', GenericIntegrationConversation),
        ('kik', GenericIntegrationConversation),
        ('skype', GenericIntegrationConversation),
        ('twilio', GenericIntegrationConversation),
        ('twilio_ip', GenericIntegrationConversation),
        ('line', GenericIntegrationConversation),
        ('spark', GenericIntegrationConversation),
        ('tropo', GenericIntegrationConversation),
        ('viber', GenericIntegrationConversation),
        ('foobar', GenericIntegrationConversation),  # __getattr__
    ])
    def test_integration_convs(self, source, integration_conv, agent):

        @agent.handle('TestIntegration')
        def handler(conv):
            assert isinstance(getattr(conv, source), integration_conv)
            return conv

        agent.test_request('TestIntegration')

    def test_context(self, conv):
        assert 'foo_ctx' in conv.contexts

    def test_ask(self, conv):
        conv.ask('foo bar?')
        resp = conv.to_webhook_response()
        assert resp.fulfillment_messages[0].text.text[0] == 'foo bar?'

    def test_tell(self, conv):
        if not isinstance(conv, V2beta1DialogflowConversation):
            pytest.skip('Only part of v2beta1')
        conv.tell('foo bar')
        resp = conv.to_webhook_response()
        assert resp.fulfillment_messages[0].text.text[0] == 'foo bar'
        assert resp.end_interaction

    def test_show_quick_replies(self, conv):
        conv.show_quick_replies('foo', 'bar', title='baz')
        resp = conv.to_webhook_response()
        qr = resp.fulfillment_messages[0].quick_replies
        assert qr.quick_replies == ['foo', 'bar']
        assert qr.title == 'baz'

    def test_show_card(self, conv):
        card = conv._df.Card('foo')
        conv.show_card(card)
        resp = conv.to_webhook_response()
        assert resp.fulfillment_messages[0].card == card

    def test_show_image(self, conv):
        img = conv._df.Image('foo.png')
        conv.show_image(img)
        resp = conv.to_webhook_response()
        assert resp.fulfillment_messages[0].image == img

    def test_alternative_query_results(self, conv):
        if not isinstance(conv, V2beta1DialogflowConversation):
            pytest.skip('Only part of v2beta1')
        assert conv.alternative_query_results == []

    def test_ctx_set_builds_full_name(self, conv):
        conv.contexts.set('baz')
        assert conv.contexts.get('baz').name == 'foo/bar/contexts/baz'

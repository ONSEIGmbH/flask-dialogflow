# -*- coding: utf-8 -*-
"""
    test_actions_on_google
    ~~~~~~~

    :copyright: (c) 2018 ONSEI GmbH
    :license: Proprietary
"""
from dataclasses import fields, dataclass, asdict
from datetime import datetime, timedelta, timezone

import pytest

from flask_dialogflow.google_apis.actions_on_google_v2 import (
    User,
    UserProfile,
    AppRequest,
    Input,
    BasicCard,
    TableCard,
    MediaResponse,
    CarouselBrowse,
    OrderUpdate,
    OpenUrlAction,
    SimpleSelect,
    ListSelect,
    CarouselSelect,
    CollectionSelect,
    ProposedOrder,
    OrderOptions,
    PaymentOptions,
    PresentationOptions,
)
from flask_dialogflow.integrations.actions_on_google import (
    UserFacade,
    V2ActionsOnGoogleDialogflowConversation,
    ssmlify,
)
from flask_dialogflow.json import JSON


class TestUserFacade:

    def test_can_init_without_user_obj(self):
        assert UserFacade()

    @pytest.fixture
    def user(self):
        return User(
            user_id='foo123',
            id_token='bar456',
            profile=UserProfile(),
            access_token='baz789',
            locale='foo_FOO',
            last_seen=datetime.now(timezone.utc),
            user_storage=None,
        )

    @pytest.fixture
    def user_facade(self, user) -> UserFacade:
        return UserFacade(user)

    @pytest.mark.parametrize('attr', [f.name for f in fields(User)])
    def test_all_user_attrs_accessible_through_facade(self, attr, user_facade):
        assert getattr(user_facade, attr, 'missing') != 'missing'

    def test_last_seen_before(self, user_facade):
        assert isinstance(user_facade.last_seen_before, timedelta)
        assert user_facade.last_seen_before.days < 100

    def test_user_storage_initialization(self, user_facade):
        assert isinstance(
            user_facade.user_storage, user_facade._user_storage_default_factory
        )

    def test_user_storage_with_existing_storage(self, user):
        user.user_storage = '{"bar": 42}'
        user_facade = UserFacade(user)
        assert isinstance(
            user_facade.user_storage, user_facade._user_storage_default_factory
        )
        assert user_facade.user_storage['bar'] == 42

    def test_delete_user_storage(self, user_facade):
        del user_facade.user_storage
        assert hasattr(user_facade, 'user_storage')
        default = user_facade._user_storage_default_factory()
        assert user_facade.user_storage == default
        assert user_facade._serialize_user_storage() is None

    def test_custom_user_storage_class(self, user):
        @dataclass
        class Foo:
            bar: int = None

        user_facade = UserFacade(
            user,
            user_storage_default_factory=Foo,
            user_storage_serializer=asdict,
            user_storage_deserializer=lambda data: Foo(**data),
        )

        assert isinstance(user_facade.user_storage, Foo)
        assert user_facade.user_storage.bar is None
        user_facade.user_storage.bar = 42
        assert user_facade.user_storage.bar == 42
        assert user_facade._serialize_user_storage() == {'bar': 42}

    def test_serialize_user_storage(self, user_facade):
        user_facade.user_storage['foo'] = 'bar'
        assert user_facade._serialize_user_storage() == '{"foo": "bar"}'


class TestV2ActionsOnGoogleDialogflowConversation:

    def test_from_request_json(self, aog_payload):
        assert V2ActionsOnGoogleDialogflowConversation.from_webhook_request_payload(
            aog_payload
        )

    @pytest.fixture
    def conv(self, aog_payload):
        return V2ActionsOnGoogleDialogflowConversation.from_webhook_request_payload(
            aog_payload
        )

    def test_app_request(self, conv):
        assert isinstance(conv.app_request, AppRequest)

    @pytest.mark.parametrize('user_attr', [f.name for f in fields(User)])
    def test_user(self, conv, user_attr):
        """Test that all User attributes are available via the UserFacade."""
        assert hasattr(conv.user, user_attr)

    def test_inputs(self, conv):
        assert all(isinstance(inp, Input) for inp in conv.inputs)

    def test_surface(self, conv):
        assert isinstance(conv.surface, tuple)
        if conv.surface:
            assert isinstance(conv.surface[0], str)

    def test_surface_when_surface_None(self, conv):
        conv.app_request.surface = None
        assert conv.surface == tuple()

    def test_has_screen(self, conv):
        assert isinstance(conv.has_screen, bool)

    def test_available_surfaces(self, conv):
        assert isinstance(conv.available_surfaces, tuple)
        if conv.available_surfaces:
            assert isinstance(conv.available_surfaces[0], str)

    def test_available_surfaces_when_available_surfaces_None(self, conv):
        conv.app_request.available_surfaces = None
        assert conv.available_surfaces == tuple()

    def test_is_in_sandbox(self, conv):
        assert isinstance(conv.is_in_sandbox, bool)

    def test_ask(self, conv):
        conv.ask('foo')
        resp = conv.to_webhook_response_payload()
        sr = resp['richResponse']['items'][0]['simpleResponse']
        assert sr['textToSpeech'] is None
        assert sr['ssml'] == '<speak>foo</speak>'

    def test_ask_with_automatic_ssml_off(self, conv):
        conv.text_to_speech_as_ssml = False
        conv.ask('foo')
        resp = conv.to_webhook_response_payload()
        sr = resp['richResponse']['items'][0]['simpleResponse']
        assert sr['textToSpeech'] == 'foo'
        assert sr['ssml'] is None

    def test_ask_ssml(self, conv):
        conv.text_to_speech_as_ssml = False
        conv.ask_ssml('foo')
        resp = conv.to_webhook_response_payload()
        sr = resp['richResponse']['items'][0]['simpleResponse']
        assert sr['textToSpeech'] is None
        assert sr['ssml'] == '<speak>foo</speak>'

    def test_ask_does_expect_response(self, conv):
        conv.ask('foo')
        resp = conv.to_webhook_response_payload()
        assert resp['expectUserResponse'] is True

    def test_tell(self, conv):
        conv.tell('foo')
        resp = conv.to_webhook_response_payload()
        sr = resp['richResponse']['items'][0]['simpleResponse']
        assert sr['textToSpeech'] is None
        assert sr['ssml'] == '<speak>foo</speak>'

    def test_tell_with_automatic_ssml_off(self, conv):
        conv.text_to_speech_as_ssml = False
        conv.tell('foo')
        resp = conv.to_webhook_response_payload()
        sr = resp['richResponse']['items'][0]['simpleResponse']
        assert sr['textToSpeech'] == 'foo'
        assert sr['ssml'] is None

    def test_tell_ssml(self, conv):
        conv.text_to_speech_as_ssml = False
        conv.tell_ssml('foo')
        resp = conv.to_webhook_response_payload()
        sr = resp['richResponse']['items'][0]['simpleResponse']
        assert sr['textToSpeech'] is None
        assert sr['ssml'] == '<speak>foo</speak>'

    def test_tell_doesnt_expect_response(self, conv):
        conv.tell('foo')
        resp = conv.to_webhook_response_payload()
        assert resp['expectUserResponse'] is False

    def test_display(self, conv):
        conv.ask('foo')
        conv.display('bar')
        resp = conv.to_webhook_response_payload()
        sr = resp['richResponse']['items'][0]['simpleResponse']
        assert sr['ssml'] == '<speak>foo</speak>'
        assert sr['displayText'] == 'bar'

    def test_display_with_multiple_rich_response_items(self, conv):
        conv.ask('foo')
        conv.ask('bar')
        conv.show_basic_card(BasicCard())
        conv.display('baz')
        resp = conv.to_webhook_response_payload()
        sr0 = resp['richResponse']['items'][0]['simpleResponse']
        assert sr0['ssml'] == '<speak>foo</speak>'
        assert sr0['displayText'] is None
        sr1 = resp['richResponse']['items'][1]['simpleResponse']
        assert sr1['ssml'] == '<speak>bar</speak>'
        assert sr1['displayText'] == 'baz'

    def test_display_raises_ValueError_when_no_text_set(self, conv):
        with pytest.raises(ValueError):
            conv.display('foo')

    def test_suggest(self, conv):
        conv.suggest('foo', 'bar')
        resp = conv.to_webhook_response_payload()
        rr = resp['richResponse']
        assert rr['suggestions'][0]['title'] == 'foo'
        assert rr['suggestions'][1]['title'] == 'bar'

    def test_show_basic_card(self, conv):
        card = BasicCard(title='foo')
        conv.show_basic_card(card)
        resp = conv.to_webhook_response_payload()
        bc = resp['richResponse']['items'][0]['basicCard']
        assert bc == card.to_json()

    def test_show_image(self, conv):
        url = 'foo.com/bar.jpg'
        conv.show_image(url=url, accessibility_text='foo')
        resp = conv.to_webhook_response_payload()
        bc = resp['richResponse']['items'][0]['basicCard']
        assert bc['image']['url'] == url

    def test_show_table_card(self, conv):
        table_card = TableCard()
        conv.show_table_card(table_card)
        resp = conv.to_webhook_response_payload()
        tc = resp['richResponse']['items'][0]['tableCard']
        assert tc == table_card.to_json()

    def test_play_media_response(self, conv):
        media_response = MediaResponse()
        conv.play_media_response(media_response)
        resp = conv.to_webhook_response_payload()
        mr = resp['richResponse']['items'][0]['mediaResponse']
        assert mr == media_response.to_json()

    def test_show_browsing_carousel(self, conv):
        carousel_browse = CarouselBrowse()
        conv.show_carousel_browse(carousel_browse)
        resp = conv.to_webhook_response_payload()
        cb = resp['richResponse']['items'][0]['carouselBrowse']
        assert cb == carousel_browse.to_json()

    def test_show_order_update(self, conv):
        order_update = OrderUpdate()
        conv.show_order_update(order_update)
        resp = conv.to_webhook_response_payload()
        struct_resp = resp['richResponse']['items'][0]['structuredResponse']
        ou = struct_resp['orderUpdate']
        assert ou == order_update.to_json()

    def test_suggest_link_out(self, conv):
        conv.suggest_link_out('foo', 'bar')
        resp = conv.to_webhook_response_payload()
        los = resp['richResponse']['linkOutSuggestion']
        assert los['destinationName'] == 'foo'
        assert los['openUrlAction']['url'] == 'bar'

    def test_ask_for_permission(self, conv):
        conv.ask_for_permission(reason='foo')
        resp = conv.to_webhook_response_payload()
        _assert_system_intent_is(resp, 'PERMISSION')
        _assert(resp, 'optContext', is_='foo')

    def test_ask_for_confirmation(self, conv):
        conv.ask_for_confirmation('foo')
        resp = conv.to_webhook_response_payload()
        _assert_system_intent_is(resp, 'CONFIRMATION')
        _assert(resp, 'dialogSpec', 'requestConfirmationText', is_='foo')

    def test_ask_for_sign_in(self, conv):
        conv.ask_for_sign_in(reason='foo')
        resp = conv.to_webhook_response_payload()
        _assert_system_intent_is(resp, 'SIGN_IN')
        _assert(resp, 'optContext', is_='foo')

    def test_ask_for_datetime(self, conv):
        conv.ask_for_datetime(request_text='foo')
        resp = conv.to_webhook_response_payload()
        _assert_system_intent_is(resp, 'DATETIME')
        _assert(resp, 'dialogSpec', 'requestDatetimeText', is_='foo')

    def test_ask_for_date(self, conv):
        conv.ask_for_date(request_text='foo')
        resp = conv.to_webhook_response_payload()
        _assert_system_intent_is(resp, 'DATETIME')
        _assert(resp, 'dialogSpec', 'requestDateText', is_='foo')

    def test_ask_for_time(self, conv):
        conv.ask_for_time(request_text='foo')
        resp = conv.to_webhook_response_payload()
        _assert_system_intent_is(resp, 'DATETIME')
        _assert(resp, 'dialogSpec', 'requestTimeText', is_='foo')

    def test_ask_for_screen_surface(self, conv):
        conv.ask_for_screen_surface('foo', 'bar')
        resp = conv.to_webhook_response_payload()
        _assert_system_intent_is(resp, 'NEW_SURFACE')
        _assert(resp, 'context', is_='foo')

    def test_ask_for_new_surface(self, conv):
        conv.ask_for_new_surface(['actions.capability.SCREEN'], 'foo', 'bar')
        resp = conv.to_webhook_response_payload()
        _assert_system_intent_is(resp, 'NEW_SURFACE')
        _assert(resp, 'context', is_='foo')

    def test_ask_for_link(self, conv):
        conv.ask_for_link(OpenUrlAction(url='foo.com'))
        resp = conv.to_webhook_response_payload()
        _assert_system_intent_is(resp, 'LINK')
        _assert(resp, 'openUrlAction', 'url', is_='foo.com')

    def test_ask_for_simple_selection(self, conv):
        simple_select = SimpleSelect()
        conv.ask_for_simple_selection(simple_select)
        resp = conv.to_webhook_response_payload()
        _assert_system_intent_is(resp, 'OPTION')
        _assert(resp, 'simpleSelect', is_=simple_select.to_json())

    def test_ask_for_list_selection(self, conv):
        list_select = ListSelect()
        conv.ask_for_list_selection(list_select)
        resp = conv.to_webhook_response_payload()
        _assert_system_intent_is(resp, 'OPTION')
        _assert(resp, 'listSelect', is_=list_select.to_json())

    def test_ask_for_collection_selection(self, conv):
        collection_select = CollectionSelect()
        conv.ask_for_collection_selection(collection_select)
        resp = conv.to_webhook_response_payload()
        _assert_system_intent_is(resp, 'OPTION')
        _assert(resp, 'collectionSelect', is_=collection_select.to_json())

    def test_ask_for_carousel_selection(self, conv):
        carousel_select = CarouselSelect()
        conv.ask_for_carousel_selection(carousel_select)
        resp = conv.to_webhook_response_payload()
        _assert_system_intent_is(resp, 'OPTION')
        _assert(resp, 'carouselSelect', is_=carousel_select.to_json())

    def test_ask_for_delivery_address(self, conv):
        conv.ask_for_delivery_address(reason='foo')
        resp = conv.to_webhook_response_payload()
        _assert_system_intent_is(resp, 'DELIVERY_ADDRESS')
        _assert(resp, 'addressOptions', 'reason', is_='foo')

    def test_ask_for_transaction_requirements_check(self, conv):
        order_options = OrderOptions()
        payment_options = PaymentOptions()
        conv.ask_for_transaction_requirements_check(
            order_options, payment_options
        )
        resp = conv.to_webhook_response_payload()
        _assert_system_intent_is(resp, 'TRANSACTION_REQUIREMENTS_CHECK')
        _assert(resp, 'orderOptions', is_=order_options.to_json())
        _assert(resp, 'paymentOptions', is_=payment_options.to_json())

    def test_ask_for_transaction_decision(self, conv):
        proposed_order = ProposedOrder()
        order_options = OrderOptions()
        payment_options = PaymentOptions()
        presentation_options = PresentationOptions()
        conv.ask_for_transaction_decision(
            proposed_order,
            order_options,
            payment_options,
            presentation_options,
        )
        resp = conv.to_webhook_response_payload()
        _assert_system_intent_is(resp, 'TRANSACTION_DECISION')
        _assert(resp, 'proposedOrder', is_=proposed_order.to_json())
        _assert(resp, 'orderOptions', is_=order_options.to_json())
        _assert(resp, 'paymentOptions', is_=payment_options.to_json())
        _assert(
            resp, 'presentationOptions', is_=presentation_options.to_json()
        )


def _assert_system_intent_is(resp: JSON, intent: str) -> None:
    """Helper to assert the type of a system intent."""
    assert resp['systemIntent']['intent'] == f'actions.intent.{intent}'


def _assert(resp: JSON, *keys: str, is_: str) -> None:
    """Helper to assert values in a system intents value spec."""
    data = resp['systemIntent']['data']
    keys = list(keys)
    while keys:
        data = data[keys.pop(0)]
    assert data == is_


def test_ssmlify():
    assert ssmlify('foo') == '<speak>foo</speak>'

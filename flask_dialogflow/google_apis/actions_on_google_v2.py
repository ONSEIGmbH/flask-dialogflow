# -*- coding: utf-8 -*-
"""
    actions_on_google
    ~~~~~~~

    :copyright: (c) 2018 ONSEI GmbH
    :license: Proprietary
"""
# pylint: disable=missing-docstring, too-many-lines

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import partial
from typing import Optional, Any, Dict, List

from flask_dialogflow.google_apis import (
    GoogleType,
    GoogleTypeSchema,
    Str,
    Int,
    Float,
    Bool,
    DateTimeF,
    ModuleLocalNested,
    DictF,
    ListF,
    Raw,
    EnumField,
)

Nested = partial(ModuleLocalNested, module_name=__name__)


# ---------- REQUEST ---------------------------------------------------------
# https://developers.google.com/actions/reference/rest/Shared.Types/AppRequest


class _AppRequestSchema(GoogleTypeSchema):
    user = Nested('_UserSchema')
    device = Nested('_DeviceSchema')
    surface = Nested('_SurfaceSchema')
    conversation = Nested('_ConversationSchema')
    inputs = ListF(Nested('_InputSchema'))
    isInSandbox = Bool(attribute='is_in_sandbox')
    availableSurfaces = ListF(
        Nested('_SurfaceSchema'), attribute='available_surfaces'
    )


@dataclass
class AppRequest(GoogleType, schema=_AppRequestSchema):
    user: Optional['User'] = None
    device: Optional['Device'] = None
    surface: Optional['Surface'] = None
    conversation: Optional['Conversation'] = None
    inputs: List['Input'] = field(default_factory=list)
    is_in_sandbox: Optional[bool] = None
    available_surfaces: List['Surface'] = field(default_factory=list)


class _UserSchema(GoogleTypeSchema):
    userId = Str(attribute='user_id')
    idToken = Str(attribute='id_token')
    profile = Nested('_UserProfileSchema')
    accessToken = Str(attribute='access_token')
    permissions = ListF(Nested('_PermissionSchema'))
    locale = Str()
    lastSeen = DateTimeF(attribute='last_seen')
    userStorage = Str(attribute='user_storage')
    packageEntitlements = ListF(
        Nested('_PackageEntitlementSchema'), attribute='package_entitlements'
    )


@dataclass
class User(GoogleType, schema=_UserSchema):
    user_id: Optional[str] = None
    id_token: Optional[str] = None
    profile: Optional['UserProfile'] = None
    access_token: Optional[str] = None
    permissions: List['Permission'] = field(default_factory=list)
    locale: Optional[str] = None
    last_seen: Optional[datetime] = None
    user_storage: Optional[str] = None
    package_entitlements: List['PackageEntitlement'] = field(
        default_factory=list
    )


class _UserProfileSchema(GoogleTypeSchema):
    displayName = Str(attribute='display_name')
    givenName = Str(attribute='given_name')
    familyName = Str(attribute='family_name')


@dataclass
class UserProfile(GoogleType, schema=_UserProfileSchema):
    display_name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None


class _PackageEntitlementSchema(GoogleTypeSchema):
    packageName = Str(attribute='package_name')
    entitlements = ListF(Nested('_EntitlementSchema'))


@dataclass
class PackageEntitlement(GoogleType, schema=_PackageEntitlementSchema):
    package_name: Optional[str] = None
    entitlements: List['Entitlement'] = field(default_factory=list)


class _EntitlementSchema(GoogleTypeSchema):
    sku = Str()
    skuType = Nested('_SkuTypeSchema', attribute='sku_type')
    inAppDetails = Nested('_SignedDataSchema', attribute='in_app_details')


@dataclass
class Entitlement(GoogleType, schema=_EntitlementSchema):
    sku: Optional[str] = None
    sku_type: Optional['SkuType'] = None
    in_app_details: Optional['SignedData'] = None


class _SignedDataSchema(GoogleTypeSchema):
    inAppPurchaseData = DictF(attribute='in_app_purchase_data')
    inAppDataSignature = Str(attribute='in_app_data_signature')


@dataclass
class SignedData(GoogleType, schema=_SignedDataSchema):
    in_app_purchase_data: Dict[str, Any] = field(default_factory=dict)
    in_app_data_signature: Optional[str] = None


class _DeviceSchema(GoogleTypeSchema):
    location = Nested('_LocationSchema')


@dataclass
class Device(GoogleType, schema=_DeviceSchema):
    location: Optional['Location'] = None


class _SurfaceSchema(GoogleTypeSchema):
    capabilities = ListF(Nested('_CapabilitySchema'))


@dataclass
class Surface(GoogleType, schema=_SurfaceSchema):
    capabilities: List['Capability'] = field(default_factory=list)


class _CapabilitySchema(GoogleTypeSchema):
    name = Str()


@dataclass
class Capability(GoogleType, schema=_CapabilitySchema):
    name: Optional[str] = None


class ConversationType(Enum):
    TYPE_UNSPECIFIED = 'TYPE_UNSPECIFIED'
    NEW = 'NEW'
    ACTIVE = 'ACTIVE'


class _ConversationSchema(GoogleTypeSchema):
    conversationId = Str(attribute='conversation_id')
    type = EnumField(ConversationType)
    conversationToken = Str(attribute='conversation_token')


@dataclass
class Conversation(GoogleType, schema=_ConversationSchema):
    conversation_id: Optional[str] = None
    type: Optional['ConversationType'] = None
    conversation_token: Optional[str] = None


class _InputSchema(GoogleTypeSchema):
    rawInputs = ListF(Nested('_RawInputSchema'), attribute='raw_inputs')
    intent = Str()
    arguments = ListF(Nested('_ArgumentSchema'))


@dataclass
class Input(GoogleType, schema=_InputSchema):
    raw_inputs: List['RawInput'] = field(default_factory=list)
    intent: Optional[str] = None
    arguments: List['Argument'] = field(default_factory=list)


class InputType(Enum):
    UNSPECIFIED_INPUT_TYPE = 'UNSPECIFIED_INPUT_TYPE'
    TOUCH = 'TOUCH'
    VOICE = 'VOICE'
    KEYBOARD = 'KEYBOARD'
    URL = 'URL'


class _RawInputSchema(GoogleTypeSchema):
    inputType = EnumField(InputType, attribute='input_type')
    query = Str()
    url = Str()


@dataclass
class RawInput(GoogleType, schema=_RawInputSchema):
    input_type: Optional['InputType'] = None
    query: Optional[str] = None
    url: Optional[str] = None


# ---------- RESPONSE --------------------------------------------------------
# https://developers.google.com/actions/reference/rest/Shared.Types/AppResponse


class _AppResponseSchema(GoogleTypeSchema):
    conversationToken = Str(attribute='conversation_token')
    userStorage = Str(attribute='user_storage')
    resetUserStorage = Bool(attribute='reset_user_storage')
    expectUserResponse = Bool(attribute='expect_user_response')
    expectedInputs = ListF(
        Nested('_ExpectedInputSchema'), attribute='expected_inputs'
    )
    finalResponse = Nested('_FinalResponseSchema', attribute='final_response')
    customPushMessage = Nested(
        '_CustomPushMessageSchema', attribute='custom_push_message'
    )
    isInSandbox = Bool(attribute='is_in_sandbox')


@dataclass
class AppResponse(GoogleType, schema=_AppResponseSchema):
    conversation_token: Optional[str] = None
    user_storage: Optional[str] = None
    reset_user_storage: Optional[bool] = None
    expect_user_response: Optional[bool] = None
    expected_inputs: List['ExpectedInput'] = field(default_factory=list)
    final_response: Optional['FinalResponse'] = None
    custom_push_message: Optional['CustomPushMessage'] = None
    is_in_sandbox: Optional[bool] = None


class _ExpectedInputSchema(GoogleTypeSchema):
    inputPrompt = Nested('_InputPromptSchema', attribute='input_prompt')
    possibleIntents = ListF(
        Nested('_ExpectedIntentSchema'), attribute='possible_intents'
    )
    speechBiasingHints = ListF(Str(), attribute='speech_biasing_hints')


@dataclass
class ExpectedInput(GoogleType, schema=_ExpectedInputSchema):
    input_prompt: Optional['InputPrompt'] = None
    possible_intents: List['ExpectedIntent'] = field(default_factory=list)
    speech_biasing_hints: List[str] = field(default_factory=list)


class _InputPromptSchema(GoogleTypeSchema):
    initialPrompts = ListF(
        Nested('_SpeechResponseShema'), attribute='initial_prompts'
    )
    richInitialPrompt = Nested(
        '_RichResponseSchema', attribute='rich_initial_prompt'
    )
    noInputPrompts = Nested(
        '_SimpleResponseSchema', attribute='no_input_prompts'
    )


@dataclass
class InputPrompt(GoogleType, schema=_InputPromptSchema):
    initial_prompts: List['SpeechResponse'] = field(default_factory=list)
    rich_initial_prompt: Optional['RichResponse'] = None
    no_input_prompts: List['SimpleResponse'] = field(default_factory=list)


class _SpeechResponseSchema(GoogleTypeSchema):
    textToSpeech = Str(attribute='text_to_speech')
    ssml = Str()


@dataclass
class SpeechResponse(GoogleType, schema=_SpeechResponseSchema):
    text_to_speech: Optional[str] = None
    ssml: Optional[str] = None


class _RichResponseSchema(GoogleTypeSchema):
    items = ListF(Nested('_ItemSchema'))
    suggestions = ListF(Nested('_SuggestionSchema'))
    linkOutSuggestion = Nested(
        '_LinkOutSuggestionSchema', attribute='link_out_suggestion'
    )


@dataclass
class RichResponse(GoogleType, schema=_RichResponseSchema):
    items: List['Item'] = field(default_factory=list)
    suggestions: List['Suggestion'] = field(default_factory=list)
    link_out_suggestion: Optional['LinkOutSuggestion'] = None


class _ItemSchema(GoogleTypeSchema):
    name = Str()
    simpleResponse = Nested(
        '_SimpleResponseSchema', attribute='simple_response'
    )
    basicCard = Nested('_BasicCardSchema', attribute='basic_card')
    structuredResponse = Nested(
        '_StructuredResponseSchema', attribute='structured_response'
    )
    mediaResponse = Nested('_MediaResponseSchema', attribute='media_response')
    carouselBrowse = Nested(
        '_CarouselBrowseSchema', attribute='carousel_browse'
    )
    tableCard = Nested('_TableCardSchema', attribute='table_card')


@dataclass
class Item(GoogleType, schema=_ItemSchema):
    name: Optional[str] = None
    simple_response: Optional['SimpleResponse'] = None
    basic_card: Optional['BasicCard'] = None
    structured_response: Optional['StructuredResponse'] = None
    media_response: Optional['MediaResponse'] = None
    carousel_browse: Optional['CarouselBrowse'] = None
    table_card: Optional['TableCard'] = None


class _SimpleResponseSchema(GoogleTypeSchema):
    textToSpeech = Str(attribute='text_to_speech')
    ssml = Str()
    displayText = Str(attribute='display_text')


@dataclass
class SimpleResponse(GoogleType, schema=_SimpleResponseSchema):
    text_to_speech: Optional[str] = None
    ssml: Optional[str] = None
    display_text: Optional[str] = None


class ImageDisplayOptions(Enum):
    DEFAULT = 'DEFAULT'
    WHITE = 'WHITE'
    CROPPED = 'CROPPED'


class _BasicCardSchema(GoogleTypeSchema):
    title = Str()
    subtitle = Str()
    formattedText = Str(attribute='formatted_text')
    image = Nested('_ImageSchema')
    buttons = ListF(Nested('_ButtonSchema'))
    imageDisplayOptions = EnumField(
        ImageDisplayOptions, attribute='image_display_options'
    )


@dataclass
class BasicCard(GoogleType, schema=_BasicCardSchema):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    formatted_text: Optional[str] = None
    image: Optional['Image'] = None
    buttons: List['Button'] = field(default_factory=list)
    image_display_options: Optional['ImageDisplayOptions'] = None


class _ButtonSchema(GoogleTypeSchema):
    title = Str()
    openUrlAction = Nested('_OpenUrlActionSchema', attribute='open_url_action')


@dataclass
class Button(GoogleType, schema=_ButtonSchema):
    title: Optional[str] = None
    open_url_action: Optional['OpenUrlAction'] = None


class _StructuredResponseSchema(GoogleTypeSchema):
    orderUpdate = Nested('_OrderUpdateSchema', attribute='order_update')


@dataclass
class StructuredResponse(GoogleType, schema=_StructuredResponseSchema):
    order_update: Optional['OrderUpdate'] = None


class _OrderUpdateSchema(GoogleTypeSchema):
    googleOrderId = Str(attribute='google_order_id')
    actionOrderId = Str(attribute='action_order_id')
    orderState = Nested('_OrderStateSchema', attribute='order_state')
    orderManagementActions = ListF(
        Nested('_ActionSchema'), attribute='order_management_actions'
    )
    receipt = Nested('_ReceiptSchema')
    updateTime = DateTimeF(attribute='update_time')
    totalPrice = Nested('_PriceSchema', attribute='total_price')
    lineItemUpdates = DictF(
        keys=Str(),
        values=Nested('_LineItemUpdateSchema'),
        attribute='line_item_updates',
    )
    userNotification = Nested(
        '_UserNotificationSchema', attribute='user_notification'
    )
    infoExtension = DictF(keys=Str(), values=Raw(), attribute='info_extension')
    rejectionInfo = Nested('_RejectionInfoSchema', attribute='rejection_info')
    cancellationInfo = Nested(
        '_CancellationInfoSchema', attribute='cancellation_info'
    )
    inTransitInfo = Nested('_InTransitInfoSchema', attribute='in_transit_info')
    fulfillmentInfo = Nested(
        '_FulfillmentInfoSchema', attribute='fulfillment_info'
    )
    returnInfo = Nested('_ReturnInfoSchema', attribute='return_info')


@dataclass
class OrderUpdate(GoogleType, schema=_OrderUpdateSchema):
    google_order_id: Optional[str] = None
    action_order_id: Optional[str] = None
    order_state: Optional['OrderState'] = None
    order_management_actions: List['Action'] = field(default_factory=list)
    receipt: Optional['Receipt'] = None
    update_time: Optional[datetime] = None
    total_price: Optional['Price'] = None
    line_item_updates: Dict[str, 'LineItemUpdate'] = field(
        default_factory=dict
    )
    user_notification: Optional['UserNotification'] = None
    info_extension: Dict[str, Any] = field(default_factory=dict)
    rejection_info: Optional['RejectionInfo'] = None
    cancellation_info: Optional['CancellationInfo'] = None
    in_transit_info: Optional['InTransitInfo'] = None
    fulfillment_info: Optional['FulfillmentInfo'] = None
    return_info: Optional['ReturnInfo'] = None


class ActionType(Enum):
    UNKNOWN = 'UNKNOWN'
    VIEW_DETAILS = 'VIEW_DETAILS'
    MODIFY = 'MODIFY'
    CANCEL = 'CANCEL'
    RETURN = 'RETURN'
    EXCHANGE = 'EXCHANGE'
    EMAIL = 'EMAIL'
    CALL = 'CALL'
    REORDER = 'REORDER'
    REVIEW = 'REVIEW'
    CUSTOMER_SERVICE = 'CUSTOMER_SERVICE'
    FIX_ISSUE = 'FIX_ISSUE'


class _ActionSchema(GoogleTypeSchema):
    type = EnumField(ActionType)
    button = Nested('_ButtonSchema')


@dataclass
class Action(GoogleType, schema=_ActionSchema):
    type: Optional['ActionType'] = None
    button: Optional['Button'] = None


class _ReceiptSchema(GoogleTypeSchema):
    confirmedActionOrderId = Str(attribute='confirmed_action_order_id')
    userVisibleOrderId = Str(attribute='user_visible_order_id')


@dataclass
class Receipt(GoogleType, schema=_ReceiptSchema):
    confirmed_action_order_id: Optional[str] = None
    user_visible_order_id: Optional[str] = None


class ReasonType(Enum):
    UNKNOWN = 'UNKNOWN'
    PAYMENT_DECLINED = 'PAYMENT_DECLINED'
    INELIGIBLE = 'INELIGIBLE'
    PROMO_NOT_APPLICABLE = 'PROMO_NOT_APPLICABLE'
    UNAVAILABLE_SLOT = 'UNAVAILABLE_SLOT'


class _RejectionInfoSchema(GoogleTypeSchema):
    type = EnumField(ReasonType)
    reason = Str()


@dataclass
class RejectionInfo(GoogleType, schema=_RejectionInfoSchema):
    type: Optional['ReasonType'] = None
    reason: Optional[str] = None


class _CancellationInfoSchema(GoogleTypeSchema):
    reason = Str()


@dataclass
class CancellationInfo(GoogleType, schema=_CancellationInfoSchema):
    reason: Optional[str] = None


class _InTransitInfoSchema(GoogleTypeSchema):
    updatedTime = DateTimeF(attribute='updated_time')


@dataclass
class InTransitInfo(GoogleType, schema=_InTransitInfoSchema):
    updated_time: datetime


class _FulfillmentInfoSchema(GoogleTypeSchema):
    deliveryTime = DateTimeF(attribute='delivery_time')


@dataclass
class FulfillmentInfo(GoogleType, schema=_FulfillmentInfoSchema):
    delivery_time: datetime


class _ReturnInfoSchema(GoogleTypeSchema):
    reason = Str()


@dataclass
class ReturnInfo(GoogleType, schema=_ReturnInfoSchema):
    reason: Optional[str] = None


class _UserNotificationSchema(GoogleTypeSchema):
    title = Str()
    text = Str()


@dataclass
class UserNotification(GoogleType, schema=_UserNotificationSchema):
    title: Optional[str] = None
    text: Optional[str] = None


class MediaType(Enum):
    MEDIA_TYPE_UNSPECIFIED = 'MEDIA_TYPE_UNSPECIFIED'
    AUDIO = 'AUDIO'


class _MediaResponseSchema(GoogleTypeSchema):
    mediaType = EnumField('MediaType', attribute='media_type')
    mediaObjects = ListF(
        Nested('_MediaObjectSchema'), attribute='media_objects'
    )


@dataclass
class MediaResponse(GoogleType, schema=_MediaResponseSchema):
    media_type: Optional['MediaType'] = None
    media_objects: List['MediaObject'] = field(default_factory=list)


class _MediaObjectSchema(GoogleTypeSchema):
    name = Str()
    description = Str()
    contentUrl = Str(attribute='content_url')
    largeImage = Nested('_ImageSchema', attribute='large_image')
    icon = Nested('_ImageSchema')


@dataclass
class MediaObject(GoogleType, schema=_MediaObjectSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    content_url: Optional[str] = None
    large_image: Optional['Image'] = None
    icon: Optional['Image'] = None


class _CarouselBrowseSchema(GoogleTypeSchema):
    items = ListF(Nested('_CarouselBrowseItemSchema'))
    imageDisplayOptions = EnumField(
        ImageDisplayOptions, attribute='image_display_options'
    )


@dataclass
class CarouselBrowse(GoogleType, schema=_CarouselBrowseSchema):
    items: List['CarouselBrowseItem'] = field(default_factory=list)
    image_display_options: Optional['ImageDisplayOptions'] = None


class _CarouselBrowseItemSchema(GoogleTypeSchema):
    title = Str()
    description = Str()
    footer = Str()
    image = Nested('_ImageSchema')
    openUrlAction = Nested('_OpenUrlActionSchema', attribute='open_url_action')


@dataclass
class CarouselBrowseItem(GoogleType, schema=_CarouselBrowseItemSchema):
    title: Optional[str] = None
    description: Optional[str] = None
    footer: Optional[str] = None
    image: Optional['Image'] = None
    open_url_action: Optional['OpenUrlAction'] = None


class _TableCardSchema(GoogleTypeSchema):
    title = Str()
    subtitle = Str()
    image = Nested('_ImageSchema')
    columnProperties = ListF(
        Nested('_ColumPropertiesSchema'), attribute='column_properties'
    )
    rows = ListF(Nested('_RowSchema'))
    buttons = ListF(Nested('_ButtonSchema'))


@dataclass
class TableCard(GoogleType, schema=_TableCardSchema):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    image: Optional['Image'] = None
    column_properties: List['ColumnProperties'] = field(default_factory=list)
    rows: List['Row'] = field(default_factory=list)
    buttons: List['Button'] = field(default_factory=list)


class HorizontalAlignment(Enum):
    LEADING = 'LEADING'
    CENTER = 'CENTER'
    TRAILING = 'TRAILING'


class _ColumnPropertiesSchema(GoogleTypeSchema):
    header = Str()
    horizontalAlignment = EnumField(
        HorizontalAlignment, attribute='horizontal_alignment'
    )


@dataclass
class ColumnProperties(GoogleType, schema=_ColumnPropertiesSchema):
    header: Optional[str] = None
    horizontal_alignment: Optional['HorizontalAlignment'] = None


class _RowSchema(GoogleTypeSchema):
    cells = ListF(Nested('_CellSchema'))
    dividerAfter = Bool(attribute='divider_after')


@dataclass
class Row(GoogleType, schema=_RowSchema):
    cells: List['Cell'] = field(default_factory=list)
    divider_after: Optional[bool] = None


class _CellSchema(GoogleTypeSchema):
    text = Str()


@dataclass
class Cell(GoogleType, schema=_CellSchema):
    text: Optional[str] = None


class _SuggestionSchema(GoogleTypeSchema):
    title = Str()


@dataclass
class Suggestion(GoogleType, schema=_SuggestionSchema):
    title: Optional[str] = None


class _LinkOutSuggestionSchema(GoogleTypeSchema):
    destinationName = Str(attribute='destination_name')
    url = Str()
    openUrlAction = Nested('_OpenUrlActionSchema', attribute='open_url_action')


@dataclass
class LinkOutSuggestion(GoogleType, schema=_LinkOutSuggestionSchema):
    destination_name: Optional[str] = None
    url: Optional[str] = None
    open_url_action: Optional['OpenUrlAction'] = None


class _ExpectedIntentSchema(GoogleTypeSchema):
    intent = Str()
    inputValueData = DictF(
        keys=Str(), values=Raw(), attribute='input_value_data'
    )
    parameterName = Str(attribute='parameter_name')


@dataclass
class ExpectedIntent(GoogleType, schema=_ExpectedIntentSchema):
    intent: Optional[str] = None
    input_value_data: Dict[str, Any] = field(default_factory=dict)
    parameter_name: Optional[str] = None


class _FinalResponseSchema(GoogleTypeSchema):
    speechResponse = Nested(
        '_SpeechResponseSchema', attribute='speech_response'
    )
    richResponse = Nested('_RichResponseSchema', attribute='rich_response')


@dataclass
class FinalResponse(GoogleType, schema=_FinalResponseSchema):
    speech_response: Optional['SpeechResponse'] = None
    rich_response: Optional['RichResponse'] = None


class _CustomPushMessageSchema(GoogleTypeSchema):
    target = Nested('_TargetSchema')
    orderUpdate = Nested('_OrderUpdateSchema', attribute='order_update')
    userNotification = Nested(
        '_UserNotification', attribute='user_notification'
    )


@dataclass
class CustomPushMessage(GoogleType, schema=_CustomPushMessageSchema):
    target: Optional['Target'] = None
    order_update: Optional['OrderUpdate'] = None
    user_notification: Optional['UserNotification'] = None


class _UserNotificationSchema(GoogleTypeSchema):
    title = Str()
    text = Str()


@dataclass
class UserNotification(GoogleType, schema=_UserNotificationSchema):
    title: Optional[str] = None
    text: Optional[str] = None


class _TargetSchema(GoogleTypeSchema):
    userId = Str(attribute='user_id')
    intent = Str()
    argument = Nested('_ArgumentSchema')
    locale = Str()


@dataclass
class Target(GoogleType, schema=_TargetSchema):
    user_id: Optional[str] = None
    intent: Optional[str] = None
    argument: Optional['Argument'] = None
    locale: Optional[str] = None


# ---------- OTHER TYPES -----------------------------------------------------


class _ArgumentSchema(GoogleTypeSchema):
    name = Str()
    rawText = Str(attribute='raw_text')
    textValue = Str(attribute='text_value')
    status = Nested('_StatusSchema')
    intValue = Str(attribute='int_value')  # Sic!
    floatValue = Float(attribute='float_value')
    boolValue = Bool(attribute='bool_value')
    datetimeValue = Nested('_DateTimeSchema', attribute='datetime_value')
    placeValue = Nested('_LocationSchema', attribute='place_value')
    extension = DictF(keys=Str(), values=Raw())
    structuredValue = DictF(
        keys=Str(), values=Raw(), attribute='structured_value'
    )


@dataclass
class Argument(GoogleType, schema=_ArgumentSchema):
    name: Optional[str] = None
    raw_text: Optional[str] = None
    text_value: Optional[str] = None
    status: Optional['Status'] = None
    int_value: Optional[str] = None
    float_value: Optional[float] = None
    bool_value: Optional[bool] = None
    datetime_value: Optional['DateTime'] = None
    place_value: Optional['Location'] = None
    extension: Dict[str, Any] = field(default_factory=dict)
    structured_value: Dict[str, Any] = field(default_factory=dict)


class _DateTimeSchema(GoogleTypeSchema):
    date = Nested('_DateSchema')
    time = Nested('_TimeOfDaySchema')


@dataclass
class DateTime(GoogleType, schema=_DateTimeSchema):
    date: Optional['Date'] = None
    time: Optional['TimeOfDay'] = None


class _DateSchema(GoogleTypeSchema):
    year = Float()
    month = Float()
    day = Float()


@dataclass
class Date(GoogleType, schema=_DateSchema):
    year: Optional[float] = None
    month: Optional[float] = None
    day: Optional[float] = None


class _TimeOfDaySchema(GoogleTypeSchema):
    hours = Float()
    minutes = Float()
    seconds = Float()
    nanos = Float()


@dataclass
class TimeOfDay(GoogleType, schema=_TimeOfDaySchema):
    hours: Optional[float] = None
    minutes: Optional[float] = None
    seconds: Optional[float] = None
    nanos: Optional[float] = None


class CardNetwork(Enum):
    UNSPECIFIED_CARD_NETWORK = 'UNSPECIFIED_CARD_NETWORK'
    AMEX = 'AMEX'
    DISCOVER = 'DISCOVER'
    MASTERCARD = 'MASTERCARD'
    VISA = 'VISA'
    JOB = 'JOB'


class _CompletePurchaseValueSchema(GoogleTypeSchema):
    purchaseStatus = Nested(
        '_PurchaseStatusSchema', attribute='purchase_status'
    )
    orderId = Str(attribute='order_id')
    purchaseToken = Str(attribute='purchase_token')


@dataclass
class CompletePurchaseValue(GoogleType, schema=_CompletePurchaseValueSchema):
    purchase_status: Optional['PurchaseStatus'] = None
    order_id: Optional[str] = None
    purchase_token: Optional[str] = None


class _CompletePurchaseValueSpecSchema(GoogleTypeSchema):
    skuId = Nested('_SkuIdSchema', attribute='sku_id')
    developerPayload = Str(attribute='developer_payload')


@dataclass
class CompletePurchaseValueSpec(
    GoogleType, schema=_CompletePurchaseValueSpecSchema
):
    sku_id: Optional['SkuId'] = None
    developer_payload: Optional[str] = None


class SkuType(Enum):
    SKU_TYPE_UNSPECIFIED = 'SKU_TYPE_UNSPECIFIED'
    SKU_TYPE_IN_APP = 'SKU_TYPE_IN_APP'
    SKU_TYPE_SUBSCRIPTION = 'SKU_TYPE_SUBSCRIPTION'


class _SkuIdSchema(GoogleTypeSchema):
    skuType = EnumField(SkuType, attribute='sku_type')
    id = Str()
    packageName = Str(attribute='package_name')


@dataclass
class SkuId(GoogleType, schema=_SkuIdSchema):
    sku_type: Optional['SkuType']
    id: Optional[str] = None
    package_name: Optional[str] = None


class _ConfirmationValueSpecSchema(GoogleTypeSchema):
    dialogSpec = Nested(
        '_ConfirmationDialogSpecSchema', attribute='dialog_spec'
    )


@dataclass
class ConfirmationValueSpec(GoogleType, schema=_ConfirmationValueSpecSchema):
    dialog_spec: Optional['ConfirmationDialogSpec'] = None


class _ConfirmationDialogSpecSchema(GoogleTypeSchema):
    requestConfirmationText = Str(attribute='request_confirmation_text')


@dataclass
class ConfirmationDialogSpec(GoogleType, schema=_ConfirmationDialogSpecSchema):
    request_confirmation_text: Optional[str] = None


class CustomerInfoProperty(Enum):
    CUSTOMER_INFO_PROPERTY_UNSPECIFIED = 'CUSTOMER_INFO_PROPERTY_UNSPECIFIED'
    EMAIL = 'EMAIL'


class _DateTimeValueSpecSchema(GoogleTypeSchema):
    dialogSpec = Nested('_DateTimeDialogSpecSchema', attribute='dialog_spec')


@dataclass
class DateTimeValueSpec(GoogleType, schema=_DateTimeValueSpecSchema):
    dialog_spec: Optional['DateTimeDialogSpec'] = None


class _DateTimeDialogSpecSchema(GoogleTypeSchema):
    requestDatetimeText = Str(attribute='request_datetime_text')
    requestDateText = Str(attribute='request_date_text')
    requestTimeText = Str(attribute='request_time_text')


@dataclass
class DateTimeDialogSpec(GoogleType, schema=_DateTimeDialogSpecSchema):
    request_datetime_text: Optional[str] = None
    request_date_text: Optional[str] = None
    request_time_text: Optional[str] = None


class DeliveryAddressUserDecision(Enum):
    UNKNOWN_USER_DECISION = 'UNKNWON_USER_DECISION'
    ACCEPTED = 'ACCEPTED'
    REJECTED = 'REJECTED'


class _DeliveryAddressValueSchema(GoogleTypeSchema):
    userDecision = EnumField(
        DeliveryAddressUserDecision, attribute='user_decision'
    )
    location = Nested('_LocationSchema')


@dataclass
class DeliveryAddressValue(GoogleType, schema=_DeliveryAddressValueSchema):
    user_decision: Optional['DeliveryAddressUserDecision'] = None
    location: Optional['Location'] = None


class _DeliveryAddressValueSpecSchema(GoogleTypeSchema):
    addressOptions = Nested(
        '_AddressOptionsSchema', attribute='address_options'
    )


@dataclass
class DeliveryAddressValueSpec(
    GoogleType, schema=_DeliveryAddressValueSpecSchema
):
    address_options: Optional['AddressOptions'] = None


class _AddressOptionsSchema(GoogleTypeSchema):
    reason = Str()


@dataclass
class AddressOptions(GoogleType, schema=_AddressOptionsSchema):
    reason: Optional[str] = None


class _DialogSpecSchema(GoogleTypeSchema):
    extension = DictF(keys=Str(), values=Raw())


@dataclass
class DialogSpec(GoogleType, schema=_DialogSpecSchema):
    extension: Dict[str, Any] = field(default_factory=dict)


class Frequency(Enum):
    FREQUENCY_UNSPECIFIED = 'FREQUENCY_UNSPECIFIED'
    DAILY = 'DAILY'
    ROUTINES = 'ROUTINES'


class _GenericExtensionSchema(GoogleTypeSchema):
    locations = ListF(Nested('_OrderLocationsSchema'))
    time = Nested('_TimeSchema')


@dataclass
class GenericExtension(GoogleType, schema=_GenericExtensionSchema):
    locations: List['OrderLocation'] = field(default_factory=list)
    time: Optional['Time'] = None


class OrderLocationType(Enum):
    UNKNOWN = 'UNKNOWN'
    DELIVERY = 'DELIVERY'
    BUSINESS = 'BUSINESS'
    ORIGIN = 'ORIGIN'
    DESTINATION = 'DESTINATION'
    PICK_UP = 'PICK_UP'


class _OrderLocationSchema(GoogleTypeSchema):
    type = EnumField(OrderLocationType)
    location = Nested('_LocationSchema')


@dataclass
class OrderLocation(GoogleType, schema=_OrderLocationSchema):
    type: Optional['OrderLocationType'] = None
    location: Optional['Location'] = None


class TimeType(Enum):
    UNKNOWN = 'UNKNOWN'
    DELIVERY_DATE = 'DELIVERY_DATE'
    ETA = 'ETA'
    RESERVATION_SLOT = 'RESERVATION_SLOT'


class _TimeSchema(GoogleTypeSchema):
    type = EnumField(TimeType)
    timeIso8601 = Str(attribute='time_iso_8601')


@dataclass
class Time(GoogleType, schema=_TimeSchema):
    type: Optional['TimeType'] = None
    time_iso_8601: Optional[str] = None


class _ImageSchema(GoogleTypeSchema):
    url = Str()
    accessibilityText = Str(attribute='accessibility_text')
    height = Float()
    width = Float()


@dataclass
class Image(GoogleType, schema=_ImageSchema):
    url: str
    accessibility_text: str
    height: Optional[float] = None
    width: Optional[float] = None


class LineItemType(Enum):
    UNSPECIFIED = 'UNSPECIFIED'
    REGULAR = 'REGULAR'
    TAX = 'TAX'
    DISCOUNT = 'DISCOUNT'
    GRATUITY = 'GRATUITY'
    SUBTOTAL = 'SUBTOTAL'
    FEE = 'FEE'


class _LineItemUpdateSchema(GoogleTypeSchema):
    orderState = Nested('_OrderStateSchema', attribute='order_state')
    price = Nested('_PriceSchema')
    reason = Str()
    extension = DictF(keys=Str(), values=Raw())


@dataclass
class LineItemUpdate(GoogleType, schema=_LineItemUpdateSchema):
    order_state: Optional['OrderState'] = None
    price: Optional['Price'] = None
    reason: Optional[str] = None
    extension: Dict[str, Any] = field(default_factory=dict)


class _LinkDialogSpecSchema(GoogleTypeSchema):
    destinationName = Str(attribute='destination_name')
    requestLinkReason = Str(attribute='request_link_reason')


@dataclass
class LinkDialogSpec(GoogleType, schema=_LinkDialogSpecSchema):
    destination_name: Optional[str] = None
    request_link_reason: Optional[str] = None


class _LinkValueSpecSchema(GoogleTypeSchema):
    openUrlAction = Nested('_OpenUrlActionSchema', attribute='open_url_action')
    dialogSpec = Nested('_DialogSpecSchema', attribute='dialog_spec')


@dataclass
class LinkValueSpec(GoogleType, schema=_LinkValueSpecSchema):
    open_url_action: Optional['OpenUrlAction'] = None
    dialog_spec: Optional['DialogSpec'] = None


class _LocationSchema(GoogleTypeSchema):
    coordinates = Nested('_LatLngSchema')
    formattedAddress = Str(attribute='formatted_address')
    zipCode = Str(attribute='zip_code')
    city = Str()
    postalAddress = Nested('_PostalAddressSchema', attribute='postal_address')
    name = Str()
    phoneNumber = Str(attribute='phone_number')
    notes = Str()
    placeId = Str(attribute='place_id')


@dataclass
class Location(GoogleType, schema=_LocationSchema):
    coordinates: Optional['LatLng'] = None
    formatted_address: Optional[str] = None
    zip_code: Optional[str] = None
    city: Optional[str] = None
    postal_address: Optional['PostalAddress'] = None
    name: Optional[str] = None
    phone_number: Optional[str] = None
    notes: Optional[str] = None
    place_id: Optional[str] = None


class _LatLngSchema(GoogleTypeSchema):
    latitude = Float()
    longitude = Float()


@dataclass
class LatLng(GoogleType, schema=_LatLngSchema):
    latitude: Optional[Float] = None
    longitude: Optional[Float] = None


class Status(Enum):
    STATUS_UNSPECIFIED = 'STATUS_UNSPECIFIED'
    FINISHED = 'FINISHED'
    FAILED = 'FAILED'


class _MediaStatusSchema(GoogleTypeSchema):
    status = EnumField(Status)


@dataclass
class MediaStatus(GoogleType, schema=_MediaStatusSchema):
    status: Optional['Status'] = None


class NewSurfaceStatus(Enum):
    NEW_SURFACE_STATUS_UNSPECIFIED = 'NEW_SURFACE_STATUS_UNSPECIFIED'
    CANCELLED = 'CANCELLED'
    OK = 'OK'


class _NewSurfaceValueSchema(GoogleTypeSchema):
    status = EnumField(NewSurfaceStatus)


@dataclass
class NewSurfaceValue(GoogleType, schema=_NewSurfaceValueSchema):
    status: Optional['NewSurfaceStatus'] = None


class _NewSurfaceValueSpecSchema(GoogleTypeSchema):
    capabilities = ListF(Str())
    context = Str()
    notificationTitle = Str(attribute='notification_title')


@dataclass
class NewSurfaceValueSpec(GoogleType, schema=_NewSurfaceValueSpecSchema):
    capabilities: List[str] = field(default_factory=list)
    context: Optional[str] = None
    notification_title: Optional[str] = None


class _OpenUrlActionSchema(GoogleTypeSchema):
    url = Str()
    androidApp = Nested('_AndroidAppSchema', attribute='android_app')
    urlTypeHint = EnumField('UrlTypeHint', attribute='url_type_hint')


@dataclass
class OpenUrlAction(GoogleType, schema=_OpenUrlActionSchema):
    url: Optional[str] = None
    android_app: Optional['AndroidApp'] = None
    url_type_hint: Optional['UrlTypeHint'] = None


class _AndroidAppSchema(GoogleTypeSchema):
    packageName = Str(attribute='package_name')
    versions = ListF(Nested('_VersionFilterSchema'))


@dataclass
class AndroidApp(GoogleType, schema=_AndroidAppSchema):
    package_name: Optional[str] = None
    versions: List['VersionFilter'] = field(default_factory=list)


class _VersionFilterSchema(GoogleTypeSchema):
    minVersion = Float(attribute='min_version')
    maxVersion = Float(attribute='max_version')


@dataclass
class VersionFilter(GoogleType, schema=_VersionFilterSchema):
    min_version: Optional[float] = None
    max_version: Optional[float] = None


class _OptionInfoSchema(GoogleTypeSchema):
    key = Str()
    synonyms = ListF(Str())


@dataclass
class OptionInfo(GoogleType, schema=_OptionInfoSchema):
    key: Optional[str] = None
    synonyms: List[str] = field(default_factory=list)


class _OptionValueSpecSchema(GoogleTypeSchema):
    simpleSelect = Nested('_SimpleSelectSchema', attribute='simple_select')
    listSelect = Nested('_ListSelectSchema', attribute='list_select')
    carouselSelect = Nested(
        '_CarouselSelectSchema', attribute='carousel_select'
    )
    collectionSelect = Nested(
        '_CollectionSelectSchema', attribute='collection_select'
    )


@dataclass
class OptionValueSpec(GoogleType, schema=_OptionValueSpecSchema):
    simple_select: Optional['SimpleSelect'] = None
    list_select: Optional['ListSelect'] = None
    carousel_select: Optional['CarouselSelect'] = None
    collection_select: Optional['CollectionSelect'] = None


class _SimpleSelectSchema(GoogleTypeSchema):
    items = ListF(Nested('_SimpleSelectItemSchema'))


@dataclass
class SimpleSelect(GoogleType, schema=_SimpleSelectSchema):
    items: List['SimpleSelectItem'] = field(default_factory=list)


class _SimpleSelectItemSchema(GoogleTypeSchema):
    optionInfo = Nested('_OptionInfoSchema', attribute='option_info')
    title = Str()


@dataclass
class SimpleSelectItem(GoogleType, schema=_SimpleSelectItemSchema):
    option_info: Optional['OptionInfo'] = None
    title: Optional[str] = None


class _ListSelectSchema(GoogleTypeSchema):
    title = Str()
    subtitle = Str()
    items = ListF(Nested('_ListItemSchema'))


@dataclass
class ListSelect(GoogleType, schema=_ListSelectSchema):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    items: List['ListItem'] = field(default_factory=list)


class _ListItemSchema(GoogleTypeSchema):
    optionInfo = Nested('_OptionInfoSchema', attribute='option_info')
    title = Str()
    description = Str()
    image = Nested('_ImageSchema')


@dataclass
class ListItem(GoogleType, schema=_ListItemSchema):
    option_info: Optional['OptionInfo'] = None
    title: Optional[str] = None
    description: Optional[str] = None
    image: Optional['Image'] = None


class _CarouselSelectSchema(GoogleTypeSchema):
    title = Str()
    subtitle = Str()
    items = ListF(Nested('_CarouselItemSchema'))
    imageDisplayOptions = EnumField(
        ImageDisplayOptions, attribute='image_display_options'
    )


@dataclass
class CarouselSelect(GoogleType, schema=_CarouselSelectSchema):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    items: List['CarouselItem'] = field(default_factory=list)
    image_display_options: Optional['ImageDisplayOptions'] = None


class _CarouselItemSchema(GoogleTypeSchema):
    optionInfo = Nested('_OptionInfoSchema', attribute='option_info')
    title = Str()
    description = Str()
    image = Nested('_ImageSchema')


@dataclass
class CarouselItem(GoogleType, schema=_CarouselItemSchema):
    option_info: Optional['OptionInfo'] = None
    title: Optional[str] = None
    description: Optional[str] = None
    image: Optional['Image'] = None


class _CollectionSelectSchema(GoogleTypeSchema):
    title = Str()
    subtitle = Str()
    items = ListF(Nested('_CollectionItemSchema'))
    imageDisplayOptions = EnumField(
        ImageDisplayOptions, attribute='image_display_options'
    )


@dataclass
class CollectionSelect(GoogleType, schema=_CollectionSelectSchema):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    items: List['CollectionItem'] = field(default_factory=list)
    image_display_options: Optional['ImageDisplayOptions'] = None


class _CollectionItemSchema(GoogleTypeSchema):
    optionInfo = Nested('_OptionInfoSchema', attribute='option_info')
    title = Str()
    description = Str()
    image = Nested('_ImageSchema')


@dataclass
class CollectionItem(GoogleType, schema=_CollectionItemSchema):
    option_info: Optional['OptionInfo'] = None
    title: Optional[str] = None
    description: Optional[str] = None
    image: Optional['Image'] = None


class _OrderOptionsSchema(GoogleTypeSchema):
    requestDeliveryAddress = Bool(attribute='request_delivery_address')
    customerInfoOptions = Nested(
        '_CustomerInfoOptionsSchema', attribute='customer_info_options'
    )


@dataclass
class OrderOptions(GoogleType, schema=_OrderOptionsSchema):
    request_delivery_address: Optional[bool] = None
    customer_info_options: Optional['CustomerInfoOptions'] = None


class _CustomerInfoOptionsSchema(GoogleTypeSchema):
    customerInfoProperties = ListF(
        EnumField(CustomerInfoProperty), attribute='customer_info_properties'
    )


@dataclass
class CustomerInfoOptions(GoogleType, schema=_CustomerInfoOptionsSchema):
    customer_info_properties: List['CustomerInfoProperty'] = field(
        default_factory=list
    )


class _OrderStateSchema(GoogleTypeSchema):
    state = Str()
    label = Str()


@dataclass
class OrderState(GoogleType, schema=_OrderStateSchema):
    state: str
    label: str


class PaymentMethodTokenizationType(Enum):
    UNSPECIFIED_TOKENIZATION_TYPE = 'UNSPECIFIED_TOKENIZATION_TYPE'
    PAYMENT_GATEWAY = 'PAYMENT_GATEWAY'
    DIRECT = 'DIRECT'


class _PaymentOptionsSchema(GoogleTypeSchema):
    googleProvidedOptions = Nested(
        '_GoogleProvidedPaymentOptionsSchema',
        attribute='google_provided_options',
    )
    actionProvidedOptions = Nested(
        '_ActionProvidedPaymentOptionsSchema',
        attribute='action_provided_options',
    )


@dataclass
class PaymentOptions(GoogleType, schema=_PaymentOptionsSchema):
    google_provided_options: Optional['GoogleProvidedPaymentOptions'] = None
    action_provided_options: Optional['ActionProvidedPaymentOptions'] = None


class _GoogleProvidedPaymentOptionsSchema(GoogleTypeSchema):
    tokenizationParameters = Nested(
        '_PaymentMethodTokenizationParametersSchema',
        attribute='tokenization_parameters',
    )
    supportedCardNetworks = ListF(
        EnumField(CardNetwork), attribute='supported_card_networks'
    )
    prepaidCardDisallowed = Bool(attribute='prepaid_card_disallowed')
    billingAddressRequired = Bool(attribute='billing_address_required')


@dataclass
class GoogleProvidedPaymentOptions(
    GoogleType, schema=_GoogleProvidedPaymentOptionsSchema
):
    tokenization_parameters: Optional[
        'PaymentMethodTokenizationParameters'
    ] = None
    supported_card_networks: List['CardNetwork'] = field(default_factory=list)
    prepaid_card_disallowed: Optional[bool] = None
    billing_address_required: Optional[bool] = None


class _PaymentMethodTokenizationParametersSchema(GoogleTypeSchema):
    tokenizationType = EnumField(
        PaymentMethodTokenizationType, attribute='tokenization_type'
    )
    parameters = DictF(keys=Str(), values=Str())


@dataclass
class PaymentMethodTokenizationParameters(
    GoogleType, schema=_PaymentMethodTokenizationParametersSchema
):
    tokenization_type: Optional['PaymentMethodTokenizationType'] = None
    parameters: Dict[str, str] = field(default_factory=dict)


class PaymentType(Enum):
    PAYMENT_TYPE_UNSPECIFIED = 'PAYMENT_TYPE_UNSPECIFIED'
    PAYMENT_CARD = 'PAYMENT_CARD'
    BANK = 'BANK'
    LOYALTY_PROGRAM = 'LOYALTY_PROGRAM'
    ON_FULFILLMENT = 'ON_FULFILLMENT'
    GIFTCARD = 'GIFTCARD'


class _ActionProvidedPaymentOptionsSchema(GoogleTypeSchema):
    paymentType = EnumField(PaymentType, attribute='payment_type')
    displayName = Str(attribute='display_name')


@dataclass
class ActionProvidedPaymentOptions(
    GoogleType, schema=_ActionProvidedPaymentOptionsSchema
):
    payment_type: 'PaymentType'
    display_name: Optional[str] = None


class Permission(Enum):
    UNSPECIFIED_PERMISSION = 'UNSPECIFIED_PERMISSION'
    NAME = 'NAME'
    DEVICE_PRECISE_LOCATION = 'DEVICE_PRECISE_LOCATION'
    DEVICE_COARSE_LOCATION = 'DEVICE_COARSE_LOCATION'
    UPDATE = 'UPDATE'


class _PermissionValueSpecSchema(GoogleTypeSchema):
    optContext = Str(attribute='opt_context')
    permissions = ListF(Str())
    updatePermissionValueSpec = Nested(
        '_UpdatePermissionValueSpecSchema',
        attribute='update_permission_value_spec',
    )


@dataclass
class PermissionValueSpec(GoogleType, schema=_PermissionValueSpecSchema):
    opt_context: Optional[str] = None
    permissions: List['Permission'] = field(default_factory=list)
    update_permission_value_spec: Optional['UpdatePermissionValueSpec'] = None


class _UpdatePermissionValueSpecSchema(GoogleTypeSchema):
    intent = Str()
    arguments = ListF(Nested('_ArgumentSchema'))


@dataclass
class UpdatePermissionValueSpec(
    GoogleType, schema=_UpdatePermissionValueSpecSchema
):
    intent: Optional[str] = None
    arguments: List['Argument'] = field(default_factory=list)


class _PlaceDialogSpecSchema(GoogleTypeSchema):
    requestPrompt = Str(attribute='request_prompt')
    permissionContext = Str(attribute='permission_context')


@dataclass
class PlaceDialogSpec(GoogleType, schema=_PlaceDialogSpecSchema):
    request_prompt: Optional[str] = None
    permission_context: Optional[str] = None


class _PlaceValueSpecSchema(GoogleTypeSchema):
    dialogSpec = Nested('_DialogSpecSchema', attribute='dialog_spec')


@dataclass
class PlaceValueSpec(GoogleType, schema=_PlaceValueSpecSchema):
    dialog_spec: Optional['DialogSpec'] = None


class _PostalAddressSchema(GoogleTypeSchema):
    revision = Str()
    regionCode = Str(attribute='region_code')
    languageCode = Str(attribute='language_code')
    postalCode = Str(attribute='postal_code')
    sortingCode = Str(attribute='sorting_code')
    administrativeArea = Str(attribute='administrative_area')
    locality = Str()
    sublocality = Str()
    addressLines = ListF(Str(), attribute='address_lines')
    recipients = ListF(Str())
    organization = Str()


@dataclass
class PostalAddress(GoogleType, schema=_PostalAddressSchema):
    revision: Optional[float] = None
    region_code: Optional[str] = None
    language_code: Optional[str] = None
    postal_code: Optional[str] = None
    sorting_code: Optional[str] = None
    administrative_area: Optional[str] = None
    locality: Optional[str] = None
    sublocality: Optional[str] = None
    address_lines: List[str] = field(default_factory=list)
    recipients: List[str] = field(default_factory=list)
    organization: Optional[str] = None


class PriceType(Enum):
    UNKNOWN = 'UNKNOWN'
    ESTIMATE = 'ESTIMATE'
    ACTUAL = 'ACTUAL'


class _PriceSchema(GoogleTypeSchema):
    type = EnumField(PriceType)
    amount = Nested('_AmountSchema')


@dataclass
class Price(GoogleType, schema=_PriceSchema):
    type: Optional['PriceType'] = None
    amount: Optional['Money'] = None


class _MoneySchema(GoogleTypeSchema):
    currencyCode = Str(attribute='currency_code')
    units = Str()
    nanos = Int()


@dataclass
class Money(GoogleType, schema=_MoneySchema):
    currency_code: Optional[str] = None
    units: Optional[str] = None
    nanos: Optional[int] = None


class _ProposedOrderSchema(GoogleTypeSchema):
    id = Str()
    cart = Nested('_CartSchema')
    otherItems = ListF(Nested('_LineItemSchema'), attribute='other_items')
    image = Nested('_ImageSchema')
    termsOfServiceUrl = Str(attribute='terms_of_service_url')
    totalPrice = Nested('_PriceSchema', attribute='total_price')
    extension = DictF(keys=Str(), values=Raw())


@dataclass
class ProposedOrder(GoogleType, schema=_ProposedOrderSchema):
    id: Optional[str] = None
    cart: Optional['Cart'] = None
    other_items: List['LineItem'] = field(default_factory=list)
    image: Optional['Image'] = None
    terms_of_service_url: Optional[str] = None
    total_price: Optional['Price'] = None
    extension: Dict[str, Any] = field(default_factory=dict)


class _CartSchema(GoogleTypeSchema):
    id = Str()
    merchant = Nested('_MerchantSchema')
    lineItems = ListF(Nested('_LineItemSchema'), attribute='line_items')
    otherItems = ListF(Nested('_LineItemSchema'), attribute='other_items')
    notes = Str()
    promotions = ListF(Nested('_PromotionSchema'))
    extension = DictF(keys=Str(), values=Raw())


@dataclass
class Cart(GoogleType, schema=_CartSchema):
    id: Optional[str] = None
    merchant: Optional['Merchant'] = None
    line_items: List['LineItem'] = field(default_factory=list)
    other_items: List['ListItem'] = field(default_factory=list)
    notes: Optional[str] = None
    promotions: List['Promotion'] = field(default_factory=list)
    extension: Dict[str, Any] = field(default_factory=dict)


class _MerchantSchema(GoogleTypeSchema):
    id = Str()
    name = Str()


@dataclass
class Merchant(GoogleType, schema=_MerchantSchema):
    id: Optional[str] = None
    name: Optional[str] = None


class _LineItemSchema(GoogleTypeSchema):
    id = Str()
    name = Str()
    type = EnumField(LineItemType)
    quantity = Float()
    description = Str()
    image = Nested('_ImageSchema')
    price = Nested('_PriceSchema')
    subLines = ListF(Nested('_SubLineSchema'), attribute='sub_lines')
    offerId = Str(attribute='offer_id')
    extension = DictF(keys=Str(), values=Raw())


@dataclass
class LineItem(GoogleType, schema=_LineItemSchema):
    id: Optional[str] = None
    name: Optional[str] = None
    type: Optional['LineItemType'] = None
    quantity: Optional[float] = None
    description: Optional[str] = None
    image: Optional['Image'] = None
    price: Optional['Price'] = None
    sub_lines: List['SubLine'] = field(default_factory=list)
    offer_id: Optional[str] = None
    extension: Dict[str, Any] = field(default_factory=dict)


class _SubLineSchema(GoogleTypeSchema):
    lineItem = Nested('_LineItemSchema', attribute='line_item')
    note = Str()


@dataclass
class SubLine(GoogleType, schema=_SubLineSchema):
    line_item: Optional['LineItem'] = None
    note: Optional[str] = None


class _PromotionSchema(GoogleTypeSchema):
    coupon = Str()


@dataclass
class Promotion(GoogleType, schema=_PromotionSchema):
    coupon: str


class PurchaseStatus(Enum):
    PURCHASE_STATUS_UNSPECIFIED = 'PURCHASE_STATUS_UNSPECIFIED'
    PURCHASE_STATUS_OK = 'PURCHASE_STATUS_OK'
    PURCHASE_STATUS_ERROR = 'PURCHASE_STATUS_ERROR'
    PURCHASE_STATUS_USER_CANCELLED = 'PURCHASE_STATUS_USER_CANCELLED'
    PURCHASE_STATUS_ALREADY_OWNED = 'PURCHASE_STATUS_ALREADY_OWNED'
    PURCHASE_STATUS_ITEM_UNAVAILABLE = 'PURCHASE_STATUS_ITEM_UNAVAILABLE'
    PURCHASE_STATUS_ITEM_CHANGE_REQUESTED = (
        'PURCHASE_STATUS_ITEM_CHANGE_REQUESTED'
    )


class RegisterUpdateStatus(Enum):
    REGISTER_UPDATE_STATUS_UNSPECIFIED = 'REGISTER_UPDATE_STATUS_UNSPECIFIED'
    OK = 'OK'
    CANCELLED = 'CANCELLED'


class _RegisterUpdateValueSchema(GoogleTypeSchema):
    status = EnumField(RegisterUpdateStatus)


@dataclass
class RegisterUpdateValue(GoogleType, schema=_RegisterUpdateValueSchema):
    status: Optional['RegisterUpdateStatus'] = None


class _RegisterUpdateValueSpecSchema(GoogleTypeSchema):
    intent = Str()
    arguments = ListF(Nested('_ArgumentSchema'))
    triggerContext = Nested(
        '_TriggerContextSchema', attribute='trigger_context'
    )


@dataclass
class RegisterUpdateValueSpec(
    GoogleType, schema=_RegisterUpdateValueSpecSchema
):
    intent: Optional[str] = None
    arguments: List['Argument'] = field(default_factory=list)
    trigger_context: Optional['TriggerContext'] = None


class _TriggerContextSchema(GoogleTypeSchema):
    timeContext = Nested('_TimeContext', attribute='time_context')


@dataclass
class TriggerContext(GoogleType, schema=_TriggerContextSchema):
    time_context: Optional['TimeContext'] = None


class _TimeContextSchema(GoogleTypeSchema):
    frequency = EnumField(Frequency)


@dataclass
class TimeContext(GoogleType, schema=_TimeContextSchema):
    frequency: Optional['Frequency'] = None


class ResultType(Enum):
    RESULT_TYPE_UNSPECIFIED = 'RESULT_TYPE_UNSPECIFIED'
    Ok = 'OK'
    USER_ACTION_REQUIRED = 'USER_ACTION_REQUIRED'
    ASSISTANT_SURFACE_NOT_SUPPORTED = 'ASSISTANT_SURFACE_NOT_SUPPORTED'
    REGION_NOT_SUPPORTED = 'REGION_NOT_SUPPORTED'


class SignInStatus(Enum):
    SIGN_IN_STATUS_UNSPECIFIED = 'SIGN_IN_STATUS_UNSPECIFIED'
    OK = 'OK'
    CANCELLED = 'CANCELLED'
    ERROR = 'ERROR'


class _SignInValueSchema(GoogleTypeSchema):
    status = EnumField(SignInStatus)


@dataclass
class SignInValue(GoogleType, schema=_SignInValueSchema):
    status: Optional['SignInStatus'] = None


class _SignInValueSpecSchema(GoogleTypeSchema):
    optContext = Str(attribute='opt_context')


@dataclass
class SignInValueSpec(GoogleType, schema=_SignInValueSpecSchema):
    opt_context: Optional[str] = None


class TransactionUserDecision(Enum):
    UNKNOWN_USER_DECISION = 'UNKNOWN_USER_DECISION'
    ORDER_ACCEPTED = 'ORDER_ACCEPTED'
    ORDER_REJECTED = 'ORDER_REJECTED'
    DELIVERY_ADDRESS_UPDATED = 'DELIVERY_ADDRESS_UPDATED'
    CART_CHANGE_REQUESTED = 'CART_CHANGE_REQUESTED'


class _TransactionDecisionValueSchema(GoogleTypeSchema):
    checkResult = Nested(
        '_TransactionRequirementsCheckResultSchema', attribute='check_result'
    )
    userDecision = EnumField(
        TransactionUserDecision, attribute='user_decision'
    )
    order = Nested('_OrderSchema')
    deliveryAddress = Nested('_LocationSchema', attribute='delivery_address')


@dataclass
class TransactionDecisionValue(
    GoogleType, schema=_TransactionDecisionValueSchema
):
    check_result: Optional['TransactionsRequirementsCheckResult'] = None
    user_decision: Optional['TransactionUserDecision'] = None
    order: Optional['Order'] = None
    delivery_address: Optional['Location'] = None


class _TransactionsRequirementsCheckResultSchema(GoogleTypeSchema):
    resultType = EnumField(ResultType, attribute='result_type')


@dataclass
class TransactionsRequirementsCheckResult(
    GoogleType, schema=_TransactionsRequirementsCheckResultSchema
):
    result_type: Optional['ResultType'] = None


class _OrderSchema(GoogleTypeSchema):
    finalOrder = Nested('_ProposedOrderSchema', attribute='final_order')
    googleOrderId = Str(attribute='google_order_id')
    orderDate = DateTimeF(attribute='order_date')
    paymentInfo = Nested('_PaymentInfoSchema', attribute='payment_info')
    actionOrderId = Str(attribute='action_order_id')
    customerInfo = Nested('_CustomerInfoSchema', attribute='customer_info')


@dataclass
class Order(GoogleType, schema=_OrderSchema):
    final_order: Optional['ProposedOrder'] = None
    google_order_id: Optional[str] = None
    order_date: Optional[datetime] = None
    payment_info: Optional['PaymentInfo'] = None
    action_order_id: Optional[str] = None
    customer_info: Optional['CustomerInfo'] = None


class _PaymentInfoSchema(GoogleTypeSchema):
    paymentType = EnumField(PaymentType, attribute='payment_type')
    displayName = Str(attribute='display_name')
    googleProvidedPaymentInstrument = Nested(
        '_GoogleProvidedPaymentInstrumentSchema',
        attribute='google_provided_payment_instrument',
    )


@dataclass
class PaymentInfo(GoogleType, schema=_PaymentInfoSchema):
    payment_type: Optional['PaymentType'] = None
    display_name: Optional[str] = None
    google_provided_payment_instrument: Optional[
        'GoogleProvidedPaymentInstrument'
    ] = None


class _GoogleProvidedPaymentInstrumentSchema(GoogleTypeSchema):
    instrumentToken = Str(attribute='instrument_token')
    billingAddress = Nested(
        '_PostalAddressSchema', attribute='billing_address'
    )


@dataclass
class GoogleProvidedPaymentInstrument(
    GoogleType, schema=_GoogleProvidedPaymentInstrumentSchema
):
    instrument_token: Optional[str] = None
    billing_address: Optional['PostalAddress'] = None


class _CustomerInfoSchema(GoogleTypeSchema):
    email = Str()


@dataclass
class CustomerInfo(GoogleType, schema=_CustomerInfoSchema):
    email: Optional[str] = None


class _TransactionDecisionValueSpecSchema(GoogleTypeSchema):
    proposedOrder = Nested('_ProposedOrderSchema', attribute='proposed_order')
    orderOptions = Nested('_OrderOptionsSchema', attribute='order_options')
    paymentOptions = Nested(
        '_PaymentOptionsSchema', attribute='payment_options'
    )
    presentationOptions = Nested(
        '_PresentationOptionsSchema', attribute='presentation_options'
    )


@dataclass
class TransactionDecisionValueSpec(
    GoogleType, schema=_TransactionDecisionValueSpecSchema
):
    proposed_order: Optional['ProposedOrder'] = None
    order_options: Optional['OrderOptions'] = None
    payment_options: Optional['PaymentOptions'] = None
    presentation_options: Optional['PresentationOptions'] = None


class _PresentationOptionsSchema(GoogleTypeSchema):
    callToAction = Str(attribute='call_to_action')


@dataclass
class PresentationOptions(GoogleType, schema=_PresentationOptionsSchema):
    call_to_action: Optional[str] = None


class _TransactionRequirementsCheckSpecSchema(GoogleTypeSchema):
    orderOptions = Nested('_OrderOptionsSchema', attribute='order_options')
    paymentOptions = Nested(
        '_PaymentOptionsSchema', attribute='payment_options'
    )


@dataclass
class TransactionRequirementsCheckSpec(
    GoogleType, schema=_TransactionRequirementsCheckSpecSchema
):
    order_options: Optional['OrderOptions'] = None
    payment_options: Optional['PaymentOptions'] = None


class UrlTypeHint(Enum):
    URL_TYPE_HINT_UNSPECIFIED = 'URL_TYPE_HINT_UNSPECIFIED'
    AMP_CONTENT = 'AMP_CONTENT'

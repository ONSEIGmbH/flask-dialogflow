# -*- coding: utf-8 -*-
#
# Copyright (c) ONSEI GmbH
"""A minimal Hello-world agent to demonstrate the general usage of this lib."""

from flask import Flask, render_template as __

from onsei_google.agent import DialogflowAgent
from onsei_google.conversation import V2DialogflowConversation
from onsei_google.google_apis.actions_on_google_v2 import (
    BasicCard,
    Image,
    MediaResponse,
    MediaType,
    MediaObject,
)

app = Flask(__name__)
agent = DialogflowAgent(app, templates_file='templates/templates.yaml')


@agent.handle('Default Welcome Intent')
def welcome(conv: V2DialogflowConversation) -> V2DialogflowConversation:
    """A simple intent handler."""
    # The simplest possible response for an Actions-on-Google agent. Speaks and
    # displays the given text and leaves the session open for further input.
    conv.google.ask('Hallo ONSEI! Was kann ich für dich tun?')
    return conv


@agent.handle('GetDate')
def get_date(conv: V2DialogflowConversation) -> V2DialogflowConversation:
    """A slightly more complex intent handler.

    This intent handler contains a tiny bit of business logic and renders
    it's response from a template.
    """
    import datetime
    today = datetime.datetime.today()

    conv.google.tell(__('get_date', date=today))
    return conv


FERNSEHTURM_CARD = BasicCard(
    title='Der Berliner Fernsehturm',
    subtitle='Eines der Wahrzeichen der Stadt',
    image=Image(
        url='https://bit.ly/2SHqMNe',
        accessibility_text='Fernsehturm Berlin'
    ),
    formatted_text=(
        'Der Berliner Fernsehturm ist mit 368 Metern das höchste '
        'Bauwerk Deutschlands sowie das vierthöchste freistehende '
        'Bauwerk Europas. Der Fernsehturm befindet sich am '
        'Bahnhof Alexanderplatz im Berliner Ortsteil Mitte. Er '
        'war im Jahr der Fertigstellung 1969 der zweithöchste '
        'Fernsehturm der Welt und zählt mit über einer Million '
        'Besuchern jährlich zu den zehn beliebtesten '
        'Sehenswürdigkeiten in Deutschland. (Quelle: Wikipedia)'
    )
)


BRANDENBURGER_TOR_CARD = BasicCard(
    title='Das Brandenburger Tor',
    subtitle='Noch ein Wahrzeichen',
    image=Image(
        url='https://bit.ly/2W34SdL',
        accessibility_text='Brandenburger Tor'
    ),
    formatted_text=(
        'Das Brandenburger Tor in Berlin ist ein frühklassizistisches '
        'Triumphtor, das an der Westflanke des quadratischen Pariser Platzes '
        'im Berliner Ortsteil Mitte steht. Es wurde als Abschluss der '
        'zentralen Prachtstraße der Dorotheenstadt, des Boulevards Unter den '
        'Linden, in den Jahren von 1789 bis 1793 auf Anweisung des '
        'preußischen Königs Friedrich Wilhelm II. nach Entwürfen von Carl '
        'Gotthard Langhans errichtet. Die das Tor krönende Skulptur der '
        'Quadriga ist ein Werk nach dem Entwurf des Bildhauers Johann '
        'Gottfried Schadow. (Quelle: Wikipedia)'
    )
)


@agent.handle('GetBerlinPicture')
def get_berlin_picture(conv: V2DialogflowConversation) \
        -> V2DialogflowConversation:
    """An intent handler that renders a RichResponse with a BasicCard.

    Rich responses can contain different types of content such as images,
    audio, cards and link-out suggestions. Certain limits apply to what types
    of RichResponse items can be combined with each other, see the official
    Google docs for that:
    https://developers.google.com/actions/reference/rest/Shared.Types/AppResponse#richresponse

    Rich response items can always be constructed ad-hoc from the underlying
    Google types, but for larger projects is recommended to refactor them into
    a separate module to make them testable and reusable.

    Rich response items can be thought of as the React components of a
    Dialogflow agent. They should contain as few business logic as possible
    and should not produce side effects, but may render their textual content
    from a template.
    """
    conv.google.tell('Hier ist ein Bild aus Berlin!')

    # Use the user_storage field to ensure that the user is shown a different
    # image each time they invoke this intent. User_storage works like a
    # dictionary and is serialized with json.dumps.
    if not conv.google.user.user_storage.get('fernsehturm_shown'):
        conv.google.show_basic_card(FERNSEHTURM_CARD)
        conv.google.user.user_storage['fernsehturm_shown'] = True
    else:
        conv.google.show_basic_card(BRANDENBURGER_TOR_CARD)
        conv.google.user.user_storage['fernsehturm_shown'] = False

    return conv


@agent.handle('GetMediaResponse')
def get_media_response(conv: V2DialogflowConversation) \
        -> V2DialogflowConversation:
    """A MediaResponse."""
    # First response must always be a text, and the media response must always
    # close the session (i.e. conv.google.tell instead of conv.google.ask).
    conv.google.tell('Hier ist deine Media-Response:')
    media_response = MediaResponse(
        media_type=MediaType.AUDIO,
        media_objects=[
            MediaObject(
                name='Walzer in E-Moll',
                description='von Frederic Chopin',
                content_url='https://bit.ly/2YQnF8O',
                large_image=Image(
                    url='https://bit.ly/2W40fjw',
                    accessibility_text='Frederic Chopin'
                )
            )
        ]
    )
    conv.google.play_media_response(media_response)
    return conv


if __name__ == '__main__':
    app.run(debug=True)

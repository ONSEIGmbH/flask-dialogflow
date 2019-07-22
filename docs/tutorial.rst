Tutorial
========

This tutorial aims to give an overview over the core features. For details on
particular interfaces see the :doc:`API documentation<api>`.

Installation and setup
----------------------

Install the library from Pip. As usual, it is recommended to install into a
virtualenv:

.. code-block:: bash

    cd my_project
    virtualenv venv
    source venv/bin/activate
    pip install flask_onsei

A Flask app can be initialized with a :class:`.DialogflowAgent` in two ways.
One way is to pass the Flask instance directly to the init method:

.. code-block:: python

    app = Flask(__name__)
    agent = DialogflowAgent(app)

The other way is to defer initialization until later and the calling
:meth:`.DialogflowAgent.init_app` manually:

.. code-block:: python

    app = Flask(__name__)
    agent = DialogflowAgent()

    agent.init_app(app)

The latter works with `application factories`_ and is the recommended approach.
In both cases the Flask app gets:

    * A new route that accepts the webhook requests from Dialogflow.
    * A second Jinja loader to be able to load the agents responses from a YAML
      file.
    * A reference to the agent in the :attr:`.Flask.extensions` dictionary.
    * A reference to the agent in a Flask shell.

The only change that the agent makes to the Flask app is that it sets
:attr:`.Flask.jinja_env.auto_reload` to True. This is necessary to enable
template randomization. See Templating_ for details.

.. _application factories: http://flask.pocoo.org/docs/1.0/patterns/appfactories/

The URL endpoint defaults to ``/`` and the templates file to ``templates.yaml``.
Both can be configured in the init method:

.. code-block:: python

    agent = DialogflowAgent(
        route='/agent', templates_file='agent/templates.yaml'
    )

flask_onsei currently supports two versions of the Dialogflow API: ``v2`` and
``v2beta1``. The latter is, despite its name, a superset of the former and
therefore set as the default version. This means that the conversation objects
will be of type :class:`.V2beta1DialogflowConversation` and that API objects such
as Cards and Images should be imported from the
:py:mod:`flask_onsei.google_apis.dialogflow_v2beta1` module.

While it is possible to change the version to ``v2`` there is not much point to
this as the difference is minuscule. This option exists mostly to make the
library forward compatible with future Dialogflow versions.

The DialogflowAgent has a debug mode that can be activate via the ``debug`` init
param or the ``flask_onsei_DEBUG`` environment variable. It causes all webhook
requests and responses to be logged to the console (prettified).

Google APIs and serialization
-----------------------------

This library uses `marshmallow`_ to serialize and deserialize the Dialogflow and
Actions on Google API objects, but this is completely abstracted. The objects
are implemented as dataclasses and each have a corresponding marshmallow schema.
Each class and schema are linked in such a way the entire de-/serialization
process is hidden behind ``from_json``/``to_json`` methods on the classes. These
classes implement the entire Dialogflow (v2, v2beta1) and Actions on Google API
in three modules:

    * :mod:`flask_onsei.google_apis.actions_on_google_v2`
    * :mod:`flask_onsei.google_apis.dialogflow_v2`
    * :mod:`flask_onsei.google_apis.dialogflow_v2beta1`

Here is an example of how it works:

.. _marshmallow: https://marshmallow.readthedocs.io/en/3.0/index.html

.. code-block:: python

    from flask_onsei.google_apis.dialogflow_v2beta1 import Image

    # Deserialization from JSON
    Image.from_json(
        {'imageUri': 'https://image.png', 'accessibilityText': 'Image'}
    )
    # Image(image_uri='https://image.png', accessibility_text='Image')

    # Serialization to JSON
    Image(image_uri='https://image.png', accessibility_text='Image').to_json()
    # {'imageUri': 'https://image.png', 'accessibilityText': 'Image'}

.. note:: By JSON, we always mean plain Python data structures that
    can be handled by :meth:`.json.dumps`/:meth:`.json.loads`, i.e. usually
    dictionaries. Pythons type system does unfortunately not allow recursive
    types, which is why we type JSON as ``MutableMapping[str, Any]``.

This system powers the entire library and can also be used by users. See the
:doc:`API documentations<api>` section on JSON handling for details. Note also
that users will sometimes have to import classes from the API modules directly,
such as when using rich response items like cards or carousels.

The API classes are not documented because they map API interfaces into native
Python classes. Because of that, users will have to consult the original Google
documentations:

    * The authoritative source for the Dialogflow API is the `Dialogflow
      Discovery document <https://www.googleapis.com/discovery/v1/apis/dialogflow/v2beta1/rest>`_.
    * A web version of this is available on the
      `Google Cloud Dialogflow <https://cloud.google.com/dialogflow/docs/reference/rest/v2beta1-overview>`_
      page.
    * The Actions on Google API is documented on the
      `Actions on Google <https://developers.google.com/actions/build/json/>`_
      website.

Since the conversion from API objects (Protobuf messages) to Python classes is
not an exact science, here are conversion rules that we have applied:

    * Every API object becomes a Python dataclass.
    * CamelCase attribute names are converted to snake_case.
    * Names are kept as they are, except for a small number of cases were a
      class name is not unique across the API. In these cases the name is
      usually prepended with the enclosing messages name.
    * All fields are optional unless a field is explicitly documented as
      required. In these cases we have set them as required here as well to
      avoid some ``x is None`` checks.
    * Optional fields always default to None, except for lists and dictionaries.
      They default to empty collections to again avoid some None checks.
    * Oneof fields are implemented as individual, optional attributes.
    * Enums become Python enums.
    * Structs become ``Dict[str, Any]``.
    * Numbers are typed as int when either the Discovery document or the
      comments in the web documentation clearly state them as such, even though
      the web documentation knows only numbers. Otherwise they are floats.

The marshmallow schemas are only used to map the attributes from API objects to
classes. They perform no validation or type conversion, this, if at all, must be
done by the Python classes.


Conversations and handlers
--------------------------

*Conversation* objects are the core idea of this library. They represent one
turn of the conversation with the user and expose the request attributes as well
as methods to build the response. :class:`.V2beta1DialogflowConversation` is the
specific type that the conversation will be of under the default settings. It
is initialized from the :class:`.WebhookRequest` behind the scenes and handed
over to the appropriate handler function. After the handler has done its job it
is supposed to hand it back to the library, which will render it to a
:class:`.WebhookResponse`, serialize it to JSON and send it back to Dialogflow.

Conversations expose the request attributes as properties, e.g.:

.. code-block:: python

    conv.intent      # The intent name
    conv.parameters  # The requests parameters
    conv.session     # The session id

They also offer methods to build responses:

.. code-block:: python

    # A simple text response
    conv.tell('Hello world!')

    # Rendering a response from a template
    from flask import render_template
    conv.tell(render_template('hello'))

    # Showing a card
    from flask_onsei.google_apis.dialogflow_v2beta1 import Card
    card = Card(title='Beautiful image', image_uri='image.png')
    conv.show_card(card)

Conversations also give access to a requests contexts, for that see the
Contexts_ section.

*Conversation handlers* implement the core business logic of the agent. They are
functions that accept the conversation object, inspect its request attributes,
perform necessary business logic, build the response and return the conversation
object again. Handlers can be arbitrarily complex as long as they accept the
conversation as their first argument and return it again.

Handlers can of course pass the conversation on to sub handlers. This makes the
data flow easier to understand and test. Here is an example of a slightly more
complex handler setup:

.. code-block:: python

    @agent.handle('SelectDate)
    def choose_date_handler(conv):
        # Entry point for conversations for the SelectDate intent
        date = parse(conv.parameters['selected_date'])
        if date >= datetime.datetime.now():
            conv = valid_date(conv)
        else:
            conv = invalid_date(conv)
        return conv

    def valid_date(conv):
        ... # Business logic
        conv.tell('Date was chosen!')
        return conv

    def invalid_date(conv):
        ... # Business logic
        conv.tell('Date is invalid:(')
        return conv

The general idea is always that a handler gets a conversation, examines the
request attributes, passes the conversation on to where the specific
conversation state is best handled, builds the response and eventually
hands the conversation back to the library, which will take care of rendering
it correctly and sending it back.

Conversations are not meant to be inspected, i.e. one should never 'check' if
a certain response was already set and then try to do something based on the
result. Responses should be set once where it is appropriate and then not be
touched anymore.

Dialogflow has some constraints on what kind of and how many responses go
together (e.g. only two speech bubbles, one card etc.), but these are not
enforced by the conversation object as they are not always clearly documented
would make the API quite brittle. Users are expected to be familiar with the
Dialogflow API and watch the Dialogflow logs for errors.

Templating
----------

flask_onsei uses the `Jinja2`_ templating library just like Flask itself, but
adds two features to make it work better for voice assistants.

.. _Jinja2: http://jinja.pocoo.org/docs/2.10

The first one is that we expect all templates to be assembled into a single
YAML file. Each key of the file is its own template an can be rendered
independently. They are of course full Jinja templates and can use all features
of the Jinja templating language:

.. code-block:: yaml

    # A plain string template
    welcome: Hi, welcome to SomeAgent!

    # A template with a variable and a filter
    confirm_delivery: Ok, your delivery will arrive by {{ date|format('%A') }}.

These two would be rendered like any normal Flask template and passed to the
conversations response methods. Since we render templates a lot we typically
alias the ``render_template`` function:

.. code-block:: python

    from flask import render_template as __

    conv.tell(__('welcome'))
    conv.tell(__('confirm_delivery', date=datetime.datetime.now())))

The second feature that we add is randomization. For voice assistants it is
typically desirable to vary each speech response somewhat so as not to sound
robotic. flask_onsei makes this simple by supporting randomization out of the
box. It can be used by using arrays of different formulations for one template
in the templates file:

.. code-block:: yaml

    welcome:
      - Hi, welcome to SomeAgent!
      - Hi there, SomeAgent here.
      - Hello, here is SomeAgent!

This template is rendered as usual (``render_template('welcome')``), but one of
the three variations will be chosen at random.

It is also possible to weigh the options by specifying them as two-element
arrays, where the second element is the weight. The weight is optional and
defaults to 1:

.. code-block:: yaml

    welcome:
      - ['Hi, welcome to SomeAgent!', 2]
      - Hi there, SomeAgent here.
      - ['Yo, wazzup? SomeAgent here for you.', 0.5]

In this case the first variant has a probability of ~57% (=2/3.5), the second of
~29% (=1/3.5) and the third of ~14% (0.5/3.5). When using this option care has
to be taken to properly quote the strings so as to not accidentally malform the
array.


Contexts
--------

Contexts_ are essential to realize complex, multi-turn dialogs. Conversations
expose a requests contexts via the
:attr:`.V2beta1DialogflowConversation.contexts` attribute, which returns a
:class:`.ContextManager` that has methods to get, set, check and delete a
context.

.. _Contexts: https://dialogflow.com/docs/contexts

Checking if a context is present:

.. code-block:: python

    conv.contexts.has('some_ctx')

    # Or shorter:
    'some_ctx' in conv.contexts

Getting a context, returning a :class:`flask_onsei.context.Context` instance:

.. code-block:: python

    conv.contexts.get('some_ctx')

    # Or shorter via attribute access:
    conv.contexts.some_ctx

Setting a context:

.. code-block:: python

    # Setting an empty context with the default lifespan:
    conv.contexts.set('some_ctx')

    # Customizing the lifespan:
    conv.contexts.set('some_ctx', lifespan_count=3)

    # Including context parameters:
    conv.contexts.set('some_ctx', lifespan_count=3, some_param='some_value')

    # Initializing a complex context up front and setting it:
    from flask_onsei.context import Context
    ctx = Context(
        'some_ctx',
        lifespan_count=3,
        parameters={'foo': 'bar'}
    )
    conv.contexts.set(ctx)

Deleting a context still sends it back in the next response, but with a lifespan
of 0 to ensure that it gets deleted in Dialogflow:

.. code-block:: python

    conv.contexts.delete('some_ctx')

    # Or shorter:
    del conv.contexts.some_ctx

Often one would like to have guarantees about the state of certain contexts. It
is therefore possible to register contexts on the agent via
:meth:`.DialogflowAgent.register_context`.

Keeping a context around: This ensures that it never expires by resetting its
lifespan to a high value on each request. This happens before the conversation
is passed to the handler, so the handler can still delete the context manually:

.. code-block:: python

    agent.register_context('some_ctx', keep_around=True)

This does not create a context when it doesn't exist. For that use a default
factory, that initialized a context with the results of this factory as the
parameters when it is not part of the request:

.. code-block:: python

    # This context will be initialized with an empty parameters dict
    agent.register_context('some_ctx', default_factory=dict)

    # This context has some parameters already set
    agent.register_context(
        'some_other_ctx', default_factory=lambda: {'foo': 'bar'}
    )

Setting both ``keep_around`` and ``default_factory`` ensures that a context is
always present and ``conv.contexts.some_ctx`` never raises an AttributeError.

For complex contexts it is desirable to have the parameters attribute not be a
dictionary, but rather a class instances. This requires that the instance can
be serialized to JSON. Context can therefore be register with a serializer and
deserializer function. The result of the deserializer will be bound to the
parameters attribute when the conversation is initialized. After handling the
serializer will be used to convert the instance back to JSON. This makes it
possible to use arbitrary Python classes as contexts and hence attach business
logic to them.

To make this even easier there is an :class:`.DialogflowAgent.context` decorator
that can be used on :class:`.JSONType` subclasses. It will set the serializer,
deserializer and default_factory automatically (should the default_factory not
be needed it can be set to None). Here is an example of how this can be used
to implement a GameState context for a quiz game:

.. code-block:: python

    # Implement the game state class and schema
    from marshmallow.fields import Int, Str
    from flask_onsei.json import JSONType, JSONTypeSchema

    class _GameStateSchema(JSONTypeSchema):
        questions_answered = Int()
        last_answer = Str()

    @agent.context('game_state', keep_around=True)
    @dataclass
    class GameState(JSONType, schema=_GameStateSchema):
        questions_answered: int = 0
        last_answer: Optional[str] = None

This ensures that:
    * The ``game_state`` context will always be present.
    * It will be correctly initialized if necessary.
    * Its lifespan never expires.
    * The :attr:`.Context.parameters` are an instance of the GameState
      class, not a dict.

In a handler this context could be used like this:

.. code-block:: python

    @agent.handle('CorrectAnswer')
    def handle_correct_answer(conv):
        conv.contexts.game_state.parameters.questions_answered += 1
        conv.contexts.game_state.parameters.last_answer = ...
        return conv

Integrations
------------

Dialogflow is a generic Google Cloud API that can be integrated with a large
number of different platforms. The most well-known of the is Actions on Google
(i.e. the Google Assistant), others are Slack, Facebook Messenger and Telegram.
It is also possible to integrate Dialogflow with custom platforms such as
proprietary chat platforms or third party smart speakers.

flask_onsei supports all of these use cases. There is extensive support for
`Actions on Google`_ (see below), basic support for the other
integrations and tools to build helpers for custom integrations.

Integrations can send platform-specific data in the webhook request and receive
platform-specific responses in the webhook response, they essentially piggyback
on the Dialogflow webhook protocol. Because of this we give them each its own
conversation object that is accessible via the overall DialogflowConversation
object.

All integration conversations must subclass the
:class:`.AbstractIntegrationConversation`, which ensures that they can be
initialized from a request and rendered to a response. The default
implementation of this interface is :class:`.GenericIntegrationConversation`,
which behaves like a dict. This class is used for all integrations except
Actions on Google, which has a more elaborate class.

Dialogflow's `default integrations`_ are set up in the conversation by default.
This means that platform-specific responses can be included without further
setup, enabling multi-platform agents out of the box:

.. code-block:: python

    conv.facebook['foo'] = 'bar'  # Response only for Facebook
    conv.slack['bar'] = 'baz'     # This is for Slack

What kind of responses the platforms accept depends on them and has to be looked
up in their documentation.

.. _default integrations: https://cloud.google.com/dialogflow/docs/integrations/

It is also possible to register new integrations via
:class:`.DialogflowAgent.register_integration`. This is useful when the
Dialogflow API is used from a custom system that has additional features.
An example of this would be a custom smart speaker that has a blinking light
that can be controlled via parameters in the response payload. This would be a
case were it is useful to implement a custom conversation class to abstract
this functionality and to register it on the agent.

.. code-block:: python

    from flask_onsei.integrations import GenericIntegrationConversation

    class BlinkingLightSpeakerConv(GenericIntegrationConversation):
        # Subclass the generic conv to get the usual dict behavior

        def blink(times=1):
            # Build the JSON payload that makes the light blink
            self['blink'] = times

    agent.register_integration(
        source='blink_speaker',
        integration_conv_cls=BlinkingLightSpeakerConv
    )

Now, every DialogflowConversation passed to a handler will have an
instance of this special conversation object that can be used to make
the light blink:

.. code-block:: python

    @agent.handle('BlinkTwice')
    def blink_twice_handler(conv):
        conv.blink_speaker.blink(times=2)
        # ... other response parts as usual
        return conv

Should the speaker carry data when calling Dialogflow (via the
:attr:`.OriginaDetectIntentRequest.payload`), it can be made available via the
conversation class just like any other request attributes. Let's assume the
speaker would tell the webhook whether the light is currently on or off by
sending ``{'light_on': True}`` in the payload. The conversation class could then
make this info available like this:

.. code-block:: python

    from flask_onsei.integrations import GenericIntegrationConversation

    @agent.integration('blink_speaker')
    class BlinkingLightSpeakerConv(GenericIntegrationConversation):

        @property
        def light_on(self) -> bool:
            # The GenericIntegrationConversation is already a dict, we
            # simply expose this attribute as a property for
            # convenience
            return self['light_on']

        def turn_light_off(self):
            # Method to turn the light off (assuming the speaker
            # handles this)
            self['light_on'] = False

This can now be used in handler functions as well:

.. code-block:: python

    @agent.handle('TurnLightOff')
    def turn_light_off_handler(conv):
        if conv.blink_speaker.light_on:
            conv.blink_speaker.turn_light_off()
        return conv

Actions on Google
-----------------

Actions on Google (AoG) is the most important integration of Dialogflow, many
agents will probably never use another one. Because of this AoG has a fairly
elaborate conversation class that is available via ``conv.google``:
:class:`.V2ActionsOnGoogleDialogflowConversation`. This class should always be
used for AoG in favor of Dialogflow's generic responses, and when an agent is
only targeted for the Google Assistant it is perfectly fine to use it
exclusively.

Because it works just like the normal conversation, we only highlight the most
important features here, see the :doc:`API docs<api>` for a full reference.

AoG by default sends all responses as SSML. This means that templates can
contain SSML tags and just work:

.. code-block:: yaml

    welcome: Hi there! <audio src="https://some_jingle.mp3"/>

.. code-block:: python

    conv.google.tell(__('welcome'))  # Plays the jingle


AoG supports system intents that take over the conversation for a brief period
of time and obtain standardized information from the user. System intents are
implemented as methods on the AoG conversation object and are typically named
``ask_for_*``. for example:

.. code-block:: python

    # Ask for permission to get the users name
    conv.google.ask_for_permission('To greet you by name', 'NAME')

    # Ask for a confirmation
    conv.google.ask_for_confirmation('Do you really want to do this?')

    # Ask the user to link a third-party OAuth account
    conv.google.ask_for_sign_in('To access your Tinder account')

    # Ask for a selection from a list
    from flask_onsei.google_apis.actions_on_google_v2 import ListSelect
    list_select = ListSelect(...)  # Build the ListSelect
    conv.google.ask_for_list_selection(list_select)

The response to a system intent is usually included in the
``conv.google.inputs`` array of the next request. The precise format varies and
has to be looked up in the `AoG docs`_.

.. _AoG docs: https://developers.google.com/actions/assistant/helpers

AoG has a user_storage field that makes it possible to persist user information
server side across sessions (thereby differing from Dialogflow contexts,
which are always bound to a session). This field is available under
``conv.google.user.user_storage`` and makes use of the same serialization system
as the contexts. It is by default treated as a dict and de-/serialized with
json.loads/dumps, which means that all of its attributes must be
JSON-serializable.

Should a more elaborate system be needed, such as a custom user storage class,
it can be configured via the DialogflowAgents init params
(``aog_user_storage_deserializer``, ``aog_user_storage_serializer``,
``aog_user_storage_default_factory``). The behavior is the same as for the
contexts.


Testing
-------

The DialogflowAgent has a special :meth:`.DialogflowAgent.test_request` method
that can be used to quickly construct webhook requests and route them trough
the agent. The response will be a special :class:`.WebhookResponse` subclass
that makes it easy to make assertions about the response. For example:

.. code-block:: python

    # Call the Welcome intent
    resp = agent.test_request('Welcome')

    # Assert a text response
    assert 'Hi, welcome to SomeAgent!' in resp.text_responses()

    # Assert that a certain context is present
    assert resp.has_context('some_ctx)

    # Get the context to inspect it in more detail
    resp.context('some_ctx')

Note that the helper currently only support the generic Dialogflow responses,
the AoG response have to be inspected manually (``resp.payload['google']``).


Flask CLI and shell
-------------------

The agent adds a ``agent`` sub command to the `Flask CLI`_ that can be used to
quickly get information about the agent. It supports the following commands:

.. code-block:: bash

    $ flask agent intents
    # Prints a table with the registered intents and handlers

    $ flask agent contexts
    # Prints a table with the registered contexts

    $ flask agent integrations
    # Prints a table with the registered integration conversation classes

.. _Flask CLI: http://flask.pocoo.org/docs/1.0/cli/

The agent is also available in a ``flask shell`` under the ``agent`` name. This
in combination with :meth:`.DialogflowAgent.test_request` is the quickest way to
test the agent during development.

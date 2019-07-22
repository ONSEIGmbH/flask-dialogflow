.. _api:

API Reference
=============

This part of the documentation covers all the interfaces of flask_onsei.


Agent object
------------

The agent is the core object of this library.

.. autoclass:: flask_onsei.agent.DialogflowAgent
    :members:


Conversation objects
--------------------

Conversation classes are the core abstraction of this library. They come in two
versions for the two supported Dialogflow version, but are, except for some
additional features in v2beta1, completely identical.

.. autoclass:: flask_onsei.conversation.V2DialogflowConversation
    :members:

.. autoclass:: flask_onsei.conversation.V2beta1DialogflowConversation
    :members:


Contexts and Context Manager
----------------------------

Contexts are essential to manage (Dialogflow) server side state. These tools
help in doing that accurately.

.. autoclass:: flask_onsei.context.Context
    :members:

.. autoclass:: flask_onsei.context.ContextManager
    :members:


.. _integrations:

Integration Conversation objects
--------------------------------

`Dialogflow integrations`_ get their own conversation objects, which work like
the standard Dialogflow conversation object. They make it possible to include
platform-specific responses, even for new or completely custom platforms.
The default integration conversation is
:class:`.GenericIntegrationConversation`, which works like a dict. It is used
for all integrations that do not have a special conversation class registered.
Actions-on-Google has a custom conversation object that supports AoG's special
features. It is registered for AoG requests by default.

.. _Dialogflow integrations: https://cloud.google.com/dialogflow/docs/integrations/

.. autoclass:: flask_onsei.integrations.AbstractIntegrationConversation
    :members:

.. autoclass:: flask_onsei.integrations.GenericIntegrationConversation


Actions on Google Conversation object
-------------------------------------

Actions on Google is currently the only integration platform that has a custom
conversation class. It supports advanced AoG features such as additional rich
responses, system intents, permissions and user storage.

.. autoclass:: flask_onsei.integrations.actions_on_google.V2ActionsOnGoogleDialogflowConversation
    :members:

.. autoclass:: flask_onsei.integrations.actions_on_google.UserFacade
    :members:


.. _JSON handling:

JSON handling
-------------

Helpers for JSON de/serialization. This module, together with `marshmallow`_
powers the serialization and deserialization of the Google API objects to
native, idiomatic Python classes. This system is part of the public API and can
be used by users to implement custom context classes.

.. note:: By JSON, we always mean plain Python data structures that
    can be handled by :meth:`.json.dumps`/:meth:`.json.loads`, i.e. usually
    dictionaries. Pythons type system does unfortunately not allow recursive
    types, which is why we type JSON as ``MutableMapping[str, Any]``.

.. _marshmallow: https://marshmallow.readthedocs.io/en/3.0/index.html

.. autoclass:: flask_onsei.json.JSONType
    :members:

.. autoclass:: flask_onsei.json.JSONTypeSchema
    :members:

.. autoclass:: flask_onsei.json.ModuleLocalNested
    :members:


.. _templating:

Templating
----------

This library uses the same Jinja templating library as Flask, but with a custom
loader to support YAML files with many individual templates (since speech
responses tend to be very short). The loader also supports randomization to add
greater variability to speech responses.

.. autoclass:: flask_onsei.templating.YamlLoaderWithRandomization
    :members:


CLI interface
-------------

A special command group for `Flask's CLI interface`_. Adds an ``agent``
sub command to the ``flask`` command which gives access to certain information
about the current Dialogflow agent. See also ``flask agent --help``. The agent
itself is also available in a ``flask shell`` as ``agent``.

.. _Flask's CLI interface: http://flask.pocoo.org/docs/1.0/cli/

.. autofunction:: flask_onsei.cli.intents

.. autofunction:: flask_onsei.cli.contexts

.. autofunction:: flask_onsei.cli.integrations


Test helper
-----------

A few tools to make testing Dialogflow agents easier. The recommended way to
test Agents built with this library is the :meth:`.DialogflowAgent.test_request`
method, which simulates an end-to-end request through the agent. See also
`Testing Flask Applications`_ for more tips.

.. _Testing Flask Applications: http://flask.pocoo.org/docs/1.0/testing/

.. autofunction:: flask_onsei.agent.build_webhook_request

.. autoclass:: flask_onsei.agent.TestWebhookResponse
    :members:



.. ONSEI_Google documentation master file, created by
   sphinx-quickstart on Sat Jun 29 18:55:09 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to ONSEI_Google!
========================

ONSEI_Google is a Flask extension to build `Dialogflow`_ agents. It aims to
shine through the following features:

    * A familiar Flask extension structure that handles the mundane stuff behind
      the scenes
    * Robust JSON serialization and deserialization of the entire Dialogflow and
      Actions on Google API to native Python classes
    * A simple API for high-level Google Assistant features
    * Special template features for voice assistants
    * Support for multi-platform agents and extensibility to new platforms
    * Integration with the Flask CLI and shell
    * Helpers to test an agent
    * A comprehensive test suite

.. _Dialogflow: https://dialogflow.com/

Here is a quick example:

.. code-block:: python

   from flask import Flask
   from onsei_google.agent import DialogflowAgent

   app = Flask(__name__)
   agent = DialogflowAgent(app)

   @agent.handle(intent='HelloWorld')
   def hello_world(conv):
      conv.ask('Hello world!')
      return conv

For more information, check out the :doc:`Tutorial<tutorial>` and the
:doc:`API documentation<api>`.

.. toctree::
   :maxdepth: 2

   tutorial
   api
   changelog



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

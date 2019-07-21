# HelloONSEI sample agent

This is a very simple sample agent for Dialogflow + Actions-on-Google. It aims to
show the general architecture of an agent build with the ONSEI_Google library.
It can be deployed to Dialogflow an run by executing the `helloonsei.py` script.
It supports the Default Welcome and a small number of custom intents:

```text
USER: Mit Hello ONSEI sprechen.
AGENT: Hallo ONSEI!

USER: Welcher Tag ist heute?
AGENT: Heute ist der X.Y.

USER: Zeige mir ein Berlin-Bild!
AGENT: Hier ist ein Bild aus Berlin [+ BasicCard]
```

The documentation expects the user to be familiar with the general structure of
Dialogflow/AoG fulfillement webhooks. These links can be helpful to look up individual
attributes of the request and response classes:

* The [Dialogflow API V2 REST reference](https://dialogflow.com/docs/reference/api-v2/rest):
This reference contains the types of which WebhookRequests and WebhookResponses
are made of, and (most of) which are implemented in the
`onsei_google.google_types.dialogflow` module.
* The [Actions on Google Conversation Webhook reference](https://developers.google.com/actions/build/json/conversation-webhook-json):
This reference contains the types for AoG Conversation Webhook requests and responses.
The separate Dialogflow Webhook is most a thin wrapper around these types, most of them
are implemented in the `onsei_google.google_types.actions_on_google` module.
* The [Actions on Google Dialogflow Webhook reference](https://developers.google.com/actions/build/json/dialogflow-webhook-json):
This is the reference by which AoG communicates with Dialogflow. Is is for the most part
only a thin wrapper around the Conversation Webhook, and shares it's types.

This example is deliberately kept simple and does not demonstrate all of the libraries
features. More complicated uses cases can be found in the Bringmeister repo, for which
this was originally written.

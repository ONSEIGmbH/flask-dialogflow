# -*- coding: utf-8 -*-
"""
    conftest
    ~~~~~~~

    :copyright: (c) 2018 ONSEI GmbH
    :license: Proprietary
"""

import json
from pathlib import Path

import pytest
from flask import Flask

from flask_dialogflow.agent import (
    DialogflowAgent, DialogflowConversation, DIALOGFLOW_VERSIONS
)

TEST_RESOURCES = Path(__file__).parent / 'test_resources'


@pytest.fixture(
    params=(TEST_RESOURCES / 'aog_webhook_requests').glob('*.json')
)
def aog_webhook_request(request):
    with open(request.param, encoding='utf8') as f:
        yield json.load(f)


@pytest.fixture
def aog_payload(aog_webhook_request):
    return aog_webhook_request['originalDetectIntentRequest']['payload']


@pytest.fixture
def templates_file(tmpdir):
    templates_file = tmpdir / 'templates.yaml'
    with open(templates_file, 'w') as f:
        f.write("""
        simple_tmpl: Hello world

        list_tmpl:
            - option a
            - option b
            - option c

        weighted_tmpl:
            - [option x, 1]
            - [option y, 5]
            - [option z, 10]

        complex_weighted_tmpl:
            - option x
            - [option y, 3]
            -
                - >
                    option z
                    break
                - 5

        invalid_tmpl:
            - option a
            - [option a, option b, 3]  # Should have quoted this string!
        """)
    return templates_file


@pytest.fixture
def app():
    return Flask(__name__)


@pytest.fixture(params=DIALOGFLOW_VERSIONS)
def agent(templates_file, request):
    agent = DialogflowAgent(
        templates_file=templates_file, version=request.param
    )

    @agent.handle('Test')
    def handler(conv: DialogflowConversation) -> DialogflowConversation:
        return conv

    return agent

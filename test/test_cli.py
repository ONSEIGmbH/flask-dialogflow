# -*- coding: utf-8 -*-
"""
    test_cli
    ~~~~~~~

    :copyright: (c) 2018 ONSEI GmbH
    :license: Proprietary
"""
from flask_dialogflow.cli import intents, contexts, integrations

import pytest


@pytest.fixture
def runner(app, agent):
    agent.init_app(app)
    return app.test_cli_runner()


def test_intents_cmd(runner):
    res = runner.invoke(intents)
    assert 'Test' in res.output


def test_contexts_cmd(runner):
    res = runner.invoke(contexts)
    assert 'Name' in res.output


def test_integrations_cmd(runner):
    res = runner.invoke(integrations)
    assert 'google' in res.output

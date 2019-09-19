# -*- coding: utf-8 -*-
"""
    test_utils
    ~~~~~~~

    :copyright: (c) 2018 ONSEI GmbH
    :license: Proprietary
"""
import pytest

from flask_dialogflow.agent import build_webhook_request
from flask_dialogflow.google_apis.actions_on_google_v2 import User
from flask_dialogflow.utils import fqn


@pytest.mark.parametrize('obj, expected', [
    (User, 'flask_dialogflow.google_apis.actions_on_google_v2.User'),
    (User.from_json, 'flask_dialogflow.json.JSONType.from_json'),
    (build_webhook_request, 'flask_dialogflow.agent.build_webhook_request'),
])
def test_fqn(obj, expected):
    assert fqn(obj) == expected

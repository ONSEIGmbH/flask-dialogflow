# -*- coding: utf-8 -*-
"""
    test_utils
    ~~~~~~~

    :copyright: (c) 2018 ONSEI GmbH
    :license: Proprietary
"""
import pytest

from flask_onsei.agent import build_webhook_request
from flask_onsei.google_apis.actions_on_google_v2 import User
from flask_onsei.utils import fqn


@pytest.mark.parametrize('obj, expected', [
    (User, 'flask_onsei.google_apis.actions_on_google_v2.User'),
    (User.from_json, 'flask_onsei.json.JSONType.from_json'),
    (build_webhook_request, 'flask_onsei.agent.build_webhook_request'),
])
def test_fqn(obj, expected):
    assert fqn(obj) == expected

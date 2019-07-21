# -*- coding: utf-8 -*-
"""
    test_utils
    ~~~~~~~

    :copyright: (c) 2018 ONSEI GmbH
    :license: Proprietary
"""
import pytest

from onsei_google.agent import build_webhook_request
from onsei_google.google_apis.actions_on_google_v2 import User
from onsei_google.utils import fqn


@pytest.mark.parametrize('obj, expected', [
    (User, 'onsei_google.google_apis.actions_on_google_v2.User'),
    (User.from_json, 'onsei_google.json.JSONType.from_json'),
    (build_webhook_request, 'onsei_google.agent.build_webhook_request'),
])
def test_fqn(obj, expected):
    assert fqn(obj) == expected

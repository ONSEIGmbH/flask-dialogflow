# -*- coding: utf-8 -*-
"""
    test_templating
    ~~~~~~~

    :copyright: (c) 2018 ONSEI GmbH
    :license: Proprietary
"""
from functools import partial
from random import Random
from unittest.mock import Mock

import pytest
from jinja2 import Environment, TemplateError, TemplateNotFound

from flask_dialogflow.templating import YamlLoaderWithRandomization


@pytest.fixture
def env() -> Environment:
    return Environment()


@pytest.fixture
def loader(templates_file) -> YamlLoaderWithRandomization:
    return YamlLoaderWithRandomization(templates_file)


class TestYamlLoaderWithRandomization:

    def test_path(self, loader):
        assert loader.path.basename == 'templates.yaml'

    def test_get_source_with_simple_template(self, env, loader):
        source, *_ = loader.get_source(env, 'simple_tmpl')
        assert source == 'Hello world'

    def test_get_source_with_list_template(self, env, loader):
        source, *_ = loader.get_source(env, 'list_tmpl')
        assert 'option' in source

    def test_get_source_with_weighted_template(self, env, loader):
        source, *_ = loader.get_source(env, 'weighted_tmpl')
        assert 'option' in source

    def test_get_source_filename(self, env, loader):
        _, filename, __ = loader.get_source(env, 'simple_tmpl')
        assert filename == loader.path

    def test_get_source_uptodate(self, env, loader):
        *_, uptodate = loader.get_source(env, 'simple_tmpl')
        assert callable(uptodate)
        assert uptodate() is False

    def test_random_list_choice(self, loader):
        rand = Random(42)
        assert loader._get_randomized_source('list_tmpl', rand) == 'option b'
        assert loader._get_randomized_source('list_tmpl', rand) == 'option a'
        assert loader._get_randomized_source('list_tmpl', rand) == 'option a'

    def test_random_weighted_choice(self, loader):
        rand = Random(42)
        tmpl = 'weighted_tmpl'
        assert loader._get_randomized_source(tmpl, rand) == 'option z'
        assert loader._get_randomized_source(tmpl, rand) == 'option x'
        assert loader._get_randomized_source(tmpl, rand) == 'option y'

    def test_random_weighted_choice_with_complex_template(self, loader):
        rand = Random(42)
        tmpl = 'complex_weighted_tmpl'
        assert loader._get_randomized_source(tmpl, rand) == 'option z break\n'
        assert loader._get_randomized_source(tmpl, rand) == 'option x'
        assert loader._get_randomized_source(tmpl, rand) == 'option y'

    def test_random_list_choice_with_env_caching(self, env, loader):
        loader._get_randomized_source = partial(
            loader._get_randomized_source, rand=Random(42)
        )
        env.loader = loader
        assert env.get_template('list_tmpl').render() == 'option b'
        assert env.get_template('list_tmpl').render() == 'option a'
        assert env.get_template('list_tmpl').render() == 'option a'

    def test_random_weighted_choice_with_env_caching(self, env, loader):
        loader._get_randomized_source = partial(
            loader._get_randomized_source, rand=Random(42)
        )
        env.loader = loader
        tmpl = 'weighted_tmpl'
        assert env.get_template(tmpl).render() == 'option z'
        assert env.get_template(tmpl).render() == 'option x'
        assert env.get_template(tmpl).render() == 'option y'

    def test_reload_mapping_when_should_update(self, env, loader, monkeypatch):
        monkeypatch.setattr(loader.__class__, '_should_reload', True)
        reload_mock = Mock()
        monkeypatch.setattr(loader, '_reload_mapping', reload_mock)
        _ = loader.get_source(env, 'simple_tmpl')
        reload_mock.assert_called_once()

    def test_dont_reload_mapping_when_when_not_should_update(
        self, env, loader, monkeypatch
    ):
        monkeypatch.setattr(loader.__class__, '_should_reload', False)
        reload_mock = Mock()
        monkeypatch.setattr(loader, '_reload_mapping', reload_mock)
        _ = loader.get_source(env, 'simple_tmpl')
        reload_mock.assert_not_called()

    def test_TemplateNotFound_error(self, env, loader):
        with pytest.raises(TemplateNotFound):
            loader.get_source(env, 'foobar')

    def test_list_templates(self, loader):
        rv = loader.list_templates()
        assert hasattr(rv, '__iter__')
        assert len(list(rv)) == len(loader.mapping)
        assert all(isinstance(tmpl, str) for tmpl in rv)


def test_validate_randomizable_template(env, loader):
    with pytest.raises(TemplateError):
        loader.get_source(env, 'invalid_tmpl')

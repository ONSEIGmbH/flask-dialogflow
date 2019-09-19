# -*- coding: utf-8 -*-
"""
    flask_dialogflow.templating
    ~~~~~~~~~~~~~~~~~~~~~~~

    Tools to support templating with Jinja2.

    :copyright: (c) 2018 ONSEI GmbH
    :license: Proprietary
"""

import os
import random
from typing import Callable, Tuple, Optional, List, Union, Iterable

import yaml
from jinja2 import BaseLoader, TemplateNotFound, Environment, TemplateError


class YamlLoaderWithRandomization(BaseLoader):
    """A simple template loader for YAML files that supports randomization.

    This template loader loads all templates from a single, flat YAML file. The
    file is loaded once during initialization and then only reloaded when a
    change is detected.

    It supports randomization in that if the template is an array it selects
    one of the arrays elements at random. This can be used to add variability
    to templates within the same context. The array elements can also be
    2-element arrays themselves, were the second element is a number. This
    number will be used to weigh the random choice. Elements without weight
    default to 1.

    Examples:

    .. code-block:: yaml

        simple_template: Hello world!

        # A list template: All variants have equal probability (i.e. 50% here)
        random_template:
          - Hi there, this is the first variant!
          - And this is the second variant.

        # Template with weights, default value is 1
        weighted_template:
          - ['This is the first variant.', 0.5]     # ~14% prob. (0.5/3.5)
          - This is the second variant.             # ~29% prob. (1/3.5)
          - ['And this is the third variant.', 2]   # ~57% prob. (2/3.5)

        # NOT allowed: Nested templates
        outer_template:
          inner_template:
            - This would be the actual text (if it were allowed)!

    Note that for randomization to work ``auto_reload`` has to be enabled on
    the Jinja environment. Otherwise the env will cache the templates
    internally and not call this loader. The loader itself will select a random
    version of each template every time it is called, see :meth:`.get_source`
    for details.

    Args:
        path: The path to the templates YAML file.
    """

    def __init__(self, path: str):
        self.path = path
        self.mapping = {}
        self._reload_mapping()

    @property
    def _should_reload(self) -> bool:
        """True when file modified since last loading."""
        return self.last_mtime != os.path.getmtime(self.path)

    def _reload_mapping(self):
        """Reload the YAML file and store the last mtime."""
        self.last_mtime = os.path.getmtime(self.path)
        with open(self.path, encoding='utf8') as f:
            self.mapping = yaml.safe_load(f.read())

    def get_source(
        self, environment: Environment, name: str
    ) -> Tuple[str, str, Callable[[], bool]]:
        """Get a template source.

        Expects the template to be a key from the YAML file and looks it up in
        the cached mapping, reloading it beforehand if the file was modified.
        The uptodate callback returned as the third param always returns false
        to force the environment to call this function every time and thus
        trigger the random selection again. This in combination with the
        auto_reload setting on the Jinja environment is necessary to make
        randomization work.

        Args:
            environment: The
                :class:`Environment<jinja2.environment.Environment>`
                to load the template from.
            name: A key from the YAML templates file.

        Returns:
            The same (source, filename, uptodate) tuple as the BaseLoader.

        Raises:
            TemplateNotFound: When the template name is not in the file.
            TemplateError: When the template files format is invalid (usually
                because of misquoted strings).
        """
        if self._should_reload:
            self._reload_mapping()
        source = self._get_randomized_source(name)
        return source, self.path, lambda: False

    def _get_randomized_source(
        self, name: str, rand: Optional[random.Random] = None
    ) -> str:
        """Get the template source, handle necessary randomization."""
        try:
            source = self.mapping[name]
        except KeyError:
            raise TemplateNotFound(name)
        if isinstance(source, list):
            _validate_randomizable_source(name, source)
            values = [s[0] if isinstance(s, list) else s for s in source]
            weights = [s[1] if isinstance(s, list) else 1 for s in source]
            if rand is None:
                rand = random.Random()
            source = rand.choices(values, weights)[0]
        return source

    def list_templates(self) -> Iterable[str]:
        """List the templates of this loader.

        Returns:
            An iterable of template names.
        """
        return sorted(self.mapping)


def _validate_randomizable_source(
        name: str, source: Union[str, List[Union[str, int, float]]]
) -> None:
    """Validate that a randomizable template source has the proper format.

    Raises a TemplateError when one of the items of a list source has an
    invalid format, which can easily happen when one forgets to quote a complex
    string.
    """
    for val in source:
        if not isinstance(val, str):
            if not (
                isinstance(val, list)
                and len(val) == 2
                and isinstance(val[1], (int, float))
            ):
                raise TemplateError(
                    f'Invalid format on randomizable template {name}. The '
                    f'individual items of a randomizable template must be '
                    f'strings or 2-item lists, where the second item is a '
                    f'number. Perhaps you forgot to enclose a complex string '
                    f'in quotes?'
                )

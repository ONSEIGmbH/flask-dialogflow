# -*- coding: utf-8 -*-
"""
    utils
    ~~~~~~~

    :copyright: (c) 2018 ONSEI GmbH
    :license: Proprietary
"""
from typing import Union, Type, Callable


def fqn(obj: Union[Type, Callable]) -> str:
    """Return the fully qualified name of an object, str() as fallback."""
    module = obj.__module__ + '.' if hasattr(obj, '__module__') else ''
    name = obj.__qualname__ if hasattr(obj, '__qualname__') else str(obj)
    return module + name

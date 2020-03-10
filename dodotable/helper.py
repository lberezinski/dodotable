# -*- coding: utf-8 -*-
""":mod:`dodotable.helper` --- helper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from .condition import SelectFilter
from .schema import Queryable, Renderable, Schema
from .util import camel_to_underscore


__all__ = '_Helper', 'Limit', 'Category',


class _Helper(Schema):
    pass


class Limit(_Helper, Renderable, Queryable):
    """Operate `` limit '' in querystring to get 100 functions
    provide.

    """

    def __init__(self, table, request_args, identifier=None):
        self.table = table
        self.request_args = request_args
        if not identifier:
            identifier = camel_to_underscore(table.cls.__name__)
        self.arg_type_name = 'limit_{}'.format(identifier)

    def __query__(self):
        pass

    def __html__(self):
        return self.render('limit.html', filter=self)


class Category(_Helper, SelectFilter):
    """``select`` Not a filter that is rendered as a tag
    Provides a filter that is rendered in category format..

    """

    def __html__(self):
        return self.render('category.html', filter=self)


def monkey_patch_environment(environ):
    modules = 'dodotable.schema', 'dodotable.condition', 'dodotable.helper'
    e = environ()
    for module_name in modules:
        module = __import__(module_name, globals(), locals(), ['*'], -1)
        for attr in dir(module):
            try:
                getattr(module, attr).environment = e
            except AttributeError:
                continue

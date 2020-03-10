# -*- coding: utf-8 -*-
""":mod:`dodotable.util` --- utilities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import codecs
import gettext
import numbers
import re

from jinja2 import Environment, PackageLoader
from six import PY2, text_type


__all__ = (
    'camel_to_underscore', 'render', '_get_data',
    'string_literal',
)


#: (:class:`_sre.SRE_Pattern`) Find the first capital letter..
first_cap_re = re.compile('(.)([A-Z][a-z]+)')
#: (:class:`_sre.SRE_Pattern`) Find all capital letters that are not first in a word.
all_cap_re = re.compile('([a-z0-9])([A-Z])')


def camel_to_underscore(name):
    """CamelCase Given by ``name`` of underscore_with_lower_case Convert to

    .. code-block:: python

       >>> camel_to_underscore('SomePythonClass')
       'some_python_class'

    :param str name: name to convert
    :return: converted name
    :rtype: :class:`str`

    """
    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()


def render(template_name, extra_environments=None, **kwargs):
    """Render the given template with jinja

    :param template_name:
    :return:

    """
    if extra_environments is None:
        extra_environments = {}
    default_loader = PackageLoader('dodotable', 'templates')
    loader = extra_environments.get(
        'template_loader',
        default_loader)
    if not loader:
        loader = default_loader
    get_translations = extra_environments.get('get_translations')
    env = Environment(loader=loader,
                      extensions=['jinja2.ext.i18n', 'jinja2.ext.with_'],
                      autoescape=True)
    env.globals.update(extra_environments)
    translations = get_translations() if callable(get_translations) else None
    if translations is None:
        translations = gettext.NullTranslations()
    env.install_gettext_translations(translations)
    template = env.get_template(template_name)
    return template.render(**kwargs)


def _get_data(data, attribute_name, default):
    name_chain = attribute_name.split('.')

    def __data__(_data, name_chain):
        if len(name_chain) > 0:
            try:
                return __data__(getattr(_data, name_chain[0]),
                                name_chain[1:])
            except AttributeError:
                return default
        return _data

    return __data__(data, name_chain)


if PY2:
    def to_str(x):
        if isinstance(x, text_type):
            return x
        if isinstance(x, numbers.Number):
            x = str(x)
        elif x is None:
            x = ''
        return codecs.unicode_escape_decode(x)[0]
    string_literal = to_str
else:
    string_literal = str

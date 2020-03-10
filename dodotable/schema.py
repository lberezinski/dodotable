# -*- coding: utf-8 -*-
""":mod:`dodotable.schema` --- table schema
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from __future__ import absolute_import

import collections
try:
    from collections.abc import MutableSequence
except ImportError:
    from collections import MutableSequence
import math

from sqlalchemy.orm import Query

from .environment.flask import FlaskEnvironment
from .util import render, string_literal, _get_data

from pprint import pprint

__all__ = (
    'Cell', 'Column', 'LinkedColumn', 'ObjectColumn', 'ENVIRONMENT',
    'Queryable', 'Renderable', 'Row', 'Table', 'Pager', 'Schema',
)


ENVIRONMENT = FlaskEnvironment()


class Schema(object):
    """

    :param environment:
    :type environment: :class:`~.environment.Environment`

    """

    environment = ENVIRONMENT

    def render(self, template_name, **kwargs):
        return render(template_name,
                      extra_environments=self.environment.__dict__(),
                      **kwargs)


class Renderable(object):
    """jinja The parent class of the class that is rendered directly from

    jinja In `` __html__ '' to render
    :class:`~Renderable` Inheriting: meth: `~ Renderable .__ html__`
    If you implement, you can render right away.

    .. code-block:: python

       class SomeElem(Renderable):

           def __html__(self):
                return "<h1>Hello World</h1>"

    .. code-block:: jinja

       {{ SomeElem() }} <!-- == <h1>Hello World</h1> -->

    """

    def __html__(self):
        """:mod:`jinja` Function for internal calls

        .. note::

           Nowadays, implementing: func: `__html__` is called de facto of an HTML spit object.

        """
        raise NotImplementedError('__html__ not implemented yet.')


class Queryable(object):
    """:class:`~sqlalchemy.orm.query.Query` Convertible to

    All fields that spawn queries inherit from: class: `~ Queryable`
    Implement: meth: `~ Queryable .__ query__` to use as a sqlalchemy query
    You need to convert

    """

    def __query__(self):
        """The method that every: class: `~ dodotable.Queryable` object must implement."""
        raise NotImplementedError('__query__ not implemented yet.')


class Cell(Schema, Renderable):
    """A class representing a table cell

    : param int col: column position
    : param int row: row position
    : param data: the data to be filled in the cell
    """

    def __init__(self, col, row, data, _repr=string_literal, classes=()):
        self.col = col
        self.row = row
        self.data = data
        self.repr = _repr
        self.classes = classes

    def __html__(self):
        return self.render('cell.html', cell=self)


class LinkedCell(Cell):
    """Cell Linked to Content

    : param int col: column position
    : param int row: row position
    : param data: the data to be filled in the cell
    : param endpoint: The url to go to when you press data

    """

    def __init__(self, col, row, data, endpoint):
        self.col = col
        self.row = row
        self.data = data
        self.url = endpoint

    def __html__(self):
        return self.render('linkedcell.html', cell=self)


class Column(Schema, Renderable):
    """A class representing a table column

    : param str label: column label
    : param str attr: Attribute name to import
    : param list order_by: Sort by
    : param list filters: Sort by
    : param function _repr: The format to be shown
    param bool sortable
    : param bool visible: Whether the column is visible in the table.
                         Even if the value is False
                         : class: `~ dodotable.condition.IlikeSet`
                         As it is seen, we can use for search.

    """

    def __init__(self, label, attr, order_by=(), filters=None,
                 _repr=string_literal, sortable=True, visible=True,
                 editable=False,classes=()):
        from .condition import Order
        if filters is None:
            filters = []
        self.label = label
        self.attr = attr
        self.filters = filters
        self.order_by = Order.of_column(attr, order_by)
        self._repr = _repr
        self.sortable = sortable
        self.visible = visible
        self.editable = editable
        self.classes = classes

    def add_filter(self, filter):
        self.filters.append(filter)

    def __cell__(self, col, row, data, attribute_name, default=None):
        """Convert the column's data to: class: `~ dodotable.Cell`.

        :param col:
        :param row:
        :param data:
        :param attribute_name:
        :param default:
        :return:
        """
        return Cell(col=col, row=row,
                    data=_get_data(data, attribute_name, default),
                    _repr=self._repr,
                    classes=self.classes)

    def __html__(self):
        return self.render('column.html', column=self)


class LinkedColumn(Column):
    """The class representing the column to which the link should go

    : param str label: column label
    : param str attr: Attribute name to import
    param str or function endpoint
    : param list order_by: Sort by

    """

    def __init__(self, *args, **kwargs):
        self.endpoint = kwargs.pop('endpoint')
        super(LinkedColumn, self).__init__(*args, **kwargs)

    def __cell__(self, col, row, data, attribute_name, default=None):
        endpoint = self.endpoint(data) if callable(
            self.endpoint) else self.endpoint
        return LinkedCell(col=col, row=row,
                          data=_get_data(data, attribute_name, default),
                          endpoint=endpoint)


class ObjectColumn(Column):
    """Get __cell_.data as result instead of attribute."""

    def __cell__(self, col, row, data, attribute_name, default=None):
        return Cell(col=col, row=row,
                    data=data if data else default,
                    _repr=self._repr,
                    classes=self.classes)


class HiddenColumn(Column):
    """Invisible heat"""

    def __init__(self, *args, **kwargs):
        super(HiddenColumn, self).__init__(*args, **kwargs)
        self.visible = False


class Row(Schema, MutableSequence, Renderable):
    """A class representing a row in a table """

    def __init__(self):
        self._row = []

    def __delitem__(self, key):
        del self._row[key]

    def __getitem__(self, item):
        return self._row[item]

    def __setitem__(self, key, value):
        self._row[key] = value

    def __len__(self):
        return len(self._row)

    def insert(self, index, object_):
        self._row.insert(index, object_)

    def append(self, cell):
        """행에 cell을 붙입니다. """
        assert isinstance(cell, Cell)
        super(Row, self).append(cell)

    def __html__(self):
        return self.render('row.html', row=self)


class Pager(Schema, Renderable):

    DEFAULT_LIMIT = 10

    DEFAULT_OFFSET = 0

    Page = collections.namedtuple('Page',
                                  ['selected', 'number', 'limit', 'offset'])

    def __init__(self, limit, offset, count, padding=10):
        try:
            self.limit = int(limit)
            self.offset = int(offset)
            self.count = int(count)
            self.padding = int(padding)
        except ValueError:
            self.limit = 10
            self.offset = 0
            self.count = 0
            self.padding = 10

    def from_page_number(self, number):
        return self.Page(limit=self.limit, offset=(number - 1) * self.limit,
                         selected=False, number=number)

    @property
    def pages(self):
        page_count = int(math.ceil(self.count / float(self.limit)))
        current_page_count = (self.offset // self.limit) + 1
        pages = []
        s = (current_page_count - 1) // self.padding
        start = s * 10 + 1
        for page in self.range(start,
                               start + self.padding - 1,
                               max_=page_count):
            selected = False
            if page == current_page_count:
                selected = True
            p = self.Page(selected=selected, number=page, limit=self.limit,
                          offset=self.limit * (page - 1))
            pages.append(p)
        return pages

    def range(self, start, end, max_, min_=1):
        i = start
        yield min_
        while i <= end and i <= max_:
            if i > min_:
                yield i
            i += 1
        if i < max_:
            yield max_

    def __html__(self):
        return self.render('pager.html', pager=self)


class Table(Schema, Queryable, Renderable):
    """The frame of the table representing the data

    :param cls:
    :param label:
    :param columns:
    :param sqlalchemy_session:

    """

    def __init__(self, cls, label, unit_label="row",
                 columns=None,
                 sqlalchemy_session=None):
        self.cls = cls
        self.label = label
        self.unit_label = unit_label
        self._filters = []
        self.rows = []
        if columns is None:
            self._columns = []
        else:
            self._columns = columns
        self._count = None
        self.session = sqlalchemy_session
        try:
            if sqlalchemy_session is None:
                self.session = self.environment.get_session()
        finally:
            if not self.session:
                raise ValueError("{0.__class__.__name__}.session "
                                 "can't be None".format(self))
        self.pager = Pager(limit=1, offset=0, count=0)
        self.pager.environment = self.environment

    def select(self, offset=Pager.DEFAULT_OFFSET, limit=Pager.DEFAULT_LIMIT):
        self.rows = []
        # print ("query {}".format(vars(self.query)))
        q = self.query.offset(offset).limit(limit)
        for i, row in enumerate(q):
            # pprint(vars(row))

            t2 = row._sa_instance_state.class_.__table__
            pprint (vars(t2))
            print()
            
            for c2 in t2.columns:
                # pprint (vars(c2) )
                print (c2.key)
                print (c2.nullable)
                print (c2.primary_key)
                print (c2.default)
           
            _row = Row()
            for j, col in enumerate(self.columns):
                pprint(vars(col))
                _row.append(
                    col.__cell__(col=j, row=i, data=row,
                                 attribute_name=col.attr)
                )
                pprint(default)
            self.rows.append(_row)
        self.pager = Pager(limit=limit, offset=offset,
                           count=self.count)
        self.pager.environment = self.environment
        return self

    def add_filter(self, filter):
        self._filters.append(filter)

    @property
    def _order_queries(self):
        """Get the sort criteria of the query."""
        from .condition import Order
        order = []
        for column in self.columns:
            if column.order_by:
                o = Order(self.cls, column.attr, column.order_by)
                order.append(o.__query__())
        if not order:
            k = self.columns[0].attr
            o = Order(self.cls, k)
            self.columns[0].order_by = o.order
            order.append(o.__query__())
        return order

    @property
    def _filter_queries(self):
        for filter in self._filters:
            if filter:
                yield filter.__query__()

    @property
    def count(self):
        return self.build_base_query().count()

    def build_base_query(self):
        if isinstance(self.cls, Query):
            query = self.cls
        else:
            query = self.session.query(self.cls)
        for filter in self._filter_queries:
            if filter is not None:
                query = query.filter(filter)
        return query

    @property
    def query(self):
        """Create a query.

        :return:
        """
        query = self.build_base_query().order_by(*self._order_queries)
        return query

    @property
    def columns(self):
        return [column for column in self._columns if column.visible]

    def __html__(self):
        return self.render('table.html', table=self)

    def __query__(self):
        return self.query

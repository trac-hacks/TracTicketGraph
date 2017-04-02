#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Colin Snover
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import datetime
import math
import pkg_resources

from trac.core import Component, implements
from trac.perm import IPermissionRequestor
from trac.ticket import model
from trac.util.datefmt import to_datetime, to_utimestamp, user_time, utc
from trac.util.html import html
from trac.util.translation import _
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider, \
                            add_script, add_script_data

MILLISECONDS_PER_DAY = 24 * 60 * 60 * 1000L
MICROSECONDS_PER_DAY = MILLISECONDS_PER_DAY * 1000


class TicketGraphModule(Component):

    implements(INavigationContributor, IPermissionRequestor, IRequestHandler,
               ITemplateProvider)

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['TICKET_GRAPH']

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'ticketgraph'

    def get_navigation_items(self, req):
        if 'TICKET_GRAPH' in req.perm:
            yield ('mainnav', 'ticketgraph',
                   html.a(_("Ticket Graph"), href=req.href.ticketgraph()))

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return [('ticketgraph',
                 pkg_resources.resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return [pkg_resources.resource_filename(__name__, 'templates')]

    # IRequestHandler methods

    def match_request(self, req):
        return req.path_info == '/ticketgraph'

    def process_request(self, req):
        req.perm.require('TICKET_GRAPH')

        days_back = int(req.args.get('days', 90))
        component = req.args.get('component', '')

        today = datetime.datetime.now(utc)
        ts_start = to_utimestamp(today - datetime.timedelta(days=days_back))
        ts_end = to_utimestamp(today)

        series = {
            'openedTickets': {},
            'closedTickets': {},
            'reopenedTickets': {},
            'openTickets': {}
        }

        components = [c.name for c in model.Component.select(self.env)]
        if component not in components:
            component = ''

        with self.env.db_query as db:
            component_clause = "AND t.component='%s'" % component \
                               if component else ""
            # number of created tickets in time period, grouped by day (ms)
            for tid, timestamp, in db("""
                    SELECT id, time FROM ticket t
                    WHERE t.time BETWEEN %%s AND %%s %s
                    ORDER BY t.time ASC
                    """ % component_clause, (ts_start, ts_end)):
                date_ = localize_and_truncate(req, timestamp)
                series['openedTickets'].setdefault(date_, 0)
                series['openedTickets'][date_] += 1

            # number of reopened tickets in time period, grouped by day (ms)
            for tid, timestamp in db("""
                    SELECT DISTINCT tc.ticket, tc.time FROM ticket_change tc
                     INNER JOIN ticket t ON tc.ticket = t.id
                    WHERE field='status' AND newvalue='reopened'
                     AND tc.time BETWEEN %%s AND %%s %s
                    ORDER BY tc.time ASC
                    """ % component_clause, (ts_start, ts_end)):
                date_ = localize_and_truncate(req, timestamp)
                series['reopenedTickets'].setdefault(date_, 0)
                series['reopenedTickets'][date_] += 1

            # number of closed tickets in time period, grouped by day (ms)
            for count, timestamp in db("""
                    SELECT DISTINCT tc.ticket, tc.time FROM ticket_change tc
                     INNER JOIN ticket t ON tc.ticket = t.id
                    WHERE field='status' AND newvalue='closed'
                     AND tc.time BETWEEN %%s AND %%s %s
                    ORDER BY tc.time ASC
                    """ % component_clause, (ts_start, ts_end)):
                date_ = localize_and_truncate(req, timestamp)
                series['closedTickets'].setdefault(date_, 0)
                series['closedTickets'][date_] -= 1

            # number of open tickets at end of the reporting period
            open_tickets = 0
            for open_tickets, in db("""
                    SELECT COUNT(*) FROM ticket t
                    WHERE status!='closed' %s
                    """ % component_clause):
                break

        open_ts = localize_and_truncate(req, ts_end)
        while open_ts >= localize_and_truncate(req, ts_start):
            if open_ts in series['closedTickets']:
                open_tickets -= series['closedTickets'][open_ts]
            if open_ts in series['openedTickets']:
                open_tickets -= series['openedTickets'][open_ts]
            if open_ts in series['reopenedTickets']:
                open_tickets -= series['reopenedTickets'][open_ts]

            series['openTickets'][open_ts] = open_tickets
            open_ts -= MILLISECONDS_PER_DAY

        data = {}
        for i in series:
            data[i] = [(k, series[i][k]) for k in sorted(series[i].keys())]

        add_script(req, 'ticketgraph/jquery.flot.min.js')
        add_script(req, 'ticketgraph/jquery.flot.stack.min.js')
        add_script(req, 'ticketgraph/jquery.flot.time.min.js')
        add_script(req, 'ticketgraph/ticketgraph.js')
        add_script_data(req, data)

        return 'ticketgraph.html', {
            'days': days_back,
            'component': component,
            'components': components
        }, None


def localize_and_truncate(req, ts):
    """Convert to localized timestamp truncated to start of the day."""
    _epoc = datetime.datetime(1970, 1, 1, tzinfo=req.tz)
    delta = to_datetime(ts, req.tz) - _epoc
    ts = delta.days * MILLISECONDS_PER_DAY + delta.seconds * 1000
    return math.floor(ts / MILLISECONDS_PER_DAY) * MILLISECONDS_PER_DAY

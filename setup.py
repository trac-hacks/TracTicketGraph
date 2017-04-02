#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Colin Snover
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from setuptools import setup

setup(
    name='TracTicketGraph',
    version='1.0.4',
    packages=['ticketgraph'],
    package_data={'ticketgraph': ['htdocs/*.*', 'templates/*.*']},

    author='Colin Snover',
    author_email='tracplugins@zetafleet.com',
    description='Graphs Trac tickets over time',
    url='https://github.com/trac-hacks/TracTicketGraph',
    long_description="A Trac plugin that displays a visual graph of ticket "
                     "changes over time.",
    license='MIT',
    keywords='trac plugin ticket statistics graph',
    classifiers=[
        'Framework :: Trac',
    ],
    install_requires=['Trac'],
    entry_points={
        'trac.plugins': [
            'ticketgraph = ticketgraph.ticketgraph',
        ],
    }
)

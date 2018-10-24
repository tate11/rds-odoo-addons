# -*- coding: utf-8 -*-
# Author: Luigi Di Naro
# C 2018 - Teuron S.r.l. and Luigi Di Naro

{
    'name': "invoice-buttons",
    'summary': """Add buttons bar on invoices forms (customer and supplier)""",
    'author': "Teuron S.r.l., Luigi Di Naro",
    'website': "http://www.teuron.it",
    'category': 'account',
    'version': '12.0.0.0',
    'license': 'OPL-1',
    # any module necessary for this one to work correctly
    'depends': ['account'],

    # always loaded
    'data': [
        'views/views.xml',
    ],
    'installable': True
}
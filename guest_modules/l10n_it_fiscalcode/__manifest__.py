# -*- coding: utf-8 -*-
# Copyright 2018 Teuron (<http://www.teuron.it>)

{
    'name': 'Italian Localisation - Fiscal Code',
    'version': '12.0.0.0.0',
    'category': 'Localisation/Italy',
    'author': "Teuron S.r.l.",
    'website': 'http://www.teuron.it',
    'license': 'AGPL-3',
    'depends': ['base_vat'],
    'external_dependencies': {
        'python': ['codicefiscale'],
    },
    'data': [
        'view/fiscalcode_view.xml'
        ],
    'images': [],
    'installable': True
}
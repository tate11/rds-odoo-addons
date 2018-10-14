# -*- coding: utf-8 -*-
# This file and any file found in child directories are part of RDS Moulding Technology SpA Addons for Odoo. 
# See LICENSE.md file in the parent folder for full copyright and licensing details.


{
    'name': 'Italian Localized Pickings',
    'version': '11.0',
    'author': 'RDS Moulding Technology S.p.A.',
    'maintainer': 'RDS Moulding Technology S.p.A.',
    'summary': 'Localizes pickings so as to conform to italian "DDT" standards.',
    'website': 'http://rdsmoulding.com',
    'category': 'Sale',
    'description':
                """
                    Stock Picking integrations to make odoo pickings conform to italian normative for transfer documents.
                """,

    'depends': ['stock', 'delivery'],
    'data': [
            'security/ir.model.access.csv',
            'report/report_ddt.xml',
            'views/stock_picking_views.xml'
            ],
    'application': False,
    'installable': True,
    'auto_install': False,
}

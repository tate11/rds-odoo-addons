# -*- coding: utf-8 -*-
# This file and any file found in child directories are part of RDS Moulding Technology SpA Addons for Odoo. 
# See LICENSE file in the parent folder for full copyright and licensing details.


{
    'name': 'Advanced Production Analytics',
    'version': '11.0',
    'author': 'RDS Moulding Technology S.p.A.',
    'maintainer': 'RDS Moulding Technology S.p.A.',
    'summary': 'More fields and views for production, maintenance and workcenter analytic accounting.',
    'website': 'http://rdsmoulding.com',
    'category': 'Accounting',
    'description':
                """
                    This module adds fields and routines necessary to improve cost analysis of production and maintenance.
                """,

    'depends': ['project', 'mrp', 'mrp_account'],
    'data': [
            'views/mrp.xml'
            ],
    'application': False,
    'installable': True,
    'auto_install': False,
}

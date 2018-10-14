# -*- coding: utf-8 -*-
# This file and any file found in child directories are part of RDS Moulding Technology SpA Addons for Odoo. 
# See LICENSE.md file in the parent folder for full copyright and licensing details.


{
    'name': 'ASA - Parter Pricelists',
    'version': '11.0',
    'author': 'RDS Moulding Technology S.p.A.',
    'maintainer': 'RDS Moulding Technology S.p.A.',
    'summary': 'Partner Pricelists integration for Advanced Sale Analysis.',
    'website': 'http://rdsmoulding.com',
    'category': 'Sale',
    'description':
                """
                    This module partner product code to ASA views.
                """,

    'depends': ['adv_sale_analysis', 'partner_pricelists'],
    'data': [
            'views/sale_order_lines.xml',
            ],
    'application': False,
    'installable': True,
    'auto_install': False,
}

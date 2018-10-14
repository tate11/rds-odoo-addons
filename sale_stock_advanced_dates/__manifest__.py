# -*- coding: utf-8 -*-
# This file and any file found in child directories are part of RDS Moulding Technology SpA Addons for Odoo. 
# See LICENSE file in the parent folder for full copyright and licensing details.


{
    'name': 'Sale&Stock Advanced Date Management',
    'version': '11.0',
    'author': 'RDS Moulding Technology S.p.A.',
    'maintainer': 'RDS Moulding Technology S.p.A.',
    'summary': 'Costumer requests, commitment, planned dates for orders and deliveries',
    'website': 'http://rdsmoulding.com',
    'category': 'Sale',
    'description':
                """
                    This module adds field and reports to enhanch costumer requests and delivery planning on logistics and sale orders.
                """,

    'depends': ['sale_stock'],
    'data': [
            'report/sale_report_templates.xml',
            'views/sale_order.xml',
            'views/stock_picking.xml'
            ],
    'application': False,
    'installable': True,
    'auto_install': False,
}

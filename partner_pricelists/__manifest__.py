# -*- coding: utf-8 -*-
# This file and any file found in child directories are part of RDS Moulding Technology SpA Addons for Odoo. 
# See LICENSE file in the parent folder for full copyright and licensing details.


{
    'name': 'Partner Pricelists',
    'version': '11.0',
    'author': 'RDS Moulding Technology S.p.A.',
    'maintainer': 'RDS Moulding Technology S.p.A.',
    'summary': 'Fully-integrated Partner based Pricelists with Workflow and Reports.',
    'website': 'http://rdsmoulding.com',
    'category': 'Sale',
    'description':
                """
                    This module implements partner-based pricelists. 
                    Partner pricelists have a workflow similar to sale orders, they can be sent as offer to the customer and be approved.                   
                    Order lines are checked against partner pricelist, if it exists, and the price is validated.

                    Partner pricelists are integrated with Odoo standard pricelists (which are renamed to Regional Pricelists).
                    You can define partner-pricelist-based rules on Regional Pricelist with the same formula engine Odoo offers.
                """,

    'depends': ['sale_management'],
    'data': [
            # views
            'views/product_pricelist_views.xml',
            'views/partner_pricelist_views.xml',
            'views/sale_order_views.xml',
            'views/product_views.xml',
            #wizard
            'wizard/partner_pricelist_lock.xml',
            #report
            'report/pricelist_report.xml',
            'report/sale_report_templates.xml',
            # data
            'data/ir_sequence_data.xml',
            'data/mail_template_data.xml',
            'security/ir.model.access.csv'
            ],
    'application': False,
    'installable': True,
    'auto_install': False,
}

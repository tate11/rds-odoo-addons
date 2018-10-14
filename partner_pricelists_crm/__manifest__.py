# -*- coding: utf-8 -*-
# This file and any file found in child directories are part of RDS Moulding Technology SpA Addons for Odoo. 
# See LICENSE.md file in the parent folder for full copyright and licensing details.


{
    'name': 'Partner Pricelists CRM',
    'version': '1.0',
    'author': 'RDS Moulding Technology S.p.A.',
    'maintainer': 'RDS Moulding Technology S.p.A.',
    'summary': 'CRM integration for Partner Pricelists',
    'website': 'http://rdsmoulding.com',
    'category': 'Sale',
    'description':
                """
                    This module implements creating partner pricelist offer from CRM opportunities.
                    It also adds UTM to partner pricelists. 
                """,

    'depends': ['partner_pricelists', 'crm'],
    'data': [
            'views/crm_leads.xml'
            ],
    'auto_install': True,
}

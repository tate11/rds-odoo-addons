# -*- coding: utf-8 -*-
# This file and any file found in child directories are part of RDS Moulding Technology SpA Addons for Odoo. 
# See LICENSE file in the parent folder for full copyright and licensing details.


{
    'name': 'CRM Lead Code',
    'version': '1.0',
    'author': 'RDS Moulding Technology S.p.A.',
    'maintainer': 'RDS Moulding Technology S.p.A.',
    'summary': 'Codified name for CRM Opportunities',
    'website': 'http://rdsmoulding.com',
    'category': 'Sale',
    'description':
                """
                    This module adds a sequence field 'Code' on CRM Leads.
                """,

    'depends': ['crm'],
    'data': [
            'views/crm_lead.xml',
            'data/ir_sequence_data.xml'
            ],
    'auto_install': True,
}

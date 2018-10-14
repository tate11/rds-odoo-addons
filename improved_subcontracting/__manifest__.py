# -*- coding: utf-8 -*-
# This file and any file found in child directories are part of RDS Moulding Technology SpA Addons for Odoo. 
# See LICENSE.md file in the parent folder for full copyright and licensing details.


{
    'name': 'Improved Subcontracting',
    'version': '11.0',
    'author': 'RDS Moulding Technology S.p.A.',
    'maintainer': 'RDS Moulding Technology S.p.A.',
    'summary': 'NON USARE MODULO IN PROVA!!! Supplierinfo on BOMs and subcontracting integrations on POs and MOs.',
    'website': 'http://rdsmoulding.com',
    'category': 'Sale',
    'description':
                """
                    Supplierinfo on BOMs and subcontracting integrations on POs and MOs.
                """,

    'depends': ['purchasing', 'mrp'],
    'data': [
            'views/mrp_views.xml',
            ],
    'application': False,
    'installable': True,
    'auto_install': False,
}

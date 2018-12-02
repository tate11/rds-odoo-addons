# -*- coding: utf-8 -*-
# This file and any file found in child directories are part of RDS Moulding Technology SpA Addons for Odoo. 
# See LICENSE.md file in the parent folder for full copyright and licensing details.


# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

{ 
    'name': 'Pickings to DDTs',
    'category': 'Localization/Italy',
    'description': """
Adds a number of functions and tables to manage italian-normative compliant DDTs.
--------------------------------------------------------------
""",
    'author': "RDS Moulding Technology SpA", 
    'license': "LGPL-3", 
    'website': "http://rdsmoulding.com", 
    'version': '12.0',
    'depends': ['stock', 'delivery'],
    'data': [
            'security/ir.model.access.csv',
            'report/ddt_templates.xml',
            'report/ddt_report.xml',
            'views/stock_picking_views.xml',
            'views/stock_ddt_views.xml',
            'data/ddt_data.xml',
            'data/mail_data.xml'
            ],
    'application': False,
    'installable': True,
    'auto_install': False,
}

# -*- coding: utf-8 -*-
# This file and any file found in child directories are part of RDS Moulding Technology SpA Addons for Odoo. 
# See LICENSE.md file in the parent folder for full copyright and licensing details.


# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

{ 
    'name': 'Account with DDTs',
    'category': 'Localization/Italy',
    'description': """
Adds a ddt reference to account invoice line.
--------------------------------------------------------------
""",
    'author': "RDS Moulding Technology SpA", 
    'license': "LGPL-3", 
    'website': "http://rdsmoulding.com", 
    'version': '12.0',
    'depends': ['l10n_it_picking_ddt', 'account'],
    'data': [
            'views/account_views.xml',
            ],
    'application': False,
    'installable': True,
    'auto_install': False,
}

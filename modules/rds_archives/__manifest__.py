# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

{ 
    'name': "RDS Archives",
    'category': 'Integrations',
    'summary': "Legacy data connector for RDS Moulding Technology S.p.A.",
    'description': """
                      This module is intended for sole use by RDS Moulding Technology S.p.A.
                      Its purpuse is to allow downloading data on-demand from its legacy archives to Odoo.
                    """,
    'author': "RDS Moulding Technology SpA", 
    'license': "LGPL-3", 
    'website': "http://rdsmoulding.com", 
    'version': '12.0',
    'depends': [
                'product', 'sale'
               ], 
    'data': [
    ],
    'application': False,
    'installable': True,
}
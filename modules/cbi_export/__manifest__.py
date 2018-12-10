# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

{ 
    'name': "CBI Export", 
    'summary': "Export invoices in CBI format.",
    'description': """
                    """,
    'author': "RDS Moulding Technology SpA", 
    'license': "LGPL-3", 
    'website': "http://rdsmoulding.com", 
    'category': 'Accounting', 
    'version': '12.0', 
    'depends': [
                'account', 'l10n_it_abicab'
               ], 
    'data': [
        'views/account_views.xml',
        'report/cbi.xml'
    ],
    'application': False,
    'installable': True,
} 
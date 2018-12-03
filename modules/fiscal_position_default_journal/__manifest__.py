# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

{ 
    'name': 'Default Journal on Fiscal Position',
    'category': 'Accounting',
    'description': """
Extends fiscal position to store information about default journal.
-------------------------------------------------------------------
""",
    'author': "RDS Moulding Technology SpA", 
    'license': "AGPL-3", 
    'website': "http://rdsmoulding.com", 
    'version': '12.0', 
    "depends" : ['account'],
    "data": ['views/sale_invoice_journal.xml'],
    'installable': True
}
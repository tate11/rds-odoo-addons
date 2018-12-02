# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

#TODO: Refactor and remove -----... code.

{ 
    'name': 'Odoo - DIA Bridge',
    'category': 'Integrations',
    'description': """
Integrates Odoo with DIA ERP. Adds tables, procedures and views to manage transfer of DDT data to the DIA ERP.
--------------------------------------------------------------
""",
    'author': "RDS Moulding Technology SpA", 
    'license': "LGPL-3", 
    'website': "http://rdsmoulding.com", 
    'version': '12.0',
    'depends': ['sale', 'l10n_it_picking_ddt'],
    'data': [
            # data
            'data/cron.xml',
            'data/sequence.xml',
            'security/ir.model.access.csv',
            # view
            'views/dia_transfer.xml',
            'views/dia_fields_views.xml'
            ],
    'application': 'false',
    'installable': 'true',
}

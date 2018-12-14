# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

{ 
    'name': "RDS Customizations - MRP II", 
    'summary': "Reports and personalized views for RDS Moulding Technology S.p.A.",
    'description': """
                      This module is intended for sole use by RDS Moulding Technology S.p.A.
                      Its purpuse is to add custom reports/views to Odoo.
                    """,
    'author': "RDS Moulding Technology SpA", 
    'license': "LGPL-3", 
    'website': "http://rdsmoulding.com", 
    'category': 'Integrations', 
    'version': '12.0',
    'depends': [
                'mrp_workorder', 'mrp_maintenance', 'stock_barcode'
               ], 
    'data': [
        'security/ir.model.access.csv',
        'report/mrp_production_label.xml',
        'views/mrp_bom_views.xml',
        'views/mrp_production_views.xml',
        'views/maintenance_views.xml',
        'views/stock_rds_report.xml'
    ],
    'application': False,
    'installable': True,
} 

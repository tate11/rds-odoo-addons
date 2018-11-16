# Intended for sole use by RDS Moulding Technology SpA. See README file.

{ 
    'name': "RDS Customizations", 
    'summary': "Report e viste personalizzate per RDS Moulding Technology S.p.A.",
    'description': """
                      This module is intended for sole use by RDS Moulding Technology S.p.A.
                      Its purpuse is to add custom reports/views to Odoo.
                    """,
    'author': "RDS Moulding Technology SpA", 
    'license': "AGPL-3", 
    'website': "http://rdsmoulding.com", 
    'category': 'hr', 
    'version': '12.0', 
    'depends': [
                'mrp', 'sale_management'
               ], 
    'data': [
        'wizard/product_merge.xml',
        'reports/mrp_production_label.xml',
        'reports/sale_order.xml'
    ],
    'application': False,
    'installable': True,
} 
# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

{ 
    'name': "RDS Customizations", 
    'summary': "Reports and personalized views for RDS Moulding Technology S.p.A.",
    'description': """
                      This module is intended for sole use by RDS Moulding Technology S.p.A.
                      Its purpuse is to add custom reports/views to Odoo.

                      Effort should be made to keep customizations in separate modules when possible.
                      This module should only keep generic procedures that do not warrant a separate module.
                    """,
    'author': "RDS Moulding Technology SpA", 
    'license': "LGPL-3", 
    'website': "http://rdsmoulding.com", 
    'category': 'Integrations', 
    'version': '12.0', 
    'depends': [
                'sale'
               ], 
    'data': [
        'wizard/product_merge.xml',
        'reports/sale_order.xml'
    ],
    'application': False,
    'installable': True,
} 
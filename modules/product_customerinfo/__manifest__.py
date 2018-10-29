# Intended for sole use by RDS Moulding Technology SpA. See README file.

{ 
    'name': "Customer-specific Product Info", 
    'summary': "Adds customer specific product info.",
    'author': "RDS Moulding Technology SpA", 
    'license': "AGPL-3", 
    'website': "http://rdsmoulding.com", 
    'category': 'hr', 
    'version': '12.0', 
    'depends': [
                'product'
               ], 
    'data': [
            'security/ir.model.access.csv',
            'views/product_views.xml',
    ],
    'application': False,
    'installable': True,
} 
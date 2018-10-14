{ 
    'name': "RDS Misc", 
    'summary': "A module for misc utilities.", 
    'description': """This module implements a number of misc utilities for RDS.""", 
    'author': "RDS Moulding Technology SpA", 
    'license': "AGPL-3", 
    'website': "http://rdsmoulding.com", 
    'category': 'RDSMisc', 
    'version': '11.0.1.0.0', 
    'depends': ['base', 'stock', 'mrp'], 
    'data': [
        'security/misc_security.xml', 'views/products.xml', 'views/company.xml', 'views/report_templates.xml', 'views/mrp.xml', 'report/product.xml'
    ],
    'application': 'false',
    'installable': 'true',
} 
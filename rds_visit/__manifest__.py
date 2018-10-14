# -*- coding: utf-8 -*-

{ 
    'name': "Visitors", 
    'summary': "A module to manage visitors.", 
    'description': """This module allows the creation of visitor profiles, scheduling of visits, printing of visitor badges.""", 
    'author': "RDS Moulding Technology SpA", 
    'license': "AGPL-3", 
    'website': "http://rdsmoulding.com", 
    'category': 'Visits', 
    'version': '11.0.1.0.0', 
    'depends': ['base','hr','rds_misc'], 
    'data': [
        'security/visit_security.xml',
        'security/ir.model.access.csv',
        'report/rds_visit_badge.xml',
        'views/rds_visit_views.xml',
    ],
    'application': 'true',
    'installable': 'true',
} 
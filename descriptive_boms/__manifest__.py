{ 
    'name': "Descriptive BOMS", 
    'summary': "Adds descriptive fields for BOM lines", 
    'description': """""", 
    'author': "RDS Moulding Technology SpA", 
    'license': "AGPL-3", 
    'website': "http://rdsmoulding.com", 
    'category': 'hr', 
    'version': '11.0.1.0.0', 
    'depends': ['mrp'], 
    'data': ['views/mrp_bom_views.xml',
             'report/bom_structure.xml'
            ],
    'application': 'false',
    'installable': 'true',
} 
# Intended for sole use by RDS Moulding Technology SpA. See README file.

{ 
    'name': "Workorder Time Offset", 
    'summary': "Adds a fixed time offset to odoo routings operations.",
    'description': """Adds a fixed time offset to odoo routings operations.""",
    'author': "RDS Moulding Technology SpA", 
    'license': "AGPL-3", 
    'website': "http://rdsmoulding.com", 
    'category': 'hr', 
    'version': '12.0', 
    'depends': [
                'mrp'
               ], 
    'data': [
        'views/mrp_bom_views.xml'
    ],
    'application': False,
    'installable': True,
} 
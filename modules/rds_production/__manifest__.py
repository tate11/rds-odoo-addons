# Intended for sole use by RDS Moulding Technology SpA. See README file.

{ 
    'name': "RDS Production", 
    'summary': "Adds a number of simple customizations for RDS's usage.",
    'description': """Adds a fixed time offset to odoo routings operations.""",
    'author': "RDS Moulding Technology SpA", 
    'license': "AGPL-3", 
    'website': "http://rdsmoulding.com", 
    'category': 'hr', 
    'version': '12.0', 
    'depends': [
                'mrp_workorder', 'mrp_maintenance'
               ], 
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_bom_views.xml',
        'views/mrp_production_views.xml',
        'views/maintenance_views.xml'
    ],
    'application': False,
    'installable': True,
} 
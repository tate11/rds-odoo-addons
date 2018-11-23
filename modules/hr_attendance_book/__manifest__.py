# Intended for sole use by RDS Moulding Technology SpA. See README file.

{ 
    'name': "HR Lul", 
    'summary': "Adds small quality-of-life improvements to HR management.", 
    'description': """This module adds menuitems and base utilities for other modules, centered on HR reporting.
                   """, 
    'author': "RDS Moulding Technology SpA", 
    'license': "AGPL-3", 
    'website': "http://rdsmoulding.com", 
    'category': 'hr', 
    'version': '12.0', 
    'depends': [
                'hr', 'hr_attendance'
               ], 
    'data': [
        'security/ir.model.access.csv',
        'views/attendance_book_views.xml',
    ],
    'application': False,
    'installable': True,
} 
# Intended for sole use by RDS Moulding Technology SpA. See README file.

{ 
    'name': "HR Quality of Life ", 
    'summary': "Adds small quality-of-life improvements to HR management.", 
    'description': """This module adds menuitems and base utilities for other modules, centered on HR reporting.
                      It also exposes certain fields, menus and views for commodity of RDS.
                   """, 
    'author': "RDS Moulding Technology SpA", 
    'license': "AGPL-3", 
    'website': "http://rdsmoulding.com", 
    'category': 'hr', 
    'version': '12.0', 
    'depends': [
                'hr', 'hr_attendance'
               ], 
    'data': ['report/employee_badge.xml',
             'views/hr_views.xml',
    ],
    'application': False,
    'installable': True,
} 
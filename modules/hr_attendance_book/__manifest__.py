# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

{ 
    'name': 'Hr Attendance Book',
    'category': 'Human Resources',
    'description': """
Extends attendance with monthly workbooks similar to traditional italian software such as
Zucchetti. Adds dedicated reports and compatibily with GIS system.
--------------------------------------------------------------
""",
    'author': "RDS Moulding Technology SpA", 
    'license': "LGPL-3", 
    'website': "http://rdsmoulding.com", 
    'version': '12.0',
    'depends': [
                'hr', 'hr_attendance', 'hr_holidays'
               ], 
    'data': [
        'security/ir.model.access.csv',
        'views/attendance_book_views.xml',
    ],
    'application': False,
    'installable': True,
} 
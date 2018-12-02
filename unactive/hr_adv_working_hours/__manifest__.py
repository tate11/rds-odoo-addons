# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

{ 
    'name': 'Advanced Working Schedule Management',
    'category': 'Human Resources',
    'description': """
Extends Employee and Resource Calendar with support for shifts. Adds dedicated reports.
--------------------------------------------------------------
""",
    'author': "RDS Moulding Technology SpA", 
    'license': "LGPL-3", 
    'website': "http://rdsmoulding.com", 
    'version': '12.0',
    'depends': ['hr', 'hr_attendance'], 
    'data': [
            'report/working_schedule_reports.xml',
            'views/hr_views.xml',
            'views/report_templates.xml',
            'wizard/working_schedule_printer.xml',
            'cron/cron_rotate_shifts.xml',
    ],
    'application': False,
    'installable': True,
}
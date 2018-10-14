# -*- coding: utf-8 -*-
# This file and any file found in child directories are part of RDS Moulding Technology SpA Addons for Odoo. 
# See LICENSE.md file in the parent folder for full copyright and licensing details.


{
    'name': 'Frontend Project Timesheet',
    'version': '11.0',
    'author': 'RDS Moulding Technology S.p.A.',
    'maintainer': 'RDS Moulding Technology S.p.A.',
    'summary': 'More fields and views for order and sale analysis.',
    'website': 'http://rdsmoulding.com',
    'category': 'Sale',
    'description':
                """
                    This module adds views, fields and other to aid in order and sales analisys.
                """,

    'depends': ['project', 'hr_timesheet'],
    'data': [
            'controllers/frontend_timesheet_views.xml',
            'views/project_task_views.xml'
            ],
    'application': False,
    'installable': True,
    'auto_install': False,
}

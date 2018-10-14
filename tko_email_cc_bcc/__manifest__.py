# -*- coding: utf-8 -*-
# © 2017 TKO <http://tko.tko-br.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Mail CC and BCC',
    'summary': '',
    'description': 'Adds CC and BCC in email compose wizard.',
    'author': 'TKO',
    'category': 'Discuss',
    'license': 'AGPL-3',
    'website': 'http://tko.tko-uk.com',
    'version': '11.0.1.0.0',
    'depends': ['base','mail'],
    'application': False,
    'installable': True,
    'auto_install': False,
    'data': [
        'views/email_cc_bcc_view.xml',
    ],
}
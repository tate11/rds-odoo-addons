# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Documents - Sales',
    'version': '1.0',
    'category': 'Uncategorized',
    'summary': 'Sales from Documents',
    'description': """
Add the ability to create sales from the document module.
""",
    'website': ' ',
    'depends': ['documents', 'sale_management'],
    'data': ['data/data.xml', 'views/documents_views.xml'],
    'installable': True,
    'auto_install': False,
}

# -*- coding: utf-8 -*-
# © 2013-15 Agile Business Group sagl (<http://www.agilebg.com>)
# © 2016 AvanzOSC (<http://www.avanzosc.es>)
# © 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# © 2016 KTec S.r.l. (<http://www.ktec.it>)
# © 2017 Teuron S.r.l. (<http://www.ktec.it>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Stock Picking Invoice Link',
    'version': '12.0.1.0.0',
    'category': 'Warehouse Management',
    'summary': 'Adds link between pickings and invoices',
    'author': 'Agile Business Group, '
              'Tecnativa, '
              'Odoo Community Association (OCA), '
              'KTec, Teuron',
    'website': 'http://www.teuron.it',
    'license': 'AGPL-3',
    'depends': ['sale_stock','invoice_buttons'],
    'data': [
        'views/stock_view.xml',
        'views/account_invoice_view.xml',
    ],
    'installable': True,
}


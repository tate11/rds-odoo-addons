# -*- encoding: utf-8 -*-
##############################################################################
#
#    OmniaSolutions, Open Source Management Solution
#    Copyright (C) 2010-2011 OmniaSolutions (<http://www.omniasolutions.eu>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'RDS Omnia Extension',
    'version': '11.0',
    'author': 'OmniaSolutions',
    'maintainer': 'OmniaSolutions',
    'website': 'http://www.omniasolutions.website',
    'category': 'Sale',
    'description': """
This module extend the sale order
""",
    'category': 'Customization',
    'depends': ['stock',
                'hr_holidays',
                'hr_attendance',
                'omnia_mold',
                # 'omnia_sale_extended',
                'rds_attachments',
                'rds_dia',
                'rds_hr',
                'rds_hr_attendance',
                # 'rds_mail',
                'rds_misc',
                'partner_pricelists',
                'rds_visit',
                'tko_email_cc_bcc',
                'web_flaggrid',
                'omnia_ddt',
                'manufacturing_subcontracting_rule',
                'omnia_mrp_analytic',
                #'omnia_pick_merge',
                #'l10n_it_fiscalcode',
                'omnia_mrp_recycle',
                'omnia_machine_updater',
                'purchase',
                'sale_stock_advanced_dates',
                'omnia_stock_delivery_report',
                'omnia_warehouse_journal',
                ],
    'data': ['views/import_report_css.xml',
             'views/mrp_workorder.xml',
             'views/mrp_extension.xml',
             'views/mrp_production.xml',
             'views/sale_order.xml',
             'views/stock_inventory_line.xml',
             'views/stock_picking.xml',
             'views/res_partner.xml',
             'views/stock_move.xml',
             # report
             'report/ddt_report_extension.xml',
             'report/sale_order.xml',
             'report/mrp_production.xml',
             'report/stock_delivery_report.xml',
             'report/labels.xml',
             # controllers
             'controllers/lables.xml',
             # wizard
             'wizard/wizard.xml',
             ],
    'application': False,
    'installable': True,
    'auto_install': False,
}

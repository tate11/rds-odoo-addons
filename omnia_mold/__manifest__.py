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
    'name': 'RDS Mold',
    'version': '11.0',
    'author': 'OmniaSolutions',
    'maintainer': 'OmniaSolutions',
    'website': 'http://www.omniasolutions.website',
    'category': 'mrp',
    'description': """
Manage mold in odoo
""",
    'category': 'mrp',
    'depends': ['mrp',
                'maintenance',
                'mrp_account',
                'project',
                'sale_timesheet',
                'omnia_mrp_analytic'],
    'data': [
            # views
            'views/mold.xml',
            'views/mrp_routing_workcenter.xml',
            'views/stock_production_lot.xml',
            'views/mrp_production.xml',
            'views/mrp_workorder.xml',
            'views/data.xml',
            'wizard/wizard.xml',
            # report
            'report/labels.xml',
            'report/mold_reports.xml',
            # security
            'security/ir.model.access.csv'],
    'application': False,
    'installable': True,
    'auto_install': False,
}

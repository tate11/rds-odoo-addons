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
    'name': 'RDS machine Updater',
    'version': '11.0',
    'author': 'OmniaSolutions',
    'maintainer': 'OmniaSolutions',
    'website': 'http://www.omniasolutions.website',
    'category': 'mrp',
    'description': """
Read data from machine file and acquire it into odoo
""",
    'category': 'mrp',
    'depends': ['mrp'],
    'data': ['views/mrp_workcenter.xml',
             'data/crono.xml',
             ],
    'application': False,
    'installable': True,
    'auto_install': False,
}

# -*- coding: utf-8 -*-
# This file and any file found in child directories are part of RDS Moulding Technology SpA Addons for Odoo. 
# See LICENSE file in the parent folder for full copyright and licensing details.


{
    'name': 'Odoo MES',
    'version': '11.0',
    'author': 'RDS Moulding Technology S.p.A.',
    'maintainer': 'RDS Moulding Technology S.p.A.',
    'summary': 'Odoo MES implements MODBUS communication with your workcenters PLC, cycle time monitoring, real-time efficiency control.',
    'website': 'http://rdsmoulding.com',
    'category': 'Sale',
    'description':
                """""",

    'depends': ['mrp', 'quality_mrp'],
    'data': [
            'data/ir_config_parameter.xml',
            'views/mrp_workorder_views.xml',
            'views/mrp_signals.xml',
            'views/oee_views.xml',
            'controllers/andon.xml'
            ],
    'application': False,
    'installable': True,
    'auto_install': False,
}

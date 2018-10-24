# -*- coding: utf-8 -*-
# This file and any file found in child directories are part of RDS Moulding Technology SpA Addons for Odoo. 
# See LICENSE file in the parent folder for full copyright and licensing details.


{
    'name': 'Kontroru',
    'version': '11.0',
    'author': 'RDS Moulding Technology S.p.A.',
    'summary': 'An odoo-centric MES software.',
    'website': 'http://rdsmoulding.com',
    'category': 'Production',
    'description':
                """Kontroru implements MODBUS communication with your workcenters PLC, cycle time monitoring, real-time efficiency control.""",

    'depends': ['mrp', 'quality_mrp'],
    'data': [
            'security/ir.model.access.csv',
            'views/mrp_scada_views.xml',
            'views/mrp_workorder_views.xml',
            'views/mrp_workcenter_views.xml',
            'views/web_asset_backend_template.xml'
            ],
    'qweb': [
        "static/src/xml/scada.xml",
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}

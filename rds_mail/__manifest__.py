{ 
    'name': "RDS Mail", 
    'summary': "Improved Mailing System.", 
    'description': """This module enhanches Odoo Mail to be a fully-featured mail client.""", 
    'author': "RDS Moulding Technology SpA", 
    'license': "AGPL-3", 
    'website': "http://rdsmoulding.com", 
    'category': 'Mail', 
    'version': '11.0.1.0.0', 
    'depends': ['base','mail'], 
    'data': ['views/mail.xml', 'views/web_asset_backend_template.xml', 'wizard/channel_tothread.xml', 'security/ir.model.access.csv'
    ],
    'application': 'false',
    'installable': 'true',
    'qweb': ['static/src/xml/mail_templates.xml'],
} 
{
    'name': "RDS Dia",
    'summary': "Modulo di integrazione a DIA.",
    'description': """Il modulo implementa integrazioni con il sistema DIA necessarie a RDS.""",
    'author': "RDS Moulding Technology SpA",
    'license': "AGPL-3",
    'website': "http://rdsmoulding.com",
    'category': 'RDSMisc',
    'version': '11.0.1.0.0',
    'depends': ['sale',
                'omnia_ddt',
                'manufacturing_subcontracting_rule'],
    'external_dependencies': {
        'python': ['unidecode'],
    },
    'data': [
            # security
            'security/security.xml',
            # data
            'data/crono.xml',
            # view
            'views/product_template.xml',
            'views/stock_picking.xml',
            'views/res_partner.xml',
            'views/sequence.xml',
            'views/account_tax.xml',
            'views/sale_order.xml',
            'views/dia_lastnumber.xml',
            'views/account_fiscal_position.xml',
            ],
    'application': 'false',
    'installable': 'true',
}

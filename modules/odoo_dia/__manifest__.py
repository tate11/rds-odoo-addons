{
    'name': "RDS Dia Revised",
    'summary': "Modulo di integrazione a DIA.",
    'description': """Il modulo implementa integrazioni con il sistema DIA necessarie a RDS.""",
    'author': "RDS Moulding Technology SpA",
    'license': "AGPL-3",
    'website': "http://rdsmoulding.com",
    'category': 'RDSMisc',
    'version': '11.0.1.0.0',
    'depends': ['sale'],
    'data': [
            # data
            'data/cron.xml',
            'data/sequence.xml',
            'security/ir.model.access.csv',
            # view
            'views/dia_transfer.xml',
            'views/dia_fields_views.xml'
            ],
    'application': 'false',
    'installable': 'true',
}

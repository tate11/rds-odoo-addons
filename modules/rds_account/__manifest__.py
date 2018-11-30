# Intended for sole use by RDS Moulding Technology SpA. See README file.

{ 
    'name': "RDS Account", 
    'summary': "Adds a number of simple customizations for RDS's usage.",
    'description': """""",
    'author': "RDS Moulding Technology SpA", 
    'license': "AGPL-3", 
    'website': "http://rdsmoulding.com", 
    'category': 'hr', 
    'version': '12.0', 
    'depends': [
                'account', 'account_budget'
               ], 
    'data': [
        'views/account_budget_views.xml'
    ],
    'application': False,
    'installable': True,
} 
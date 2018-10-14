{ 
    'name': "HR Formation", 
    'summary': "Un modulo di RDS per tenere traccia dei corsi di formazione e gestire le abilità del personale.", 
    'description': """Contiene le integrazioni seguenti: Corsi, Documenti Corsi, Diplomi, Abilità, Skill Matrix""", 
    'author': "RDS Moulding Technology SpA", 
    'license': "AGPL-3", 
    'website': "http://rdsmoulding.com", 
    'category': 'hr', 
    'version': '11.0.1.0.0', 
    'depends': ['rds_hr',
                'rds_attachments'], 
    'data': ['security/ir.model.access.csv','views/hr_views.xml', 'report/skill_log.xml'
    ],
    'application': 'false',
    'installable': 'true',
} 
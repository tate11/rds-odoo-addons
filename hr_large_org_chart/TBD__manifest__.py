{ 
    'name': "Large Organizational Chart", 
    'summary': "Full Organizational Chart, with controller or report.", 
    'description': """This module adds a company-wide organizational chart.
                      This Org. Chart can be viewed through a controller at /hr/org_chart, e.g. for andons, or it can be printed as a report. This latter use is currently only for debug mode due to bad rendering (Cause by QWeb limits.)
                   """, 
    'author': "RDS Moulding Technology SpA", 
    'license': "AGPL-3", 
    'website': "http://rdsmoulding.com", 
    'category': 'hr', 
    'version': '12.0', 
    'depends': [
                'hr_org_chart',
                'hr_qol'
               ], 
    'data': ['report/print_org_chart.xml',
             'wizard/org_chart_printer_view.xml',
             'views/report_templates.xml',
    ],
    'application': False,
    'installable': True,
} 
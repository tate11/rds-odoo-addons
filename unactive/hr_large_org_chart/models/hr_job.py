from odoo import fields, models

class Job(models.Model):
    _inherit = ['hr.job']
    collapse_on_org_chart = fields.Boolean(string='Collassa su Organigramma')
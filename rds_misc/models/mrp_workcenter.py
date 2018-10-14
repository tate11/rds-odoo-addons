
from odoo import api, fields, models

class MrpWorkcenter(models.Model):

    _inherit = ['mrp.workcenter']

    location = fields.Char(string="Dislocazione")
    department_id = fields.Many2one('hr.department', string="Reparto Responsabile")
    
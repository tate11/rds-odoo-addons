# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

from odoo import fields, models

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    advantage_id = fields.Many2one('hr.attendance.advantage', "Modello di Presenza")
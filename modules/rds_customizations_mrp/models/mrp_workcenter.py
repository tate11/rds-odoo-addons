# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

from odoo import models, fields, api

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class MrpWorkcenter(models.Model):
    _inherit = "mrp.workcenter"

    time_logging = fields.Selection([('standard', 'Interface-Detection'), ('manual', 'Manual')],
                                     default='standard', string="Time Logging", required=True)

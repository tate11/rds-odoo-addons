# -*- coding: utf-8 -*-
# This file and any file found in child directories are part of RDS Moulding Technology SpA Addons for Odoo. 
# See LICENSE file in the parent folder for full copyright and licensing details.

from odoo import models, fields, api

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class MrpWorkcenter(models.Model):
    _inherit = "mrp.workcenter"

    time_logging = fields.Selection([('standard', 'Interface-Detection'), ('manual', 'Manual')],
                                     default='standard', string="Time Logging", required=True)

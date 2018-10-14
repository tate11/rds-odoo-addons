'''
Created on 10 Jul 2018

@author: mboscolo
'''
from odoo.exceptions import UserError
from datetime import datetime
from odoo import models
from odoo import fields
from odoo import _
from odoo import api
import logging


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    routing_type = fields.Selection([('process', "Process-oriented"), ('tool', 'Tool-oriented')], string="Routing Type", required=True, default="process")
    tool_ids = fields.Many2many('maintenance.equipment', string='Tools', compute="get_mold")

    @api.one
    def get_mold(self):
        if self.routing_type != "tool":
            self.tool_ids = False
        else:
            self.tool_ids = self.env['omnia_mold.mold_configuration'].search([('product_id', '=', self.product_tmpl_id.id)]).mapped(lambda x: x.mold_id)

# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'
    tag_ids = fields.Many2many('mrp.routing.workcenter.tags', string="Tags", help="The material will be consumed at the first matching operation.")

class MrpBom(models.Model):
    _inherit = 'mrp.bom'
    alternative_routings = fields.Many2many('mrp.routing', string="Alternative Routings", help="Alternative routings to be chosen from in manual workorder creation.")

class ReportBomStructure(models.AbstractModel):
    _inherit = 'report.mrp.report_bom_structure'

    def _get_operation_line(self, routing, qty, level):
        operations = super(ReportBomStructure, self)._get_operation_line(routing, qty, level)
        for i in operations:
            i['duration_expected'] += i['operation'].time_offset
            total = ((i['duration_expected'] / 60.0) * i['operation'].workcenter_id.costs_hour)
            i['total'] = float_round(total, precision_rounding=self.env.user.company_id.currency_id.rounding)

        return operations
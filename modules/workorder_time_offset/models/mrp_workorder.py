# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round

from itertools import groupby
import logging


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    unit_operation = fields.Boolean("Unit Operation", related="operation_id.unit_operation", readonly=True, help="Marks the operation as a unitary operation. All parts will be processed at once.")

    @api.model
    def create(self, vals):
        if vals.get('duration_excepted'):
            vals["duration_excepted"] = vals["duration_excepted"] + self.env['mrp.routing.workcenter'].browse(vals['operation_id']).time_offset
        return super(MrpWorkorder, self).create(vals)

    def write(self, vals):
        if vals.get('duration_excepted'):
            vals["duration_excepted"] = vals["duration_excepted"] + self.operation_id.time_offset
        super(MrpWorkorder, self).write(vals)


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    time_offset = fields.Float("Fixed Offset")
    unit_operation = fields.Boolean("Unit Operation", help="Marks the operation as a unitary operation. All parts will be processed at once.")


class ReportBomStructure(models.AbstractModel):
    _inherit = 'report.mrp.report_bom_structure'

    def _get_operation_line(self, routing, qty, level):
        operations = super(ReportBomStructure, self)._get_operation_line(routing, qty, level)
        for i in operations:
            i['duration_expected'] += i['operation'].time_offset
            total = ((i['duration_expected'] / 60.0) * i['operation'].workcenter_id.costs_hour)
            i['total'] = float_round(total, precision_rounding=self.env.user.company_id.currency_id.rounding)

        return operations
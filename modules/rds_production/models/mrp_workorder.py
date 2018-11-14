# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round

from itertools import groupby
import logging


class OperationTag(models.Model):
    _description = 'Operation Tag'
    _name = 'mrp.routing.workcenter.tags'
    _order = 'name'

    name = fields.Char(string='Tag Name', required=True)
    color = fields.Integer(string='Color Index')
    active = fields.Boolean(default=True, help="The active field allows you to hide the category without removing it.")
    
    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Tag name must be unique.')
    ]


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
    tag_id = fields.Many2one('mrp.routing.workcenter.tags', "Tag")
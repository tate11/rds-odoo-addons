# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round

import logging
logger = logging.getLogger()

class MrpProduction(models.Model):
    """ Manufacturing Orders """
    _inherit = 'mrp.production'

    routing_id = fields.Many2one(
        'mrp.routing', 'Routing',
        compute='_compute_routing', inverse="_set_routing", store=True, readonly=True, states={'confirmed': [('readonly', False)]},
        help="The list of operations (list of work centers) to produce the finished product. The routing "
             "is mainly used to compute work center costs during operations and to plan future loads on "
             "work centers based on production planning.")

    routing_id_force = fields.Many2one('mrp.routing', 'Routing', readonly=True)

    default_routing = fields.Many2one('mrp.routing', related="bom_id.routing_id")
    alternative_routings = fields.Many2many('mrp.routing', string="Alternative Routings", related="bom_id.alternative_routings", help="Alternative routings to be chosen from in manual workorder creation.")

    has_maintenance = fields.Boolean('Tools on Maintenance', compute='_tools_on_maintenance')
    equipment_ids = fields.Many2many('maintenance.equipment', compute='_tools_on_maintenance', string="Tools Status")
    
    def _tools_on_maintenance(self):
        for production in self:
            production.equipment_ids = production.routing_id.operation_ids.mapped(lambda x: x.equipment_ids + x.workcenter_id.equipment_ids) 
            _tools_on_maintenance = production.equipment_ids.filtered(lambda x: x.maintenance_open_count >= 1)
            if _tools_on_maintenance:
                production.has_maintenance = True

    def _generate_raw_move(self, bom_line, line_data):
        line = super(MrpProduction, self)._generate_raw_move(bom_line, line_data)
        if self.routing_id:
            routing = self.routing_id
        else:
            routing = self.bom_id.routing_id

        operation_consumption = routing.operation_ids.filtered(lambda x: x.tag_id in bom_line.tag_ids)
        line.operation_id = operation_consumption and operation_consumption[0] or line.operation_id

        return line

    @api.multi
    @api.depends('bom_id.routing_id', 'bom_id.routing_id.operation_ids')
    def _compute_routing(self):
        for production in self:
            if production.routing_id_force:
                production.routing_id = production.routing_id_force
            elif production.bom_id.routing_id.operation_ids:
                production.routing_id = production.bom_id.routing_id.id
            else:
                production.routing_id = False

    def _set_routing(self):
        if not self.routing_id.operation_ids:
            raise ValidationError(_("The chosen routing has no operations defined. Please correct the routing."))
        else:
            if self.routing_id != self.default_routing:
                self.routing_id_force = self.routing_id
                for i in self.move_raw_ids:
                    operation_consumption = self.routing_id.operation_ids.filtered(lambda x: x.tag_id in i.bom_line_id.tag_ids)
                    i.operation_id =  operation_consumption and operation_consumption[0] or False
            else:
                self.routing_id_force = False

    def _workorders_create(self, bom, bom_data):
        """
        :param bom: in case of recursive boms: we could create work orders for child
                    BoMs
        """
        workorders = self.env['mrp.workorder']
        bom_qty = bom_data['qty']

        # Initial qty producing
        if self.product_id.tracking == 'serial':
            quantity = 1.0
        else:
            quantity = self.product_qty - sum(self.move_finished_ids.mapped('quantity_done'))
            quantity = quantity if (quantity > 0) else 0

        for operation in self.routing_id.operation_ids:
            # create workorder
            cycle_number = float_round(bom_qty / operation.workcenter_id.capacity, precision_digits=0, rounding_method='UP')
            duration_expected = (operation.workcenter_id.time_start +
                                 operation.workcenter_id.time_stop +
                                 cycle_number * operation.time_cycle * 100.0 / operation.workcenter_id.time_efficiency)
            workorder = workorders.create({
                'name': operation.name,
                'production_id': self.id,
                'workcenter_id': operation.workcenter_id.id,
                'operation_id': operation.id,
                'duration_expected': duration_expected,
                'state': len(workorders) == 0 and 'ready' or 'pending',
                'qty_producing': quantity,
                'capacity': operation.workcenter_id.capacity,
            })
            if workorders:
                workorders[-1].next_work_order_id = workorder.id
            workorders += workorder

            # assign moves; last operation receive all unassigned moves (which case ?)
            moves_raw = self.move_raw_ids.filtered(lambda move: move.operation_id == operation)
            if len(workorders) == len(bom.routing_id.operation_ids):
                moves_raw |= self.move_raw_ids.filtered(lambda move: not move.operation_id)
            moves_finished = self.move_finished_ids.filtered(lambda move: move.operation_id == operation) #TODO: code does nothing, unless maybe by_products?
            moves_raw.mapped('move_line_ids').write({'workorder_id': workorder.id})
            (moves_finished + moves_raw).write({'workorder_id': workorder.id})

            workorder._generate_lot_ids()
        return workorders

    def button_unplan(self):
        self.mapped('workorder_ids').unlink()
        for i in self:
            self.state = 'confirmed'
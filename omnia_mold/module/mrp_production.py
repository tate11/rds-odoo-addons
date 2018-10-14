##############################################################################
#
#    OmniaSolutions, Your own solutions
#    Copyright (C) 27/set/2016 OmniaSolutions (<http://www.omniasolutions.eu>). All Rights Reserved
#    info@omniasolutions.eu
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
'''
Created on 27/set/2016

@author: mboscolo
'''
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round, float_is_zero
from datetime import datetime
from odoo import models
from odoo import fields
from odoo import _
from odoo import api
import math
import logging


class MrpProductionToolPreview(models.TransientModel):
    _name = "mrp.tool.preview"
    tool_id = fields.Many2one('maintenance.equipment',
                              string=_("Equipment"),)


class MrpProduction(models.Model):
    _name = "mrp.production"
    _inherit = "mrp.production"

    routing_type = fields.Selection([('process', "Process-oriented"), ('tool', 'Tool-oriented')], string="Routing Type", related="bom_id.routing_type")
    mold_id = fields.Many2one('maintenance.equipment',
                              string=_("Equipment"),)

    mold_routing_id = fields.Many2one('mrp.routing',
                                      string=_("Routing"),)

    project_id = fields.Many2one('project.project',
                                 string=_('Analytic Account'))

    customer_id = fields.Many2one(related="project_id.partner_id",
                                  string=_('Customer'))

    def_date_planned_start = fields.Datetime('Creation Deadline Start', copy=False)

    def_date_planned_finished = fields.Datetime('Deadline End', copy=False)

    @api.one
    @api.depends('product_id')
    def _get_tool_preview(self):
        self.tool_production_previews = False
        possible_tools = self.env['omnia_mold.mold_configuration'].search([('product_id', '=', self.product_id.id)]).mapped(lambda x: x.mold_id)
        logging.warning(possible_tools)
        t = []
        for i in possible_tools:
            t = self.env['mrp.tool.preview'].new({'tool_id': i.id})
            logging.warning(t)
            logging.warning(t.tool_id)
        self.tool_production_previews = t

    tool_production_previews = fields.Many2many('mrp.tool.preview',
                                                string="Attrezzature Disponibili", compute=_get_tool_preview)

    @api.one
    @api.depends('mold_routing_id')
    def _get_workcenters(self):
        self.tool_workcenter_ids = self.mold_routing_id.workcenter_ids

    tool_workcenter_ids = fields.One2many('mrp.workcenter', compute=_get_workcenters,
                                          string=_("Workcenter Flow"),)

    @api.one
    @api.depends('mold_id')
    def _mould_product_domain(self):
        self.mould_routings = [(4, x) for x in self.mold_id.routings_ids.ids]
        self.product_molds = self.env['omnia_mold.mold_configuration'].search([('product_id', '=', self.product_id.id)]).mapped(lambda x: x.mold_id)

    mould_routings = fields.One2many('mrp.routing',
                                     compute=_mould_product_domain)

    product_molds = fields.One2many('maintenance.equipment',
                                    compute=_mould_product_domain)

    @api.onchange('product_qty')
    def onChangeProductQty(self):
        if self.mold_id:
            n_traces = self.getNImpronte(self.product_id)
            n_shut = self.product_qty / n_traces
            suggested_qty = int(n_shut) * n_traces
            if n_shut - int(n_shut) > 0.0001:
                raise UserError("Insert exact shut multiple of %r Suggested value %r" % (n_traces, suggested_qty))

    @api.onchange('mold_id')
    def onChangeMoldId(self):
        self.onChangeProductQty()

    @api.onchange('product_id')
    def fillUpMold(self):
        super(MrpProduction, self).onchange_product_id()
        self.onChangeProductQty()
        self.mold_id = False
        self.mold_routing_id = False
        self.tool_workcenter_ids = False
        self.bom_id = False
        self._msg_mold()
        if not self.product_id:
            logging.warning("No Product id found for mrp_production %r" % self.id)
            return
        self.bom_id = False

        configuration = self.env['omnia_mold.mold_configuration'].search([('product_id', '=', self.product_id.id)], limit=1)
        if configuration:
            mold = configuration[0].mold_id
            self.mold_id = mold
            logging.warning(mold.name)
            if mold.routings_ids:
                self.mold_routing_id = mold.routings_ids[0]
                logging.warning(self.mold_routing_id.name)
            self._mould_product_domain()
            return
        logging.warning("no mold found for mrp_production %r" % self.id)

    @api.one
    def _msg_mold(self):
        possible_mold = ""
        computed = []
        for mold in self.env['omnia_mold.mold_configuration'].search([('product_id', '=', self.product_id.id)]):
            mold_id = mold.mold_id
            if not mold_id or mold_id.id in computed:
                continue
            products = mold_id.mold_configuration.mapped(lambda x: "[%s]" % x.product_id.default_code)
            msg_mold = _("Mold no. %s with Products: %s" % (mold_id.name, ",".join(products)))
            possible_mold = possible_mold + (_(r'<div style="margin: 5px">%r </div></br>' % msg_mold))
            computed.append(mold_id.id)
        if len(possible_mold) > 0:
            possible_mold = _(r'<div style="margin: 5px">You can produce this product with the following tools</div></br>') + possible_mold
        self.msg_mold = possible_mold
    msg_mold = fields.Html(compute=_msg_mold)

    @api.multi
    def button_plan(self):
        res = super(MrpProduction, self).button_plan()
        if not self.def_date_planned_start:
            self.def_date_planned_start = self.date_planned_start
        if not self.def_date_planned_finished:
            self.def_date_planned_finished = self.date_planned_finished
        return res

    @api.one
    @api.depends('mold_id')
    def _mold_status(self):
        self.mould_cavity_close = self.mold_id.have_cavity_closed()
        self.mould_maintenance = self.mold_id.have_active_maintenance()
        self.mold_product_ids = self.mold_id.mold_configuration.mapped(lambda x: x.product_id.id)

    mold_product_ids = fields.Many2many('product.product',
                                        compute=_mold_status,
                                        string=_("Prodotti stampo"),
                                        store=False)
    mould_maintenance = fields.Boolean(compute=_mold_status)
    mould_cavity_close = fields.Boolean(compute=_mold_status)

    @api.model
    def create(self, vals):
        obj = super(MrpProduction, self).create(vals)
        n_shut = obj.product_qty / self.getNImpronte(obj.product_id)
        createProjectFlag = eval(self.env["ir.config_parameter"].sudo().get_param(
            "CREATE_PROJECT_FROM_PRODUCTION",
            False,
        ))
        if createProjectFlag and not obj.project_id:
            accountObject = False
            if obj.origin:
                objOrder = self.env['sale.order'].search([('name', '=', obj.origin)])
                if objOrder.project_project_id:
                    accountObject = obj.project_id
            if not accountObject:
                accountObject = self.env['project.project'].create({'name': obj.name})
            if obj.mold_id:
                for activity in obj.mold_routing_id.operation_ids:
                    self.env['project.task'].create({'name': activity.name,
                                                     'project_id': accountObject.id})
            obj.project_id = accountObject
        if obj.mold_id:
            obj.routing_id = obj.mold_routing_id
            #
            # delete and create raw move
            #
            for move in obj.move_raw_ids:
                move._action_cancel()
                move.unlink()
            for cavity in obj.mold_id.mold_configuration:
                if not cavity.exclude:
                    for bom_id in cavity.product_id.bom_ids:
                        factor = 1  # production.product_uom_id._compute_quantity(production.product_qty, production.bom_id.product_uom_id) / production.bom_id.product_qty
                        _boms, exploded_lines = bom_id.explode(cavity.product_id,
                                                               factor,
                                                               picking_type=bom_id.picking_type_id)
                        for bom_line, line_data in exploded_lines:
                            move = obj._generate_raw_move(bom_line, line_data)
                            move.product_uom_qty = n_shut * line_data.get('qty', 1)
                            move.unit_factor = line_data.get('qty', 1)
                        break
            if obj.mold_id.product_raw_sprue_id:
                obj._generate_materozza_raw_move(obj.mold_id.product_raw_sprue_qty,
                                                 n_shut,
                                                 obj.mold_id.product_raw_sprue_id,
                                                 obj.mold_id.product_raw_sprue_uom)
            obj._adjust_procure_method()
            for move in obj.move_raw_ids:
                if move.state == 'draft':
                    move._action_confirm()
            #
            # delete and create out product ids
            #
            for move in obj.move_finished_ids:
                move._action_cancel()
                move.unlink()
            for cavity in obj.mold_id.mold_configuration:
                if not cavity.exclude:
                    cavity._generate_finished_moves(obj)
            if obj.mold_id.product_raw_sprue_id:
                obj.mold_id._generate_sprue_finished_moves(obj)
        return obj

    def _generate_materozza_raw_move(self, quantity, n_shut, product_id, product_uom_id):
        # alt_op needed for the case when you explode phantom bom and all the lines will be consumed in the operation given by the parent bom line
        if self.routing_id:
            routing = self.routing_id
        else:
            routing = self.bom_id.routing_id
        if routing and routing.location_id:
            source_location = routing.location_id
        else:
            source_location = self.location_src_id
        data = {
            'sequence': 100,
            'name': self.name,
            'date': self.date_planned_start,
            'date_expected': self.date_planned_start,
            'bom_line_id': False,
            'product_id': product_id.id,
            'product_uom_qty': quantity * n_shut,
            'product_uom': product_uom_id.id,
            'location_id': source_location.id,
            'location_dest_id': self.product_id.property_stock_production.id,
            'raw_material_production_id': self.id,
            'company_id': self.company_id.id,
            'operation_id': False,
            'price_unit': product_id.standard_price,
            'procure_method': 'make_to_stock',
            'origin': self.name,
            'warehouse_id': source_location.get_warehouse().id,
            'group_id': self.procurement_group_id.id,
            'propagate': self.propagate,
            'unit_factor': quantity,
            'is_materozza': True,
        }
        return self.env['stock.move'].create(data)

    def _cal_price(self, consumed_moves):
        """Set a price unit on the finished move according to `consumed_moves`.
        """
        if not self.mold_id:
            return super(MrpProduction, self)._cal_price(consumed_moves)
        work_center_cost = 0
        finished_moves = self.move_finished_ids.filtered(lambda x: x.state not in ('done', 'cancel') and x.quantity_done > 0)
        for finished_move in finished_moves:
            #  finished_move.ensure_one()
            for work_order in self.workorder_ids:
                time_lines = work_order.time_ids.filtered(lambda x: x.date_end and not x.cost_already_recorded)
                duration = sum(time_lines.mapped('duration'))
                time_lines.write({'cost_already_recorded': True})
                work_center_cost += (duration / 60.0) * work_order.workcenter_id.costs_hour
            if finished_move.product_id.cost_method in ('fifo', 'average'):
                qty_done = finished_move.product_uom._compute_quantity(finished_move.quantity_done, finished_move.product_id.uom_id)
                finished_move.price_unit = (sum([-m.value for m in consumed_moves]) + work_center_cost) / qty_done
                finished_move.value = sum([-m.value for m in consumed_moves]) + work_center_cost
        return True

    @api.multi
    def _generate_workorders(self, exploded_boms):
        workorders = self.env['mrp.workorder']
        original_one = False
        for bom, bom_data in exploded_boms:
            # If the routing of the parent BoM and phantom BoM are the same, don't recreate work orders, but use one master routing
            if (bom.routing_id.id and (not bom_data['parent_line'] or bom_data['parent_line'].bom_id.routing_id.id != bom.routing_id.id)) or self.routing_id:
                temp_workorders = self._workorders_create(bom, bom_data)
                workorders += temp_workorders
                if temp_workorders:  # In order to avoid two "ending work orders"
                    if original_one:
                        temp_workorders[-1].next_work_order_id = original_one
                    original_one = temp_workorders[0]
        return workorders

    def _workorders_create(self, bom, bom_data):
        if self.mold_id:
            return self._workorders_create_mold()
        else:
            return super(MrpProduction, self)._workorders_create(bom, bom_data)

    def _workorders_create_mold(self):
        """
        :param bom: in case of recursive boms: we could create work orders for child
                    BoMs
        """
        workorders = self.env['mrp.workorder']

        # Initial qty producing
        if self.product_id.tracking == 'serial':
            quantity = 1.0
        else:
            quantity = self.product_qty - sum(self.move_finished_ids.mapped('quantity_done'))
            quantity = quantity if (quantity > 0) else 0

        for operation in self.mold_routing_id.operation_ids:
            # create workorder
            cycle_number = math.ceil(quantity / self.getNImpronte(self.product_id))  # TODO: float_round UP
            duration_expected = (operation.workcenter_id.time_start +
                                 operation.workcenter_id.time_stop +
                                 operation.time_mount_machine +
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
            if len(workorders) == len(self.mold_routing_id.operation_ids):
                moves_raw |= self.move_raw_ids.filtered(lambda move: not move.operation_id)
            moves_finished = self.move_finished_ids.filtered(lambda move: move.operation_id == operation)  # TODO: code does nothing, unless maybe by_products?
            moves_raw.mapped('move_line_ids').write({'workorder_id': workorder.id})
            (moves_finished + moves_raw).write({'workorder_id': workorder.id})

            workorder._generate_lot_ids()
        return workorders

    @api.depends('move_finished_ids.move_line_ids')
    def _compute_lines(self):
        for production in self:
            if not production.mold_id:
                return super(MrpProduction, self)._compute_lines()
            lineIds = []
            for move in production.move_finished_ids:
                lineIds.extend(move.move_line_ids.ids)
            production.finished_move_line_ids = lineIds

    def getBomsFromMold(self, mold):
        outBoms = []
        for configBrws in mold.mold_configuration:
            productBrws = configBrws.product_id
            outBoms.extend(productBrws.bom_ids)
        return outBoms

    def explodeMoldBoms(self, order, qty=False):
        boms_tot = []
        lines_tot = []
        bomDictEvaluated = {}
        for bomBrws in self.getBomsFromMold(order.mold_id):
            if bomBrws.id in bomDictEvaluated.keys():
                bomLines, lines = bomDictEvaluated[bomBrws.id]
            else:
                if not qty:
                    qty = order.product_uom_id._compute_quantity(order.product_qty, order.bom_id.product_uom_id) / order.bom_id.product_qty
                bomLines, lines = bomBrws.explode(bomBrws.product_id, qty, picking_type=bomBrws.picking_type_id)
            boms_tot.extend(bomLines)
            lines_tot.extend(lines)
            bomDictEvaluated[bomBrws.id] = (bomLines, lines)
        return boms_tot, lines_tot

    @api.multi
    def getNImpronte(self, product_id):
        return len(self.mold_id.mold_configuration.filtered(lambda x: x.product_id == product_id and x.exclude is not True)) or 1

    @api.multi
    def post_inventory_product(self, product_id, qty):
        
        def getFinishedMovesByProd(moves, prodBrws):
            out = []
            for move in moves:
                if move.product_id.id == prodBrws.id and move.move_line_ids.qty_done:
                    out.append(move)
            return out
        
        def actionOnMove(move, qty, getResidual=False):
            if move.move_line_ids.qty_done == qty:
                move._action_done()
            else:
                if move.move_line_ids:
                    linesQty = move.move_line_ids.qty_done
                    if getResidual:
                        if qty > linesQty:
                            residualQty = qty - linesQty
                            move._action_done()
                            return residualQty
                        elif qty == linesQty:
                            move._action_done()
                            return residualQty
                        else:
                            residualQty = linesQty - qty
                            move.move_line_ids.qty_done = qty
                            move._action_done()
                            newMove = move.copy()
                            newMove.quantity_done += residualQty
                            newMove._action_confirm()
                    else:
                        total_qty = move.move_line_ids.qty_done - qty
                        move.move_line_ids.qty_done = qty
                        move._action_done()
                        newMove = move.copy()
                        newMove.quantity_done += total_qty
                        newMove._action_confirm()
                else:
                    # TODO: create the line move_line_ids
                    pass
            if getResidual:
                return 0
            
            
        out_lines = []
        for order in self:
            moves_not_to_do = order.move_raw_ids.filtered(lambda x: x.state == 'done')
            moves_to_do = order.move_raw_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
            for move in moves_to_do.filtered(lambda m: m.product_qty == 0.0 and m.quantity_done > 0):
                move.product_uom_qty += qty
                move._action_done()
            moves_to_do = order.move_raw_ids.filtered(lambda x: x.state == 'done') - moves_not_to_do
            order._cal_price(moves_to_do)
            moves_to_finish = order.move_finished_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
            finishedMoves = getFinishedMovesByProd(moves_to_finish, product_id)
            if len(finishedMoves) == 1:
                actionOnMove(finishedMoves[0], qty)
                out_lines.append(finishedMoves[0])
            elif len(finishedMoves) == 0:
                raise UserError(_("Il prodotto %s non è presente tra i prodotti finiti dell'ordine di produzione." % (product_id.display_name)))
            else:
                for move in finishedMoves:
                    qty = actionOnMove(move, int(qty), getResidual=True)
                    out_lines.append(move)
                    if not qty:
                        break
            order.action_assign()
            consume_move_lines = moves_to_do.mapped('active_move_line_ids')
            for moveline in moves_to_finish.mapped('active_move_line_ids'):
                if moveline.product_id.id == product_id.id:
                    if moveline.product_id == order.product_id and moveline.move_id.has_tracking != 'none':
                        if any([not ml.lot_produced_id for ml in consume_move_lines]):
                            raise UserError(_('You can not consume without telling for which lot you consumed it'))
                        # Link all movelines in the consumed with same lot_produced_id false or the correct lot_produced_id
                        filtered_lines = consume_move_lines.filtered(lambda x: x.lot_produced_id == moveline.lot_id)
                        moveline.write({'consume_line_ids': [(6, 0, [x for x in filtered_lines.ids])]})
                    else:
                        # Link with everything
                        moveline.write({'consume_line_ids': [(6, 0, [x for x in consume_move_lines.ids])]})
        return out_lines

    def get_kitting_lines(self):  # fixare
        return self.mold_id.toolkit_lines.filtered(lambda x: (x.workcenter_id in self.tool_workcenter_ids) or (x.workcenter_id is False))

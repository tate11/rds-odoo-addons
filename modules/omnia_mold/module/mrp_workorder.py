'''
Created on 20 Mar 2018

@author: mboscolo
'''
import datetime
from odoo import api
from odoo import fields
from odoo import models
from odoo import _
from odoo.tools import float_compare, float_round
from odoo.exceptions import UserError
import logging
from dateutil.relativedelta import relativedelta


class MrpWorkOrder(models.Model):
    _inherit = 'mrp.workorder'

    @api.multi
    def _getMold(self):
        for workorder in self:
            workorder.mold_id = workorder.production_id.mold_id

    mold_id = fields.Many2one('maintenance.equipment',
                              string="Mold",
                              compute=_getMold,
                              store=True)

    @api.multi
    def clientMachineRecordProduction(self, productedQty):
        try:
            for workOrder in self:
                if isinstance(productedQty, dict):
                    lossReasonId = productedQty['id_loss_reason']
                    timeline_obj = self.env['mrp.workcenter.productivity']
                    self.end_previous()
                    self.button_start()
                    productivityBrwsList = timeline_obj.search([('workorder_id', 'in', self.ids),
                                                                ('date_end', '=', False),
                                                                ('user_id', '=', self.env.user.id)])
                    for productivityBrws in productivityBrwsList:
                        productivityBrws.button_block()
                        productivityBrws.write({'date_end': False, 'loss_id': lossReasonId})
                elif workOrder.qty_produced + productedQty >= workOrder.qty_production:
                    workOrder.record_production()
                    workOrder.button_finish()
                else:
                    workOrder.qty_producing = productedQty
                    workOrder.record_production()
            return True
        except Exception as ex:
            logging.log(ex)

    @api.onchange('date_planned_start')
    def _date_planned_start(self):
        for workorder_id in self:
            workorder_id.date_planned_finished = fields.Datetime.from_string(workorder_id.date_planned_start) + relativedelta(minutes=workorder_id.duration_expected)

    @api.multi
    def plan_selected(self):
        """
            Plan the selected work order
        """
        ids = self.ids
        if len(ids) < 1:
            return False
        vals = {'from_date_plan': datetime.datetime.now(),
                'work_order_ids': [(6, 0, self.ids)]}
        wizard_id = self.env['workorder_replan'].create(vals)
        return {'name': _('Plan Tool'),
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'workorder_replan',
                'target': 'new',
                'res_id': wizard_id,
                'type': 'ir.actions.act_window',
                'domain': "[]"}

    # this fix a singleton bug tichet issiues : 1867625
    @api.multi
    def record_production(self):
        if not self.production_id.mold_id:
            return super(MrpWorkOrder, self).record_production()

        self.ensure_one()
        if self.qty_producing <= 0:
            raise UserError(_('Please set the quantity you are currently producing. It should be different from zero.'))

        if (self.production_id.product_id.tracking != 'none') and not self.final_lot_id and self.move_raw_ids:
            raise UserError(_('You should provide a lot/serial number for the final product'))

        # Update quantities done on each raw material line
        # For each untracked component without any 'temporary' move lines,
        # (the new workorder tablet view allows registering consumed quantities for untracked components)
        # we assume that only the theoretical quantity was used
        n_traces = self.production_id.getNImpronte(self.production_id.product_id)
        n_shut = self.qty_producing / n_traces
        if n_shut - int(n_shut) > 0.0001:
            raise UserError("Insert exact shut multiple of %r" % n_traces)
        # raw material transfers
        for move in self.move_raw_ids:
            if move.has_tracking == 'none' and (move.state not in ('done', 'cancel')) and (move.bom_line_id or move.is_materozza)\
                                and move.unit_factor and not move.move_line_ids.filtered(lambda ml: not ml.done_wo):
                rounding = move.product_uom.rounding
                qty_to_add = float_round(n_shut * move.unit_factor, precision_rounding=rounding)
                if self.product_id.tracking != 'none':
                    move._generate_consumed_move_line(qty_to_add, self.final_lot_id)
                else:
                    move.quantity_done += qty_to_add
        # Transfer quantities from temporary to final move lots or make them final
        for move_line in self.active_move_line_ids:
            # Check if move_line already exists
            if move_line.qty_done <= 0:  # rounding...
                move_line.sudo().unlink()
                continue
            if move_line.product_id.tracking != 'none' and not move_line.lot_id:
                raise UserError(_('You should provide a lot/serial number for a component'))
            # Search other move_line where it could be added:
            lots = self.move_line_ids.filtered(lambda x: (x.lot_id.id == move_line.lot_id.id) and (not x.lot_produced_id) and (not x.done_move) and (x.product_id == move_line.product_id))
            if lots:
                lots[0].qty_done += move_line.qty_done
                lots[0].lot_produced_id = self.final_lot_id.id
                move_line.sudo().unlink()
            else:
                move_line.lot_produced_id = self.final_lot_id.id
                move_line.done_wo = True

        # One a piece is produced, you can launch the next work order
        if self.next_work_order_id.state == 'pending':
            self.next_work_order_id.state = 'ready'

        self.move_line_ids.filtered(
            lambda move_line: not move_line.done_move and not move_line.lot_produced_id and move_line.qty_done > 0
        ).write({
            'lot_produced_id': self.final_lot_id.id,
            'lot_produced_qty': self.qty_producing
        })

        # If last work order, then post lots used
        # TODO: should be same as checking if for every workorder something has been done?
        if not self.next_work_order_id:
            product_ids = self.production_id.mold_product_ids.ids
            product_ids.append(self.production_id.mold_id.product_sprue_id.id)
            production_moves = self.production_id.move_finished_ids.filtered(lambda x: (x.product_id.id in product_ids) and (x.state not in ('done', 'cancel')))
            for production_move in production_moves:
                if production_move.product_id.tracking != 'none':
                    move_line = production_move.move_line_ids.filtered(lambda x: x.lot_id.id == self.final_lot_id.id)
                    if move_line:
                        move_line.product_uom_qty += n_shut
                        move_line.qty_done += n_shut
                    else:
                        move_line.create({'move_id': production_move.id,
                                          'product_id': production_move.product_id.id,
                                          'lot_id': self.final_lot_id.id,
                                          'product_uom_qty': n_shut,
                                          'product_uom_id': production_move.product_uom.id,
                                          'qty_done': self.qty_producing,
                                          'workorder_id': self.id,
                                          'location_id': production_move.location_id.id,
                                          'location_dest_id': production_move.location_dest_id.id})
                else:
                    if production_move.is_materozza:
                        production_move.quantity_done += n_shut
                    else:
                        production_move.quantity_done += n_shut
        # Update workorder quantity produced
        self.qty_produced += self.qty_producing
        # Set a qty producing
        rounding = self.production_id.product_uom_id.rounding
        if float_compare(self.qty_produced, self.production_id.product_qty, precision_rounding=rounding) >= 0:
            self.qty_producing = 0
        elif self.production_id.product_id.tracking == 'serial':
            self._assign_default_final_lot_id()
            self.qty_producing = 1.0
            self._generate_lot_ids()
        else:
            self.qty_producing = float_round(self.production_id.product_qty - self.qty_produced, precision_rounding=rounding)
            self._generate_lot_ids()
        if self.next_work_order_id and self.production_id.product_id.tracking != 'none':
            self.next_work_order_id._assign_default_final_lot_id()
        if float_compare(self.qty_produced, self.production_id.product_qty, precision_rounding=rounding) >= 0:
            self.button_finish()
        return True

# -*- coding: utf-8 -*-
# This file and any file found in child directories are part of RDS Moulding Technology SpA Addons for Odoo. 
# See LICENSE file in the parent folder for full copyright and licensing details.

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    @api.depends('name', 'client_order_ref')
    def name_get(self):
        res = []
        for order in self:
            name = (order.client_order_ref and ("[%s] " % order.client_order_ref) or "") + order.name
            res += [(order.id, name)]
        return res

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _get_line_index(self):
        for i in self:
            i.line_index = i.order_id.order_line.ids.index(i.id)
    line_index = fields.Integer("Line Index", compute=_get_line_index)

    @api.multi
    def _remaining_qty(self):
        for line in self:
            if not isinstance(line.product_uom_qty, bool) and not isinstance(line.qty_delivered, bool):
                line.remaining_qty = line.product_uom_qty - line.qty_delivered
                line.amt_to_deliver = isinstance(line.price_unit, float) and line.remaining_qty * line.price_unit
                
    remaining_qty = fields.Float("Qty to Deliver", compute=_remaining_qty)
    amt_to_deliver = fields.Float("Amt to Deliver", compute=_remaining_qty)

    def _get_pickings(self):
        Moves = self.env['stock.move']
        for line in self:
            line.picking_ids = Moves.search([('sale_line_id', '=', line.id)]).mapped(lambda x: x.picking_id)
    picking_ids = fields.Many2many('stock.picking', string="Pickings", compute=_get_pickings)

    def btn_view_pickings(self):
        '''
        This function returns an action that display existing picking orders of given purchase order ids.
        When only one found, show the picking immediately.
        '''
        action = self.env.ref('stock.action_picking_tree_all')
        result = action.read()[0]

        #override the context to get rid of the default filtering on operation type
        result['context'] = {}
        pick_ids = self.mapped('picking_ids')
        #choose the view_mode accordingly
        if not pick_ids or len(pick_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % (pick_ids.ids)
        elif len(pick_ids) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = pick_ids.id
        return result


            
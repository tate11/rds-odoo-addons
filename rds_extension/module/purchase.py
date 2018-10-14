'''
Created on 17 Jul 2018

@author: mboscolo
'''

import logging
from odoo import api
from odoo import fields
from odoo import models

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, float_compare
from datetime import datetime, timedelta, time


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = super(PurchaseOrderLine, self).onchange_product_id()
        if self.price_unit == 0.0:
            self.price_unit = self.product_id.standard_price
        return res

    @api.model
    def fix_subcontractiong_order(self):
        res = []
        stock_move_obj = self.env['stock.move']
        product_product_obj = self.env['product.product']
        for purchase_line in self.search([('sub_move_line', '!=', False)]):
            stock_move_id = purchase_line.sub_move_line
            default_code = stock_move_id.product_id.default_code
            default_code = default_code[1:]
            products = product_product_obj.search([('default_code', 'ilike', '%' + default_code)])
            for spool_move in stock_move_obj.search([('mrp_production_id', '=', stock_move_id.mrp_production_id),
                                                     ('product_id', 'in', products.ids),
                                                     ('id', '!=', stock_move_id.id)]):
                spool_move.purchase_order_line_subcontracting_id = purchase_line.id
                res.append("move_id %r purchese.line.id %r" % (spool_move.id, purchase_line.id))
        return res

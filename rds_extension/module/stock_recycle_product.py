'''
Created on 3 Jul 2018

@author: mboscolo
'''
from odoo import api
from odoo import models
from odoo.exceptions import UserError


class StockRecicleProduct(models.Model):
    _inherit = "stock.recycle_product"

    @api.onchange('from_qty', 'from_product_id')
    def recalculateQty(self):
        _qty, product_id = self.from_product_id.calculateQuantityFromBom()
        self.to_product_id = product_id
        self.calculateQty()

    @api.one
    def calculateQty(self):
        qty, product_id = self.from_product_id.calculateQuantityFromBom(self.to_product_uom)
        if product_id:
            self.to_product_id = product_id
            self.to_qty = self.from_qty * qty
        else:
            UserError("Row material product not found")

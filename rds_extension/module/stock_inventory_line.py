'''
Created on 4 Jul 2018

@author: mboscolo
'''
from odoo import api
from odoo import fields
from odoo import models


class StockInventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

    @api.multi
    def _ramain_qty(self):
        for sil in self:
            sil.remain_qty = sil.theoretical_qty - sil.product_qty
    remain_qty = fields.Float(string="diff",
                              compute=_ramain_qty)
    note = fields.Text(string="Note")

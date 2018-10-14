'''
Created on 28 Jul 2018

@author: mboscolo
'''

from odoo import models
from odoo import fields
from odoo import _
from odoo import api


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.model
    def _commonCompute(self, useIVA=False):
        doneQty = self.quantity_done
        saleLineBrws = self.sale_line_id
        if saleLineBrws and doneQty:
            unitPrice = saleLineBrws.price_unit
            if useIVA:
                # This function is used from sale order line to compute price_subtotal
                # the price will be computed due to taxes
                taxes = saleLineBrws.tax_id.compute_all(unitPrice,
                                                saleLineBrws.order_id.currency_id,
                                                doneQty,
                                                product=saleLineBrws.product_id,
                                                partner=saleLineBrws.order_id.partner_shipping_id)
                return taxes.get('total_included', 0)
            else:
                return unitPrice * doneQty
        return 0

    @api.multi
    def _computePriceWithIVA(self):
        for moveBrws in self:
            moveBrws.price_with_iva = moveBrws._commonCompute(True)
    
    @api.multi
    def _computePriceWithoutIVA(self):
        for moveBrws in self:
            moveBrws.price_no_iva = moveBrws._commonCompute(False)
    
    main_partner_id = fields.Many2one('res.partner', related='picking_id.main_partner_id', store=True)
    price_with_iva = fields.Float(_('Prezzo IVA'), compute=_computePriceWithIVA)
    price_no_iva = fields.Float(_('Prezzo No IVA'), compute=_computePriceWithoutIVA)

    @api.multi
    def getSaleLineMsg(self):
        def emptyIfFalse(value):
            if not value:
                return ""
            return str(value)

        sale_order_line = self.sale_line_id
        if sale_order_line:
            sale_order = sale_order_line.order_id
            if sale_order:
                return _("Order: ") + emptyIfFalse(sale_order.name) + _(" - Customer.O: ") + emptyIfFalse(sale_order.client_order_ref) + _(" Date: ") + emptyIfFalse(sale_order.date_order).split(" ")[0]
        return ""

    @api.model
    def getChildProduct(self, startProd, strFilter, recursive=True):
        bomLines = []
        for bomBrws in startProd.bom_ids:
            if bomBrws.active:
                bomLines.extend(bomBrws.bom_line_ids)
                for bomLineBrws in bomBrws.bom_line_ids:
                    if bomLineBrws.product_id.default_code.startswith(strFilter):
                        return bomLineBrws.product_id, bomLineBrws.product_qty
        for bomLineBrws in bomLines:
            prodBrws, qty = self.getChildProduct(bomLineBrws.product_id, strFilter, recursive)
            if prodBrws:
                return prodBrws, qty
        return self.env['product.product'], 1

    @api.multi
    def getRawTotalPlusWastage(self):
        total = self.getRawTotal()
        if total is None:
            return total
        if total > 0:
            total = total / 1000.0
        return total * 1.05

    @api.multi
    def getRawTotal(self):
        outWeight = None
        if self.picking_id and self.picking_id.partner_id.effective_consumed_material and self.product_id.default_code.startswith('A'):
            eprod, multiplier1 = self.getChildProduct(self.product_id, 'E')
            grezzo, multiplier2 = self.getChildProduct(eprod, '9', recursive=False)
            if grezzo:
                outWeight = multiplier1 * multiplier2 * (grezzo.weight or 1)
                return self.quantity_done * outWeight
        return outWeight
# 
#     @api.model
#     def changeMoveLocation(self, move_id, location_id):
#         for move in self.search([('id', '=', move_id)]):
#             qty_done = move.qty_done
#             move.qyt_done = 0
#             move.action_cancel()
#             new_move = move.copy({'location_des_id': location_id})
#             new_move.qty_done = qty_done
#             new_move.confirm()

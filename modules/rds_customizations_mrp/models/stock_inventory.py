# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    selected_line = fields.Many2one('stock.inventory.line', "Selected Line")

    def _add_product(self, product, qty=1.0):
        corresponding_line = self.line_ids.filtered(lambda r: r.product_id.id == product.id and (self.scan_location_id.id == r.location_id.id or not self.scan_location_id))
        if corresponding_line:
            if self.selected_line == corresponding_line[0]:
                corresponding_line[0].product_qty += qty
            else:
                self.selected_line = corresponding_line[0]
        else:
            StockQuant = self.env['stock.quant']
            company_id = self.company_id.id
            if not company_id:
                company_id = self._uid.company_id.id
            dom = [('company_id', '=', company_id), ('location_id', '=', self.scan_location_id.id or self.location_id.id), ('lot_id', '=', False),
                        ('product_id','=', product.id), ('owner_id', '=', False), ('package_id', '=', False)]
            quants = StockQuant.search(dom)
            th_qty = sum([x.quantity for x in quants])
            newline = self.line_ids.new({
                'location_id': self.scan_location_id.id or self.location_id.id,
                'product_id': product.id,
                'product_uom_id': product.uom_id.id,
                'theoretical_qty': th_qty,
                'product_qty': qty,
            })
            self.line_ids += newline
            self.selected_line = newline
        return True

    def on_barcode_scanned(self, barcode):
        import logging
        logging.warning(barcode)
        product = self.env['product.product'].search([('barcode', '=', barcode)])
        if product:
            self._add_product(product)
            return

        product_packaging = self.env['product.packaging'].search([('barcode', '=', barcode)])
        if product_packaging.product_id:
            self._add_product(product_packaging.product_id, product_packaging.qty)
            return

        location = self.env['stock.location'].search([('barcode', '=', barcode)])
        if location:
            self.scan_location_id = location[0]
            return
        
        try:
            if int(barcode) and self.selected_line:
                line = self.selected_line

                if line.product_qty > 1:
                    line.product_qty += int(barcode)
                else:
                    line.product_qty = int(barcode)
        except ValueError:
            return
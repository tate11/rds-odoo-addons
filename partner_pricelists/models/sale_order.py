# -*- coding: utf-8 -*-
# Part of RDS Moulding Technology SpA Addons for Odoo. See LICENSE file in the parent folder for full copyright and licensing details.


from odoo import api, fields, models

class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = 'sale.order'

    @api.depends('order_line.is_on_pricelist')
    def compute_is_on_pricelist(self):
        for i in self:
            i.is_on_pricelist = (i.partner_pricelist_id and i.partner_pricelist_id.enforce_lots) and (not any([(not x.is_on_pricelist) for x in i.order_line]))

    partner_pricelist_id = fields.Many2one('partner.pricelist', string='Partner Pricelist', store=True, compute='get_partner_pricelist', help="Partner pricelist for current sales order.")
    pricelist_id = fields.Many2one(string="Regional Pricelist")
    is_on_pricelist = fields.Boolean(compute=compute_is_on_pricelist)

    @api.depends('partner_id')
    def get_partner_pricelist(self):
        for i in self:
            pl = self.env['partner.pricelist'].search([('partner_id', '=', i.partner_id.id), ('state', '=', 'done')], limit=1)
            i.partner_pricelist_id = pl and pl[0] or False

class SaleOrderLine(models.Model):
    _inherit = ['sale.order.line']

    @api.depends('product_id','order_id.partner_id')
    def compute_product_code(self):
        for i in self:
            i.product_customer_ref = i.product_id.get_customer_ref(i.order_id.partner_id)
    
    product_customer_ref = fields.Char(string='Customer Product Ref.', compute=compute_product_code)


    @api.depends('product_uom_qty','price_unit','order_id.pricelist_id')
    def compute_is_on_pricelist(self):
        for i in self:
            if (not i.partner_pricelist_id) or (i.partner_pricelist_id and i.partner_pricelist_id.enforce_lots):
                i.is_on_pricelist = True
                continue

            if i.product_id:
                pl = i.partner_pricelist_id

                valid_lines = pl.pricelist_lines.filtered(lambda x: (x.product_id.id == i.product_id.id) and (x.lot_size <= i.product_uom._compute_quantity(i.product_uom_qty, i.product_id.uom_id))).sorted(lambda x: -x.lot_size)
                
                product = i.product_id.with_context(
                    lang=i.order_id.partner_id.lang,
                    partner=i.order_id.partner_id.id,
                    quantity=i.product_uom_qty,
                    date=i.order_id.date_order,
                    pricelist=i.order_id.pricelist_id.id,
                    uom=i.product_uom.id
                )

                display_price = i._get_display_price(product)

                if valid_lines and (round(display_price, 4) == round(i.price_unit, 4)):
                    i.is_on_pricelist = True
                else:
                    i.is_on_pricelist = False

    partner_pricelist_id = fields.Many2one('partner.pricelist', related='order_id.partner_pricelist_id')
    is_on_pricelist = fields.Boolean(compute=compute_is_on_pricelist)
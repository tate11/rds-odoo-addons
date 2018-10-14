# -*- coding: utf-8 -*-
# Part of RDS Moulding Technology SpA Addons for Odoo. See LICENSE.md file in the parent folder for full copyright and licensing details.


from odoo import api, fields, models, tools, _

class ProductTemplate(models.Model):
    _inherit = ['product.template']
    partner_pricelist_lines = fields.One2many('partner.pricelist.line', string='Partner Pricelist Lines', compute="get_partner_pricelist_lines")

    @api.multi
    def get_partner_pricelist_lines(self):
        for i in self:
            i.partner_pricelist_lines = self.env['product.product'].search([('product_tmpl_id', '=', i.id)]).mapped(lambda x: x.partner_pricelist_lines)

    @api.multi
    def price_compute(self, price_type, uom=False, currency=False, company=False):
        # TDE FIXME: delegate to template or not ? fields are reencoded here ...
        # compatibility about context keys used a bit everywhere in the code
        if not uom and self._context.get('uom'):
            uom = self.env['product.uom'].browse(self._context['uom'])
        if not currency and self._context.get('currency'):
            currency = self.env['res.currency'].browse(self._context['currency'])
        
        if price_type == 'partner_pricelist':
            partner_pricelist = (self._context.get('partner') and self.env['partner.pricelist'].search([('partner_id', '=', self._context.get('partner')), ('state', '=', 'done')])) or None

            if partner_pricelist:
                results = dict()
                for product in self:
                    results[product.id] = partner_pricelist.get_product_price(product, product._context.get('quantity') if not uom else uom._compute_quantity(product._context.get('quantity'), product.uom_id)) or results.get(product.id, 0)
                    if results[product.id] == None:
                        results[product.id] = super(ProductTemplate, product).price_compute('list_price', uom, currency, company)
                
                return results

        return super(ProductTemplate, self).price_compute('list_price', uom, currency, company)

class ProductProduct(models.Model):

    _inherit = ['product.product']

    partner_pricelist_lines = fields.One2many('partner.pricelist.line', string='Partner Pricelist Lines', compute="get_partner_pricelist_lines")

    @api.multi
    def get_partner_pricelist_lines(self):
        for i in self:
            i.partner_pricelist_lines = self.env['partner.pricelist.line'].search([('product_id', '=', i.id), ('state', '=', 'done')])

    def get_customer_ref(self, customer=False):
        if customer:
            pl_line = self.partner_pricelist_lines.filtered(lambda x: x.partner_id == customer)
            return (pl_line and pl_line[0].customer_ref) or ""

    @api.multi
    def price_compute(self, price_type, uom=False, currency=False, company=False):
        # TDE FIXME: delegate to template or not ? fields are reencoded here ...
        # compatibility about context keys used a bit everywhere in the code
        if not uom and self._context.get('uom'):
            uom = self.env['product.uom'].browse(self._context['uom'])
        if not currency and self._context.get('currency'):
            currency = self.env['res.currency'].browse(self._context['currency'])
        
        if price_type == 'partner_pricelist':
            partner_pricelist = (self._context.get('partner') and self.env['partner.pricelist'].search([('partner_id', '=', self._context.get('partner')), ('state', '=', 'done')])) or None

            if partner_pricelist:
                results = dict()
                for product in self:
                    results[product.id] = partner_pricelist.get_product_price(product, product._context.get('quantity') if not uom else uom._compute_quantity(product._context.get('quantity'), product.uom_id)) or results.get(product.id, 0)
                    if results[product.id] == None:
                        results[product.id] = super(ProductProduct, product).price_compute('list_price', uom, currency, company)
                
                return results

        return super(ProductProduct, self).price_compute('list_price', uom, currency, company)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        result = super(ProductProduct, self).name_search(name, args, operator, limit)

        if not result:
            customers = self.env['partner.pricelist.line'].search([
                ('customer_ref', operator, name)])
            if customers:
                products = customers.mapped(lambda x: x.product_id)
                result = products.name_get()

        return result
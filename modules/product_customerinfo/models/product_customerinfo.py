# Intended for sole use by RDS Moulding Technology SpA. See README file.

from odoo import api, fields, models
import logging

class ProductCustomerInfo(models.Model):
    _name = 'product.customerinfo'
    _description = 'Product description for a specific customer'
    
    name = fields.Many2one('res.partner', "Partner", domain=[('customer', '=', True)])
    description = fields.Char("Description")
    code = fields.Char("Code")

    product_tmpl_id = fields.Many2one('product.template', "Product", required=True)
    product_id = fields.Many2one('product.product', "Product Variant", domain=lambda x: [('product_tmpl_id', '=', x.product_tmpl_id.id)])

    notes = fields.Text("Notes")


class ProductTemplate(models.Model):
    _inherit = "product.template"

    customers_ids = fields.One2many('product.customerinfo', 'product_tmpl_id', "Customer-specific Info")
    variant_customers_ids = fields.One2many('product.customerinfo', 'product_tmpl_id')

    def _search_product_partner(self, operator, value):
        positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']

        if value == False:
            cinfo = self.env['product.customerinfo'].search([])
            tmpl_ids = [x.product_tmpl_id.id for x in cinfo]
            if operator in positive_operators:
                return [('id', 'not in', tmpl_ids)]
            return [('id', 'in', tmpl_ids)]

        if operator in positive_operators:
            cinfo = self.env['product.customerinfo'].search([('name', operator, value)])
            tmpl_ids = [x.product_tmpl_id.id for x in cinfo]
            return [('id', 'in', tmpl_ids)]
        else:
            cinfo = self.env['product.customerinfo'].search([('name', 'not like', '%{}%'.format(value))])
            tmpl_ids = [x.product_tmpl_id.id for x in cinfo]
            return [('id', 'not in', tmpl_ids)]

    partner_id = fields.Many2many('res.partner', "Customer", store=False, compute=lambda x: False, search=_search_product_partner)

class ProductProduct(models.Model):
    _inherit = "product.product"

    variant_customers_ids = fields.One2many('product.customerinfo', 'product_id',  "Customer-specific Info")

    def _search_product_partner(self, operator, value):
        positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']

        if value == False:
            cinfo = self.env['product.customerinfo'].search([])
            tmpl_ids = [x.product_tmpl_id.id for x in cinfo]
            if operator in positive_operators:
                return [('product_tmpl_id', 'not in', tmpl_ids)]
            return [('product_tmpl_id', 'in', tmpl_ids)]

        if operator in positive_operators:
            cinfo = self.env['product.customerinfo'].search([('name', operator, value)])
            tmpl_ids = [x.product_tmpl_id.id for x in cinfo]
            return [('product_tmpl_id', 'in', tmpl_ids)]
        else:
            cinfo = self.env['product.customerinfo'].search([('name', 'not like', '%{}%'.format(value))])
            tmpl_ids = [x.product_tmpl_id.id for x in cinfo]
            return [('product_tmpl_id', 'not in', tmpl_ids)]

    partner_id = fields.Many2many('res.partner', "Customer", store=False, compute=lambda x: False, search=_search_product_partner)
    
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        result = super(ProductProduct, self)._name_search(name, args, operator, limit, name_get_uid)
        if self._context.get('partner_id'):
            customers_ids = self.env['product.customerinfo']._search([
                ('name', '=', self._context.get('partner_id')),
                '|',
                ('code', operator, name),
                ('description', operator, name)], access_rights_uid=name_get_uid)
            if customers_ids:
                product_ids = self._search([('variant_customers_ids', 'in', customers_ids)], limit=limit, access_rights_uid=name_get_uid)
                if not product_ids:
                    product_ids = self._search([('product_tmpl_id.customers_ids', 'in', customers_ids)], limit=limit, access_rights_uid=name_get_uid)
                result += self.browse(product_ids).name_get()

        return result

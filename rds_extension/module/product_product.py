'''
Created on 3 Jul 2018

@author: mboscolo
'''
import re
import logging
from odoo import api
from odoo import fields
from odoo import models
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, float_compare
from datetime import datetime, timedelta, time


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def calculateQuantityFromBom(self, origin_uom=False):
        for bom_id in self.bom_ids:
            for bom_line_id in bom_id.bom_line_ids:
                if len(bom_line_id.product_id.bom_ids) > 0:
                    return bom_line_id.product_id.calculateQuantityFromBom(origin_uom)
                else:
                    if str(bom_line_id.product_id.default_code).startswith("905"):
                        product_id = bom_line_id.product_id
                        qty = bom_line_id.product_qty
                        if origin_uom:
                            qty = bom_line_id.product_uom_id._compute_quantity(qty, origin_uom)
                        return qty, product_id
        return 0, self.env['product.product']

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if not args:
            args = []
        if name:
            positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
            products = self.env['product.product']
            if operator in positive_operators:
                products = self.search([('default_code', '=', name)] + args, limit=limit)
                if not products:
                    products = self.search([('barcode', '=', name)] + args, limit=limit)
            if not products and operator not in expression.NEGATIVE_TERM_OPERATORS:
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                products = self.search(args + [('default_code', operator, name)], limit=limit)
                if not limit or len(products) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    limit2 = (limit - len(products)) if limit else False
                    products += self.search(args + [('name', operator, name), ('id', 'not in', products.ids)], limit=limit2)
            elif not products and operator in expression.NEGATIVE_TERM_OPERATORS:
                products = self.search(args + ['&', ('default_code', operator, name), ('name', operator, name)], limit=limit)
            if not products and operator in positive_operators:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    products = self.search([('default_code', '=', res.group(2))] + args, limit=limit)
            # still no results, partner in context: search on supplier info as last hope to find something
            if not products and self._context.get('partner_id'):
                suppliers = self.env['product.supplierinfo'].search([
                    ('name', '=', self._context.get('partner_id')),
                    '|',
                    ('product_code', operator, name),
                    ('product_name', operator, name)])
                if suppliers:
                    products = self.search([('product_tmpl_id.seller_ids', 'in', suppliers.ids)], limit=limit)

            if not products:
                customers = self.env['partner.pricelist.line'].search([
                    ('customer_ref', operator, name)])
                if customers:
                    products = customers.mapped(lambda x: x.product_id)

        else:
            products = self.search(args, limit=limit)
        return products.name_get()

# -*- coding: utf-8 -*-
# This file and any file found in child directories are part of RDS Moulding Technology SpA Addons for Odoo. 
# See LICENSE.md file in the parent folder for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare
from odoo.addons import decimal_precision as dp

class BomSupplierInfo(models.Model):
    _name = "bom.supplierinfo"
    _description = "Subcontracting Supplier Info."
    _order = 'sequence, min_qty desc, price'

    name = fields.Many2one(
        'res.partner', 'Vendor',
        domain=[('supplier', '=', True)], ondelete='cascade', required=True,
        help="Vendor of this product")
    product_name = fields.Char(
        'Vendor Service Name',
        help="This vendor's service name will be used when printing a request for quotation. Keep empty to use the internal one.")
    product_code = fields.Char(
        'Vendor Service Code',
        help="This vendor's service code will be used when printing a request for quotation. Keep empty to use the internal one.")
    sequence = fields.Integer(
        'Sequence', default=1, help="Assigns the priority to the list of product vendor.")
    product_uom = fields.Many2one(
        'product.uom', 'Vendor Unit of Measure',
        readonly="1", related='bom_id.product_uom_id',
        help="This comes from the product form.")
    min_qty = fields.Float(
        'Minimal Quantity', default=0.0, required=True,
        help="The minimal quantity to purchase from this vendor, expressed in the vendor Product Unit of Measure if not any, in the default unit of measure of the product otherwise.")
    price = fields.Float(
        'Price', default=0.0, digits=dp.get_precision('Product Price'),
        required=True, help="The price to purchase a product")
    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env.user.company_id.id, index=1)
    currency_id = fields.Many2one(
        'res.currency', 'Currency',
        default=lambda self: self.env.user.company_id.currency_id.id,
        required=True)
    bom_id = fields.Many2one('mrp.bom', string='Bom ID', index=True, ondelete='cascade',
                              help="BOM this subcontracting info refers to.")
    product_tmpl_id = fields.Many2one(
        'product.template', string='Subcontracting Service', help="Service product to be used on sale orders.")

    #date_start = fields.Date('Start Date', help="Start date for this vendor price")              # NYI
    #date_end = fields.Date('End Date', help="End date for this vendor price")
    #product_id = fields.Many2one(
    #    'product.product', 'Product Variant',
    #    help="If not set, the vendor price will apply to all variants of this products.")
    #product_variant_count = fields.Integer('Variant Count', related='product_tmpl_id.product_variant_count')
    #delay = fields.Integer(
    #    'Delivery Lead Time', default=1, required=True,
    #    help="Lead time in days between the confirmation of the purchase order and the receipt of the products in your warehouse. Used by the scheduler for automatic computation of the purchase order planning.")

    @api.multi
    def name_get(self):
        result = []
        for i in self:
            if i.bom_id:
                result.append((i.id, "{}: {}/{}".format(i.name.name, i.product_tmpl_id.name, i.product_name)))
            else:
                result.append((i.id, i.product_name))
        return result


class MrpBom(models.Model):
    _inherit = 'mrp.bom'
    
    seller_ids = fields.One2many('bom.supplierinfo', 'bom_id', 'Subcontracting Info')
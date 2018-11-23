from odoo import api, fields, models, _

class ProductProduct(models.Model):
    _inherit = 'product.product'

    sale_ok = fields.Boolean('Can be Sold', default=True)
    purchase_ok = fields.Boolean('Can be Purchased', default=True)
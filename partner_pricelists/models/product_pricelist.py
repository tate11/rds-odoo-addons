# -*- coding: utf-8 -*-
# Part of RDS Moulding Technology SpA Addons for Odoo. See LICENSE.md file in the parent folder for full copyright and licensing details.

from odoo import api, fields, models, tools, _

class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    base = fields.Selection(selection_add=[('partner_pricelist', 'Partner Pricelist')])
# -*- coding: utf-8 -*-
# This file and any file found in child directories are part of RDS Moulding Technology SpA Addons for Odoo. 
# See LICENSE file in the parent folder for full copyright and licensing details.

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    requested_date = fields.Datetime(string="Requested Date", related="sale_line_id.requested_date",
                                     help="This is the date your customer wishes the products to be delivered on.")
                                     
    initial_commitment_date = fields.Datetime(string="Initial Commitment Date", related="sale_line_id.delivery_date",
                                     help="This is the date your sales department promised to the customer.")
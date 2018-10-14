# -*- coding: utf-8 -*-
# This file and any file found in child directories are part of RDS Moulding Technology SpA Addons for Odoo. 
# See LICENSE file in the parent folder for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    qty_to_deliver = fields.Float('Qty to Deliver', readonly=True)
    amt_to_deliver = fields.Float('Amount to Deliver', readonly=True)
    amt_delivered = fields.Float('Amount Delivered', readonly=True)

    def _select(self):
        return super(SaleReport, self)._select() + """,
            sum((l.product_uom_qty - l.qty_delivered) / u.factor * u2.factor) as qty_to_deliver,
            sum((l.price_unit * (l.product_uom_qty - l.qty_delivered) / u.factor * u2.factor) / COALESCE(cr.rate, 1.0)) as amt_to_deliver,
            sum((l.price_unit * l.qty_delivered / u.factor * u2.factor) / COALESCE(cr.rate, 1.0)) as amt_delivered
        """
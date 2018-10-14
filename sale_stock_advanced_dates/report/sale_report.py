# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    delivery_date = fields.Datetime('Delivery Date', readonly=True)
    requested_date = fields.Datetime('Requested Date', readonly=True)

    def _select(self):
        return super(SaleReport, self)._select() + """,
            (s.date_order + concat(l.customer_lead::text, ' day')::interval) as delivery_date,
            l.requested_date as requested_date
        """

    def _group_by(self):
        return super(SaleReport, self)._group_by() + """,
            l.customer_lead,
            (s.date_order + concat(l.customer_lead::text, ' day')::interval),
            l.requested_date
        """

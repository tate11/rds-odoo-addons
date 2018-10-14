# -*- coding: utf-8 -*-
# This file and any file found in child directories are part of RDS Moulding Technology SpA Addons for Odoo. 
# See LICENSE file in the parent folder for full copyright and licensing details.

from datetime import timedelta, datetime

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def product_id_change(self):
        result = super(SaleOrderLine, self).product_id_change()
        self.update({'customer_lead': self.product_id.sale_delay})
        self._get_delivery_date()
        
        return result

    @api.depends('customer_lead')
    def _get_delivery_date(self):
        for i in self:
            if i.customer_lead:
                order_date = datetime.strptime(i.order_id.date_order, DEFAULT_SERVER_DATETIME_FORMAT)
                i.delivery_date = (order_date + timedelta(days=i.customer_lead)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.one
    def _set_delivery_date(self):
        if self.delivery_date:
            order_date = datetime.strptime(self.order_id.date_order, DEFAULT_SERVER_DATETIME_FORMAT)
            line_delivery_date = datetime.strptime(self.delivery_date, DEFAULT_SERVER_DATETIME_FORMAT)
            self.write({'customer_lead': (line_delivery_date-order_date).days + (line_delivery_date-order_date).seconds/(3600*24)})
        else:
            self.write({'customer_lead': 0})

    delivery_date = fields.Datetime(string='Commitment Date', help="This is the date you pledge to deliver the products. It is calculated based on lead times.", required=True, inverse='_set_delivery_date', compute='_get_delivery_date')
    
    requested_date = fields.Datetime(string='Requested Date', help="This is the date your customer wishes the products to be delivered on.")
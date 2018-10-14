# -*- coding: utf-8 -*-
# Part of RDS Moulding Technology SpA Addons for Odoo. See LICENSE.md file in the parent folder for full copyright and licensing details.


from odoo import api, fields, models

#This keeps UTM info consistent regardless of user input.
class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = 'sale.order'

    @api.model
    def create(self, vals):
        a = super(SaleOrder, self).new(vals)

        if a.partner_pricelist_id:
            pl = a.partner_pricelist_id
            vals['opportunity_id'] = vals.get('opportunity_id') or pl.opportunity_id.id
            vals['campaign_id'] = vals.get('campaign_id') or pl.campaign_id.id
            vals['source_id'] = vals.get('source_id') or pl.source_id.id
            vals['medium_id'] = vals.get('medium_id') or pl.medium_id.id

        return super(SaleOrder, self).create(vals)


# -*- coding: utf-8 -*-
# Part of RDS Moulding Technology SpA Addons for Odoo. See LICENSE.md file in the parent folder for full copyright and licensing details.

from odoo import api, fields, models, _

class PartnerPricelist(models.Model):
    _name = "partner.pricelist"
    _inherit = ['partner.pricelist', 'utm.mixin']

    opportunity_id = fields.Many2one('crm.lead', string='Opportunity', domain="[('type', '=', 'opportunity')]")
# -*- coding: utf-8 -*-
# Part of RDS Moulding Technology SpA Addons for Odoo. See LICENSE.md file in the parent folder for full copyright and licensing details.

from odoo import api, fields, models, _

class Lead(models.Model):
    _inherit = ['crm.lead']

    @api.model
    def _get_pricelists_count(self):
        pl = self.env['partner.pricelist']
        for i in self:
            i.pricelists_count = pl.search_count([('opportunity_id', 'in', self.ids)])

    pricelists_count = fields.Integer(string='# of Pricelists', compute='_get_pricelists_count', readonly=True, copy=False)

    @api.multi
    def action_view_pricelists(self):
        self.ensure_one()
        action = self.env.ref('partner_pricelists.action_partner_pricelist').read()[0]
        action['domain'] = [('opportunity_id', 'in', self.ids)]
        action['context'] = {
                                'default_partner_id': self.partner_id.id,
                                'default_team_id': self.team_id.id,
                                'default_campaign_id': self.campaign_id.id,
                                'default_medium_id': self.medium_id.id,
                                'default_source_id': self.source_id.id,
                                'default_opportunity_id': self.id
                            }
        return action

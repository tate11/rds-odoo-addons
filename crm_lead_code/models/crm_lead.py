# -*- coding: utf-8 -*-
# This file and any file found in child directories are part of RDS Moulding Technology SpA Addons for Odoo. 
# See LICENSE file in the parent folder for full copyright and licensing details.

from odoo import api, fields, models, _

class Lead(models.Model):
    _inherit = ['crm.lead']

    code = fields.Char(string='Code', help="Lead reference code.", default=_('New'), readonly=False)

    @api.model
    def create(self, vals):
        if vals.get('code', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['code'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('crm.lead') or _('New')
            else:
                vals['code'] = self.env['ir.sequence'].next_by_code('crm.lead') or _('New')

        return super(Lead, self).create(vals)
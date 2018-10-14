# -*- coding: utf-8 -*-
# Part of RDS Moulding Technology SpA Addons for Odoo. See LICENSE.md file in the parent folder for full copyright and licensing details.


from odoo import api, fields, models

from datetime import datetime


class PartnerPricelistLock(models.TransientModel):
    _name = 'partner.pricelist.lock'

    def _compute_current_pl(self):
        self.old_pricelist_id = self.env['partner.pricelist'].search([('state','=','done'), ('partner_id', '=', self.partner_id.id)])

    def get_default_name(self):
        return self.env['ir.sequence'].sudo().next_by_code('partner.pricelist')

    pricelist_id = fields.Many2one('partner.pricelist', readonly=True)
    partner_id = fields.Many2one('res.partner', readonly=True)

    partner_name = fields.Char(related='partner_id.name', string="Partner Name", readonly=True)
    partner_code = fields.Char(related='partner_id.ref', readonly=True)

    
    pl_code = fields.Char(string='New Code', default=get_default_name)

    old_pricelist_id = fields.Many2one('partner.pricelist', compute=_compute_current_pl, readonly=True)
    copy_old_lines = fields.Boolean(string="Copy old lines", required=True, default=True)

    @api.multi
    def confirm_pricelist(self):
        if self.old_pricelist_id:
            if self.copy_old_lines:
                sets = self.pricelist_id.pricelist_lines.mapped(lambda x: (x.product_id, x.lot_size))

                for l in self.old_pricelist_id.pricelist_lines:
                    if not ( (l.product_id, l.lot_size) in sets):
                        l.copy_to_other(self.pricelist_id.id)

            self.old_pricelist_id.action_surpass()

        self.pricelist_id.write({'name': self.pl_code,
                                'state': 'done',
                                'activation_date': datetime.now()})


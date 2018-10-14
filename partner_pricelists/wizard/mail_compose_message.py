# -*- coding: utf-8 -*-
# Part of RDS Moulding Technology SpA Addons for Odoo. See LICENSE.md file in the parent folder for full copyright and licensing details.


from odoo import api, models


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def send_mail(self, auto_commit=False):
        obj = super(MailComposeMessage, self).send_mail(auto_commit=auto_commit)
        if self._context.get('default_model') == 'sale.order' and self._context.get('default_res_id') and self._context.get('mark_so_as_sent'):
            order = self.env['sale.order'].browse([self._context['default_res_id']])
            if order.state in ['draft', 'valid']:
                order.with_context(tracking_disable=True).state = 'sent'
            self = self.with_context(mail_post_autofollow=True)
        if self._context.get('default_model') == 'partner.pricelist' and self._context.get('default_res_id') and self._context.get('mark_pl_as_sent'):
            pl = self.env['partner.pricelist'].browse([self._context['default_res_id']])
            if pl.state in ['draft', 'valid']:
                pl.with_context(tracking_disable=True).state = 'sent'
            self = self.with_context(mail_post_autofollow=True)
        return obj

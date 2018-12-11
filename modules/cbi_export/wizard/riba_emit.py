# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class ForceRibaEmit(models.TransientModel):
    _name = "account.riba.emit"
    _description = "RiBa Emission Wizard"

    partner_bank_id = fields.Many2one('res.partner.bank', string='Bank Account', help='Bank Account Number to which the invoices will be paid.', required=True)
    force_reemit = fields.Boolean("Force Re-emission", help="Flag this field to re-emit already emitted invoices.")

    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id)

    state = fields.Selection([('prep', 'Preparing'), ('done', 'Done')], "State", readonly=True)
    count = fields.Integer("Done Ribas", readonly=True)
    total = fields.Float("Total Invoiced", readonly=True)

    @api.depends('force_reemit')
    def _get_emitted_invoices(self):
        if not self._context.get('active_ids', False):
            self.invoices_to_emit = False
        else:
            active = self.env['account.invoice'].browse(self._context.get('active_ids', []))
            todo = active.filtered(lambda x: (x.type in ["out_invoice", "out_refound"]) and (x.riba_state in (['todo'] + (['done'] if self.force_reemit else []))))

            if not todo:
                self.invoices_to_emit = False
            else:
                self.invoices_to_emit = todo

    invoices_to_emit = fields.Many2many('account.invoice', string='Emitted Invoice Account', compute=_get_emitted_invoices)

    def emit(self):
        for i in self.invoices_to_emit:
            i.partner_bank_id = self.partner_bank_id
            i.riba_state = "done"

        self = self.with_context(active_ids=self.invoices_to_emit.ids)
        a = self.env.ref('cbi_export.cdi_bank_riba').report_action(self.invoices_to_emit)

        self.state = 'done'
        self.count = len(self.invoices_to_emit)
        self.total = sum(self.invoices_to_emit.mapped(lambda x: x.amount_total_signed))
        return a
# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 KTec S.r.l.
#    (<http://www.ktec.it>).
#    @author: Luigi Di Naro
#
################################################################################

from odoo import models,fields, api, _
from odoo.exceptions import ValidationError


class SaleAdvancePaymentInv(models.TransientModel):

    _inherit = 'sale.advance.payment.inv'

    journal_id = fields.Many2one(
        'account.journal',
        domain=[('type', '=', 'sale')],
        string='Journal',
        help='Select a journal for this invoice(s).'
    )
    date_invoice = fields.Date(string='Invoice Date')

    @api.multi
    def _create_invoice(self, order, so_line, amount):

        invoice = super(SaleAdvancePaymentInv,self)._create_invoice(order, so_line, amount)
        if self.journal_id:
            invoice.journal_id = self.journal_id
        if self.date_invoice:
            invoice.date_invoice = self.date_invoice
        return invoice

    @api.multi
    def create_invoices(self):
        context_invoice = self.env.context
        if self.date_invoice or self.journal_id:
            context_invoice = self.env.context.copy()
            if self.journal_id:
                context_invoice['journal_id'] = self.journal_id
            if self.date_invoice:
                context_invoice['date_invoice'] = self.date_invoice
        return super(SaleAdvancePaymentInv,self.with_context(context_invoice)).create_invoices()


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def _prepare_invoice(self):

        invoice_vals = super(SaleOrder,self)._prepare_invoice()

        if self.fiscal_position_id and self.fiscal_position_id.sale_journal_id:
            invoice_vals['journal_id'] = self.fiscal_position_id.sale_journal_id.id

        if 'journal_id' in self.env.context:
            invoice_vals['journal_id'] = self.env.context['journal_id'].id
        if 'date_invoice' in self.env.context:
            invoice_vals['date_invoice'] = self.env.context['date_invoice']

        return invoice_vals

class FiscalPosition(models.Model):
    _name = 'account.fiscal.position'

    sale_journal_id = fields.Many2one('account.journal', 'Default Journal', domain=[('type', '=', 'sale')], help="Default sale invoicing journal for this fiscal position.")
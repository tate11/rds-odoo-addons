from odoo import models,fields, api, _
from odoo.exceptions import ValidationError

class FiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    sale_journal_id = fields.Many2one('account.journal', 'Default Sale Journal', domain=[('type', '=', 'sale')], help="Default sale invoicing journal for this fiscal position.")
    purchase_journal_id = fields.Many2one('account.journal', 'Default Purchase Journal', domain=[('type', '=', 'purchase')], help="Default purschase invoicing journal for this fiscal position.")


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super(AccountInvoice, self)._onchange_partner_id()

        if self.type in ['out_invoice', 'out_refund']:
            if self.fiscal_position_id and self.fiscal_position_id.sale_journal_id:
                self.journal_id = self.fiscal_position_id.sale_journal_id
        elif self.fiscal_position_id and self.fiscal_position_id.purchase_journal_id:
            self.journal_id = self.fiscal_position_id.purchase_journal_id

        return res

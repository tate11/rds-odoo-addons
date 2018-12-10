from odoo import api, exceptions, fields, models, _
from odoo.exceptions import UserError
import datetime as dt

def lj(st, lenght, fill='0'):
    st = st and str(st) or ""
    return st.ljust(lenght, fill)

def rj(st, lenght, fill='0'):
    st = st and str(st) or ""
    return st.rjust(lenght, fill)

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    riba_bank_id = fields.Many2one('res.bank', 'RiBa Bank')
    method = fields.Selection([('bank_transfer', 'Bank Transfer'), ('riba', 'RiBa'), ('other', 'Other')], string="Payment Method", readonly=True, related="payment_term_id.method"

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super(AccountInvoice, self)._onchange_partner_id()
        if self.partner_id.riba_bank_ids:
            self.riba_bank_id = self.partner_id.riba_bank_ids[0]
        return res


    @api.multi
    def cbi_IB(self):
        companies = self.mapped(lambda x: x.company_id)
        banks = self.mapped(lambda x: x.partner_bank_id)
        currencies = self.mapped(lambda x: x.currency_id)

        if any([len(x) > 1 for x in [companies, banks, currencies]]):
            raise UserError(_("You must pick invoices with the same company, bank, and currencies!"))
        
        inv = self[0]
        return """{}{}{}{}                                                                          {}      """.format(
                rj(inv.company_id.sia, 5),
                rj(inv.partner_bank_id.bank_abi, 5),
                dt.date.today().strftime("%d%m%y"),
                lj(inv.partner_bank_id.bank_id.name, 20, ' '),
                inv.currency_id.name[0:1])

    def cbi_14(self, line=False):
        return """            {}30000{}-{}{}{}{}{}            {}4{}      {}""".format(
            line and line[0].strftime("%d%m%y") or self.date_due.strftime("%d%m%y"),
            rj(int(line and line[1]*100 or self.amount_total*100), 13),
            rj(self.partner_bank_id.bank_abi, 5),
            rj(self.partner_bank_id.bank_cab, 5),
            lj(self.partner_bank_id.acc_number and self.partner_bank_id.acc_number.replace(' ', '')[-12], 12),
            rj(self.riba_bank_id.abi, 5),
            rj(self.riba_bank_id.cab, 5),
            rj(self.company_id.sia, 5),
            lj(self.partner_id.ref, 16),
            self.currency_id.name[0:1])

    def cbi_20(self):
        return "{}{}{}{}              ".format(
            lj(self.company_id.name, 24, ' '),
            lj(self.company_id.street, 24, ' '),
            lj(self.company_id.zip, 24, ' '),
            lj(' ', 24, ' ')
        )
        
    def cbi_30(self):
        return "{}{}                                  ".format(
            lj(self.partner_id.name, 60, ' '),
            lj(self.partner_id.vat, 16, ' ')
        )

    def cbi_40(self):
        return "{}{}{}{}".format(
            lj((self.partner_id.street or '') + ' ' + (self.partner_id.street2 or ''), 30, ' '),
            rj(self.partner_id.zip, 5, '0'),
            rj(self.partner_id.city, 25, ' '),
            lj(self.riba_bank_id.name, 50, ' ')
        )

    def cbi_50(self):
        return "{}          {}    ".format(
                lj(self.name, 80, ' '),
                lj(self.company_id.vat, 16, ' ')
            )

    def cbi_51(self):
        return "{}{}{}".format(
                rj('1800009999', 10),
                lj(self.company_id.name, 20, ' '),
                " " * 80
            )

    def cbi_70(self):
        return " " * 110

    def cbi_EF(self):
        inv = self[0]
        
        n_ribas = 0
        for i in self:
            if i.payment_term_id:
                n_ribas += len(i.payment_term_id.compute(1, i.invoice_date))
            else:
                n_ribas += 1

        return "{}{}{}{}      {}{}000000000000000{}                        {}      ".format(
                rj(inv.company_id.sia, 5), 
                rj(inv.partner_bank_id.bank_abi, 5),
                dt.date.today().strftime("%d%m%y"),
                lj(inv.partner_bank_id.bank_id.name, 20, ' '),
                rj(n_ribas, 7),
                rj(sum(self.mapped(lambda x: int(x.total*100))), 15),
                lj(n_ribas*7 + 2, 7),
                inv.currency_id.name[0:1]
        )
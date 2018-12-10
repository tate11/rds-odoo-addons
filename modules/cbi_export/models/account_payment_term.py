from odoo import api, exceptions, fields, models, _
from dateutil.relativedelta import relativedelta

class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    method = fields.Selection([('bank_transfer', 'Bank Transfer'), ('riba', 'RiBa'), ('other', 'Other')], string="Payment Method", required=True, default='bank_transfer')
from odoo import api, exceptions, fields, models, _
import datetime as dt

class ResPartner(models.Model):
    _inherit = "res.partner"

    riba_bank_ids = fields.Many2many('res.bank', 'riba_res_partner_res_bank', string="RiBa Banks")

class ResCompany(models.Model):
    _inherit = "res.company"

    sia = fields.Char("sia")
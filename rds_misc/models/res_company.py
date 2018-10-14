import base64
import os
import re

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError


class Company(models.Model):
    _inherit = "res.company"
    _description = 'Companies'
    _order = 'sequence, name'

    #name = fields.Char(related='partner_id.name', string='Company Name', required=True, store=True)
    #sequence = fields.Integer(help='Used to order Companies in the company switcher', default=10)
    #parent_id = fields.Many2one('res.company', string='Parent Company', index=True)
    #child_ids = fields.One2many('res.company', 'parent_id', string='Child Companies')
    #partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    #report_header = fields.Text(string='Company Tagline', help="Appears by default on the top right corner of your printed documents (report header).")
    #report_footer = fields.Text(string='Report Footer', translate=True, help="Footer text displayed at the bottom of all reports.")
    #logo = fields.Binary(related='partner_id.image', default=_get_logo, string="Company Logo")
    certificate_logo = fields.Binary(string="Company Certificates Logo")
    # logo_web: do not store in attachments, since the image is retrieved in SQL for
    # performance reasons (see addons/web/controllers/main.py, Binary.company_logo)
    #logo_web = fields.Binary(compute='_compute_logo_web', store=True)
    #currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self._get_user_currency())
    #user_ids = fields.Many2many('res.users', 'res_company_users_rel', 'cid', 'user_id', string='Accepted Users')
    #account_no = fields.Char(string='Account No.')
    #street = fields.Char(compute='_compute_address', inverse='_inverse_street')
    #street2 = fields.Char(compute='_compute_address', inverse='_inverse_street2')
    #zip = fields.Char(compute='_compute_address', inverse='_inverse_zip')
    #city = fields.Char(compute='_compute_address', inverse='_inverse_city')
    #state_id = fields.Many2one('res.country.state', compute='_compute_address', inverse='_inverse_state', string="Fed. State")
    #bank_ids = fields.One2many('res.partner.bank', 'company_id', string='Bank Accounts', help='Bank accounts related to this company')
    #country_id = fields.Many2one('res.country', compute='_compute_address', inverse='_inverse_country', string="Country")
    #email = fields.Char(related='partner_id.email', store=True)
    #phone = fields.Char(related='partner_id.phone', store=True)
    #website = fields.Char(related='partner_id.website')
    
    #vat = fields.Char(related='partner_id.vat', string="TIN")
    #company_registry = fields.Char()
    rea = fields.Char(string="R.E.A.")
    export = fields.Char(string="Export")

    #paperformat_id = fields.Many2one('report.paperformat', 'Paper format', default=lambda self: self.env.ref('base.paperformat_euro', raise_if_not_found=False))
    external_report_layout = fields.Selection(selection_add=[
        ('rds', 'Template RDS'),
    ])
    cap_soc = fields.Float(string="Capitale Sociale")

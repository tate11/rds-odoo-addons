# -*- coding: utf-8 -*-
# Part of RDS Moulding Technology SpA Addons for Odoo. See LICENSE.md file in the parent folder for full copyright and licensing details.


from odoo import api, fields, models, _

from datetime import datetime, timedelta

class PartnerPricelist(models.Model):
    _name = "partner.pricelist"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "Price List"
    _order = 'state, rfq_date desc, id desc'

    @api.model
    def _get_default_team(self):
        return self.env['crm.team']._get_default_team_id()

    def _get_default_currency_id(self):
        return self.env.user.company_id.currency_id.id

    @api.model
    def _get_sale_orders_count(self):
        orders = self.env['sale.order']
        for i in self:
            i.orders_count = orders.search_count(['&', ('state', 'in', ['sale', 'done']), ('partner_pricelist_id', 'in', self.ids)])

    @api.model
    def _get_quotations_count(self):
        orders = self.env['sale.order']
        for i in self:
            i.quotations_count = orders.search_count(['&', ('state', 'in', ['draft', 'sent']), ('partner_pricelist_id', 'in', self.ids)])

    @api.model
    def _get_lines_count(self):
        for i in self:
            i.lines_count = len(i.pricelist_lines)

    name = fields.Char(string='Pricelist Name', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
   
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True, states={'draft': [('readonly', False)]}, required=True, track_visibility='always')
    pricelist_lines = fields.One2many('partner.pricelist.line', 'pricelist_id', string='pricelist Items', readonly=True, states={'draft': [('readonly', False)]}, copy=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Offer Sent'),
        ('confirm', 'Pricelist Confirmed'),
        ('done', 'Active Pricelist'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, track_visibility='onchange', default='draft')

    #UTM
    origin = fields.Char(string='Source Document', help="Reference of the document that generated this sales order request.")
    customer_ref = fields.Char(string='Customer Reference', copy=False, readonly=True, states={'draft': [('readonly', False)]})
    team_id = fields.Many2one('crm.team', 'Sales Channel', change_default=True, default=_get_default_team, oldname='section_id')

    #Dates
    rfq_date = fields.Datetime(string='Customer Request Date', required=True, readonly=True, states={'draft': [('readonly', False)]}, copy=False, default=lambda x: fields.Datetime.now())
    sent_date = fields.Datetime(string='Sent Date', readonly=True, copy=False)

    validity_date = fields.Datetime(string='Expiration Date', readonly=True, states={'draft': [('readonly', False)]}, copy=False, help="Manually set the expiration date of your pricelist.")
    
    confirmation_date = fields.Datetime(string='Confirmation Date', readonly=True, help="Date on which the price list is confirmed.", copy=False)
    
    activation_date = fields.Datetime(string='Active Since', readonly=True, help="Date on which the price list was activated.", copy=False)
    end_date = fields.Datetime(string='Inactive Since', readonly=True, help="Date on which the price list expired.", copy=False)  

    #Company Fields
    user_id = fields.Many2one('res.users', string='Salesperson', index=True, track_visibility='onchange', default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('sale.order'))
    currency_id = fields.Many2one('res.currency', 'Currency', default=_get_default_currency_id, required=True)

    #Default terms
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms', oldname='payment_term', readonly=True, states={'draft': [('readonly', False)]})
    enforce_lots = fields.Boolean(string='Force Lots', readonly=True, states={'draft': [('readonly', False)]})

    #incoterm = fields.Many2one(
    #    'stock.incoterms', 'Incoterms',
    #    help="International Commercial Terms are a series of predefined commercial terms used in international transactions.")

    note = fields.Text('Notes', readonly=False)

    #Computed fields for buttons
    orders_count = fields.Integer(string='# of Orders', compute='_get_sale_orders_count', readonly=True, copy=False)
    quotations_count = fields.Integer(string='# of Quotations', compute='_get_quotations_count', readonly=True, copy=False)
    lines_count = fields.Integer(string='# of Lines', compute='_get_lines_count', readonly=True, copy=False)

    def action_view_lines(self):
        domain = [('pricelist_id', '=', self.ids[0])]
        context = dict(self.env.context or {})
        context['default_pricelist_id'] = self.ids[0]
        return {
            'name': 'Pricelist %s Lines' % self.name,
            'create': False,
            'domain': domain,
            'res_model': 'partner.pricelist.line',
            'type': 'ir.actions.act_window',
            'context': context,
            'view_id': False,
            'view_mode': (self.state == 'draft' and 'tree') or 'tree,form',
            'view_type': 'form',
            'help': '''<p class="oe_view_nocontent_create">
                        Here you can find the pricelist lines for this partner pricelist.
                    </p>''',
            'limit': 80,
        }

    def action_view_orders(self):
        action = self.env.ref('sale.action_orders').read()[0]
        action['domain'] = ['&', ('state', 'in', ['sale', 'done']), ('partner_pricelist_id', 'in', self.ids)]
        action['context'] = "{'default_partner_id': %d, 'default_team_id': %d}" % (self.partner_id.id, self.team_id.id)
        return action

    def action_view_quotations(self):
        self.ensure_one()
        action = self.env.ref('sale.action_quotations').read()[0]
        action['domain'] = ['&', ('state', 'in', ['draft', 'sent']), ('partner_pricelist_id', 'in', self.ids)]
        action['context'] = "{'default_partner_id': %d, 'default_team_id': %d}" % (self.partner_id.id, self.team_id.id)
        return action


    #Report
    def action_pricelist_send(self):
        self.ensure_one()
        '''
        This function opens a window to compose an email, with the edi sale template message loaded by default
        '''
        if(self.state == 'draft'):
            self.write({'state': 'sent'})

        valid_until = (datetime.now() + timedelta(days=8))
        self.write({'sent_date': fields.Datetime.now(), 'validity_date': valid_until})

       
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('partner_pricelists', 'email_template_partner_pricelist')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'partner.pricelist',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_pl_as_sent': True,
            'force_email': True
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def print_pricelist(self):
        return self.env.ref('partner_pricelists.action_report_partner_pricelist').report_action(self)


    #Workflow Buttons
    def action_to_draft(self):
        return self.write({'sent_date': False,
                    'validity_date': False,
                    'activation_date': False,
                    'state': 'draft'})

    def action_done(self):        
        wizard = self.env['partner.pricelist.lock']
        new = wizard.create({'pricelist_id': self.ids[0], 'partner_id': self.partner_id.id})
        return {'name': _('Activate Partner Pricelist'),
                'view_type': 'form',
                'res_model': 'partner.pricelist.lock',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_id': new.id,
                'target': 'new',
                'view_id': self.env.ref('partner_pricelists.partner_pricelist_lock_view_form').id,
                }

    def action_confirm(self):
        return self.write({
            'state': 'confirm',
            'confirmation_date': fields.Datetime.now()
        })

    def action_cancel(self):
        return self.write({'state': 'cancel'})

    def action_surpass(self):  #This is a hook for revision handling
        return self.write({'state': 'cancel'})

    #Autocomplete
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment terms
        - Invoice address
        - Delivery address
        """
        if not self.partner_id:
            self.update({
                'payment_term_id': False,
            })
            return

        values = {
            'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            'user_id': self.partner_id.user_id.id or self.env.uid
        }

        self.update(values)

    #Oncreate

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('partner.pricelist') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('partner.pricelist') or _('New')

        return super(PartnerPricelist, self).create(vals)


    #Price computation

    def get_product_price(self, product, qty):
        self.ensure_one()
        line = self.pricelist_lines.filtered(lambda x: ((x.lot_size <= qty) and x.product_id.id == product.id)).sorted(lambda x: -x.lot_size)
        if not line:
            line = self.pricelist_lines.filtered(lambda x: (x.product_id.id == product.id)).sorted(lambda x: x.lot_size)

        if line:
            return line[0].price_unit
        else:
            return None

class PartnerPricelistLine(models.Model):
    _name = "partner.pricelist.line"
    _description = "Partner Pricelist Line"

    _order = 'state, product_id, lot_size'

    #Father Pricelist
    pricelist_id = fields.Many2one('partner.pricelist', string='Pricelist Reference', required=True, ondelete='cascade', copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Offer Sent'),
        ('confirm', 'Pricelist Confirmed'),
        ('done', 'Active Pricelist'),
        ('cancel', 'Cancelled'),
        ], related='pricelist_id.state', string='Pricelist Status', readonly=True, states={'draft': [('readonly', False)]}, copy=False, store=True, default='draft')
    partner_id = fields.Many2one('res.partner', 'Customer', readonly=True, related='pricelist_id.partner_id', store=True)

    activation_date = fields.Datetime(string='Active Since', related="pricelist_id.activation_date", readonly=True, help="Date on which the pricelist was activated.", copy=False)
    end_date = fields.Datetime(string='Inactive Since', related="pricelist_id.end_date", readonly=True, help="Date on which the pricelist expired.", copy=False)

    #Actual line
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], required=True, readonly=True, states={'draft': [('readonly', False)]})
    lot_size   = fields.Integer(string='Lot Size', required=True, readonly=True, states={'draft': [('readonly', False)]})

    customer_ref = fields.Char(String='Customer Ref.', readonly=True, states={'draft': [('readonly', False)]})

    price_unit = fields.Monetary(string='Price per Unit', required=True)

    #Company Fields
    currency_id = fields.Many2one(related='pricelist_id.currency_id', string='Currency', store=True, readonly=True)
    company_id = fields.Many2one(related='pricelist_id.company_id', string='Company', store=True, readonly=True)

    is_unique = fields.Boolean(string="Riga univoca", compute="get_is_unique")

    @api.multi
    def get_is_unique(self):
        for i in self:
            if len(i.pricelist_id.pricelist_lines.filtered(lambda x: (x.product_id.id == i.product_id.id) and (x.lot_size == i.lot_size))) >= 2:
                i.is_unique = False
            else:
                i.is_unique = True

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.name = (self.product_id.name  + ' - ' + self.product_id.description_sale) if self.product_id.description_sale else self.product_id.name
        ref = self.pricelist_id.pricelist_lines.filtered(lambda x: x.product_id.id == self.product_id.id).mapped(lambda x: x.customer_ref)
        self.customer_ref = (ref and ref[0]) or False

    @api.model
    def copy_to_other(self, d_pricelist_id):
        vals = {}
        vals['pricelist_id'] = d_pricelist_id
        self.copy(vals)

    
# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import datetime
import odoo.osv.osv as osv
import math

class Visit(models.Model): 
    _name = 'rds.visit'
    _description = 'Cartellino Visita'
    _order = 'state asc, date_out desc, date_in desc' 
    _inherit = ['mail.thread', 'mail.activity.mixin', 'rds.mixin']

    name = fields.Char(string='Summary', required=True) 
    state = fields.Selection([
        ('draft', 'Bozza'),
        ('confirm', 'Autorizzata'),
        ('start', 'Check in fatto'),
        ('done', 'Check out fatto'),
        ('cancel', 'Annullato'),
        ('expired', 'Scaduto'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    
    ## Buttons

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})
    
    @api.multi
    def action_confirm(self):
        for i in self:
            if i.state == 'draft':
                i.write({'state': 'confirm'})

    @api.multi
    def action_start(self):
        i, f = math.modf(self.ciwo)
        _firstcheckin = datetime.strptime(self.date_in + 'T' + str(int(f)).zfill(2) + ':' + str(round(i*60)).zfill(2) + ':00', '%Y-%m-%dT%H:%M:%S')
        _earliestcheckin = datetime.strptime(datetime.today().strftime('%Y-%m-%d') + 'T' + str(int(f)).zfill(2) + ':' + str(round(i*60)).zfill(2) + ':00', '%Y-%m-%dT%H:%M:%S')
        i, f = math.modf(self.cowi)
        _latestcheckin = datetime.strptime(datetime.today().strftime('%Y-%m-%d') + 'T' + str(int(f)).zfill(2) + ':' + str(round(i*60)).zfill(2) + ':00', '%Y-%m-%dT%H:%M:%S')
        _lastcheckin = datetime.strptime(self.date_out + 'T' + str(int(f)).zfill(2) + ':' + str(round(i*60)).zfill(2) + ':00', '%Y-%m-%dT%H:%M:%S')


        if (datetime.now() > _lastcheckin):
            self.notify_managers('Visita "%s": Check in non valido' % self.name, 'In data e ora: [ ' + fields.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ] è stato richiesto un check in su un cartellino scaduto. (Check-in negato)')
            return self.write({'state': 'expired'})

        if (datetime.now() < _firstcheckin):   
            self.notify_managers('Visita "%s": Check in anticipo' % self.name, 'In data e ora: [ ' + fields.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ] è stato fatto un check in prima della entrata in validità del cartellino.')
            return self.write({'state': 'start'})

        if ((datetime.now() < _earliestcheckin) or (datetime.now() > _latestcheckin)):   
            self.notify_managers('Visita "%s": Check in fuori orario' % self.name, 'In data e ora: [ ' + fields.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ] è stato fatto un check in fuori orario.')
            return self.write({'state': 'start'})

        return self.write({'state': 'start'})
        
    
    @api.multi
    def action_done(self):
        i, f = math.modf(self.cowi)
        _lastcheckout = datetime.strptime(self.date_out + 'T' + str(int(f)).zfill(2) + ':' + str(round(i*60)).zfill(2) + ':00', '%Y-%m-%dT%H:%M:%S')
        _latestcheckout = datetime.strptime(datetime.today().strftime('%Y-%m-%d') + 'T' + str(int(f)).zfill(2) + ':' + str(round(i*60)).zfill(2) + ':00', '%Y-%m-%dT%H:%M:%S')

        if (datetime.now() > _lastcheckout):
            self.notify_managers('Visita "%s": Check out su Cartellino Scaduto' % self.name, 'In data e ora: [ ' + fields.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ] è stato fatto un check out dopo la scadenza del cartellino.')
            return self.write({'state': 'expired'})
        if (datetime.now() > _latestcheckout):
            self.notify_managers('Visita "%s": Check out fuori orario' % self.name, 'In data e ora: [ ' + fields.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ] è stato fatto un check out fuori orario.')
            return self.write({'state': 'done'})

        return self.write({'state': 'done',})

    @api.multi
    def action_askconfirm(self):
        self.notify_managers('Visita "%s": Richiesta di Autorizzazione' % self.name, 'Si richiede la autorizzazione alla presente visita.')

   
    @api.multi 
    def change_state(self, new_state): 
        for visit in self: 
            if visit.is_allowed_transition(visit.state, 
                                          new_state): 
                visit.state = new_state 
            else: 
                continue
    
    @api.constrains('date_out')
    def _check_date_validity(self): 
        if(self.date_out < self.date_in): 
            raise models.ValidationError('Errore! La data di attivazione deve essere precedente alla data di scadenza.')
        elif(self.date_out < fields.Date.today()):
            raise models.ValidationError('Errore! La data di scadenza deve essere uguale o posteriore alla data odierna.')
    
    @api.constrains('cowi')
    def _check_cico_validity(self): 
        if((self.ciwo - 1.0) > self.cowi): 
            raise models.ValidationError('L\'orario di check-out deve essere posteriore di almeno un ora all\'orario di check-in.')
    
    @api.constrains('visitor')
    def _check_visitor_validity(self): 
        if(self.visitor_contact.name and self.visitor_contact.name != self.visitor): 
            raise models.ValidationError('Errore! Se si utilizza un Contatto il nome del visitatore deve coincidere con quello riportato nel Contatto!')
    @api.constrains('visitor_company')
    def _check_visitor_company_validity(self): 
        if(self.visitor_contact.parent_id.name and self.visitor_contact.parent_id.name != self.visitor_company): 
            raise models.ValidationError('Errore! Se si utilizza un Contatto il nome della azienda deve coincidere con quello riportato nel Contatto!')

    @api.onchange('visitor_contact')
    def update_visitor_data_from_contact(self):
        self.visitor = self.visitor_contact.name
        if (self.visitor_contact.parent_id.name):
            self.visitor_company = self.visitor_contact.parent_id.name
        else:
            self.visitor_company = "Libero Professionista"

    @api.onchange('date_in')
    def update_date_out(self):
        if((not self.date_out) or (self.date_in > self.date_out)):
            self.date_out = self.date_in

    visitor_contact = fields.Many2one('res.partner', string='Contatto Visitatore', readonly=True, states={'draft': [('readonly', False)]})

    visitor = fields.Char(string='Visitatore', required=True, readonly=True, store=True, states={'draft': [('readonly', False)]})
    visitor_company = fields.Char(string='Azienda', required=True, readonly=True, store=True, states={'draft': [('readonly', False)]})
 
    conductor = fields.Many2one('hr.employee', readonly=True, states={'draft': [('readonly', False)]}, string='Accompagnatore')
    is_unaccompained = fields.Boolean(string='Può muoversi non accompagnato', default=False)

    date_in = fields.Date(string='Valido da', readonly=True, states={'draft': [('readonly', False)]}, track_visibility=True, required=True)
    date_out = fields.Date(string='Valido fino', readonly=True, states={'draft': [('readonly', False)]}, track_visibility=True)
    ciwo = fields.Float(string='Check In Dopo:', readonly=True, states={'draft': [('readonly', False)]}, track_visibility=True, default=9.00)
    cowi = fields.Float(string='Check Out Entro:', readonly=True, states={'draft': [('readonly', False)]}, track_visibility=True, default=18.00)

    notes = fields.Text('Note')

    @api.model
    def expire_visits(self):
        expired = self.env['rds.visit'].search([('date_out', '<', fields.date.today())])
        expired.write({'state': 'expired'})
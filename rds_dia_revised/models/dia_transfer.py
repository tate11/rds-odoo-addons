# -*- encoding: utf-8 -*-

import os
import logging

from datetime import datetime, date, time, timedelta

from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo import tools
from odoo.exceptions import UserError

from io import BytesIO
from docutils.parsers.rst.directives import encoding

class DiaTransferable(models.AbstractModel):
    _name = 'dia.transferable'
    _description = 'Trasferibile a DIA'

    def _get_record_type(self):
        for i in self:
            if i.record:
                i.record_type = i.record._description

    dia_transfer_status = fields.Selection(selection=[
                                                    ('none', 'Non da Trasferire'),
                                                    ('draft', 'Da Trasferire'),
                                                    ('success',  'Trasferito con Successo'),
                                                    ('failed', 'Trasferimento Fallito')
                                                ], default="none", string="Stato Dia", readonly=True, copy=False)

    dia_transfer_type = fields.Selection(selection=[('insert', 'Nuovo Record'), ('update', 'Aggiornamento Record')], default="insert", string="Tipo di Trasferimento", copy=False)
    dia_transfer_notes = fields.Char(string="Note", copy=False)
    
    dia_transfer_id = fields.Many2one('dia.transfer', 'Trasferimento', copy=False)

class DiaTransfer(models.Model):
    _name = 'dia.transfer'
    _description = 'Gruppi di Trasferimento a DIA'
    _order = 'scheduled_date DESC, id DESC'

    @api.model
    def _get_next_scheduled_date(self):
        now = datetime.now()

        if now.hour <= 12:
            return (datetime.combine(date.today(), time(12,0))).strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)
        else:
            return (datetime.combine(date.today(), time(0,0)) + timedelta(1)).strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)


    name = fields.Char('Nome', default="Nuovo Trasferimento")
    state = fields.Selection(selection=[
                                        ('draft', 'Nuovo Trasferimento'),
                                        ('partial', 'Trasferito Parzialmente'),
                                        ('failed', 'Fallito'),
                                        ('cancel', 'Annullato'),
                                        ('success',  'Trasferito')
                                        ], default="draft", string="Stato Dia", readonly=True)

    creation_date = fields.Datetime('Data di Creazione', default=fields.Datetime.now(), readonly=True)
    scheduled_date = fields.Datetime('Data Schedulata', default=_get_next_scheduled_date)

    last_transfer_date = fields.Datetime('Ultimo Trasferimento', readonly=True)
    last_transfer_result = fields.Text('Risultato', readonly=True)

    @api.model
    def get_next(self):
        return self.search([('state','=','draft')], limit=1) or self.sudo().create({})


    ###### IMPLEMENTARE IN SEGUITO I MODELLI DA TRASFERIRE

    pickings_ids = fields.One2many('stock.picking', 'dia_transfer_id', string="Bolle & DDT", readonly=True)
    products_ids = fields.One2many('product.template', 'dia_transfer_id', string="Prodotti", readonly=True)
    partners_ids = fields.One2many('res.partner', 'dia_transfer_id', string="Clienti & Fornitori", readonly=True)

    def button_run(self):
        self._action_run()

    def button_retry(self):
        self._action_run(retry=True)
    
    def button_force(self):
        self._action_run(force=True)

    @api.one
    def _action_run(self, retry=False, force=True):
        result = list()
        totransfer = ((force and ['draft', 'failed', 'success']) or (retry and ['draft', 'failed']) or ['draft'])
        
        result += self.pickings_ids.filtered(lambda x: x.dia_transfer_status in totransfer).transfer_to_dia()
        result += self.partners_ids.filtered(lambda x: x.dia_transfer_status in totransfer).transfer_to_dia()
        result += self.products_ids.filtered(lambda x: x.dia_transfer_status in totransfer).transfer_to_dia()

        if ('failed' in result) and ('success' in result):
            self.state = 'partial'
        elif ('success' in result):
            self.state = 'success'
        elif ('failed' in result):
            self.state = 'failed'
        else:
            self.state = 'cancel'

        self.last_transfer_date = fields.Datetime.now()
        self.last_transfer_result = "Stato trasferimento: {}\nRecord Trasferiti: {}\nRecord Falliti: {}\nRecord saltati: {}\n ".format(self.state,result.count('success'), result.count('failed'), result.count('none'))

    @api.model
    def cron_run(self):
        transfers = self.search([('state', '=', 'draft'), ('scheduled_date', '<=', fields.Datetime.now())], limit=1)
        for i in transfers:
            try:
                i._action_run()
            except Exception as e:
                i.last_transfer_result = "Errore! {}".format(e)
                continue


    @api.model
    def create(self, vals):
        vals['name'] = _("Trasferimento {}").format(fields.Datetime.now())

        return super(DiaTransfer, self).create(vals)
# -*- encoding: utf-8 -*-
from odoo import api, fields, models

from datetime import datetime, date, timedelta
import logging
from odoo.exceptions import ValidationError

# is_mail_thread


class ChannelToThread(models.TransientModel):
    _name = 'channel.tothread'

    @api.model 
    def _referenceable_threads(self): 
        models = self.env['ir.model'].search([('is_mail_thread', '=', True)]) 
        return [(x.model, x.name) for x in models]


    topic_id = fields.Many2one('rds.mail.topic')

    mode = fields.Selection(selection=[
        ('convert'    , 'Converti'),
        ('merge'   , 'Unisci'),
    ], required=True, default="convert", string="Tipo di Operazione", help="Sceglie se unire a un oggetto già esistente o crearne uno nuovo.")
    
    convert_to = fields.Many2one('ir.model', string="Oggetto a cui convertire")
    merge_to = fields.Reference(selection='_referenceable_threads', 
                                string='Thread su cui unire')


    def do_ch(self):
        if (self.mode == 'convert'):
            if self.convert_to == False:
                raise ValidationError("Devi scegliere l'oggetto in cui convertire il canale!")
            else:
                model, res = self.convert()
                return {
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': model,
                        'res_id': res,
                        'type': 'ir.actions.act_window',
                        'target': 'self',
                        }
        
        if (self.mode == 'merge'):
            if self.merge_to == False:
                raise ValidationError("Devi scegliere l'oggetto in cui far confluire il canale!")
            else:
                model, res = self.merge()
                return {
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': model,
                        'res_id': res,
                        'type': 'ir.actions.act_window',
                        'target': 'self',
                        }

    @api.multi
    def convert(self):
        ch = self.sudo().topic_id
        model = self.sudo().convert_to.model
        new = self.env[model].create({'name': ch.name})
        

        for msg in ch.message_ids:
            msg.model = model
            msg.res_id = new.ids[0]
            for att in msg.attachment_ids:
                att.res_model = model
                msg.res_id = new.ids[0]
        
        new.sudo().write({'message_ids': [(4, x) for x in ch.message_ids.ids], 'message_partner_ids': [(4, x) for x in ch.message_partner_ids.ids]})
        ch.sudo().unlink()
        return (model, new.ids[0])
   
    
    @api.multi
    def merge(self):
        model = self.merge_to._name
        new = self.sudo().merge_to
        ch = self.sudo().topic_id

        for msg in ch.message_ids:
            msg.model = model
            msg.res_id = new.ids[0]
            for att in msg.attachment_ids:
                att.res_model = model
                msg.res_id = new.ids[0]
        
        new.write({'message_ids': [(4, x) for x in ch.message_ids.ids], 'message_partner_ids': [(4, x) for x in ch.message_partner_ids.ids]})
        ch.sudo().unlink()
        return (model, new.ids[0])

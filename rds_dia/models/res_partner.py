'''
Created on 30 May 2018

@author: mboscolo
'''
import os
from datetime import datetime
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo import tools
from io import BytesIO
from .common import FTCL
import logging

from_path = '/mnt/dia/odoo'
if not os.path.exists(from_path):
    logging.error("Path mnt/dia not defined")
    from_path = '/tmp/'

FILE_CLIENTI = os.path.join(from_path, 'clienti.txt')
UPDATE_FILE_CLIENTI = os.path.join(from_path, 'u_clienti.txt')

FILE_FORNITORI = os.path.join(from_path, 'fornitori.txt')
UPDATE_FILE_FORNITORI = os.path.join(from_path, 'u_fornitori.txt')


class stock_picking_custom(models.Model):
    _inherit = 'res.partner'
    send_to_dia = fields.Selection([('new', 'New'),
                                    ('modifie', 'Modifie'),
                                    ('updated', 'Updated')],
                                   default='new')
    dia_ref_customer = fields.Char('Riderimento Dia Cliente')
    dia_ref_vendor = fields.Char('Riderimento Dia Fornitore')

    @api.multi
    def chron_transfer_to_dia(self):
        logging.info("Start scheduled task Dia for partner")
        try:
            self.transfer_to_dia_template(customer=True)   # Customer
            self.transfer_to_dia_template(customer=False)  # Vendor
        except Exception as ex:
            logging.error("Error on scheduled task %r" % ex)
            return False
        return True

    @api.multi
    def transfer_to_dia(self):
        isNew = False
        if self.send_to_dia == 'new':
            isNew = True
        if self.customer:
            self.transfer_to_dia_template(customer=True,
                                          force_partner=self)   # Customer
            if isNew:
                self.send_to_dia = 'new'
        if self.supplier:
            self.transfer_to_dia_template(customer=False,
                                          force_partner=self)  # Vendor

    @api.model
    def transfer_to_dia_template(self, customer=True, force_partner=None):
        file_new = FILE_FORNITORI
        file_upd = UPDATE_FILE_FORNITORI
        if customer:
            file_new = FILE_CLIENTI
            file_upd = UPDATE_FILE_CLIENTI
        if force_partner:
            partners = force_partner
        else:
            partners = self.env['res.partner'].search([('send_to_dia', 'in', ['new', 'modifie']),
                                                       ('customer', '=', customer)])
        new_p, upd_p = self.transfer_customer_to_dia(partners, customer)
        if new_p:
            if os.path.exists(file_new):
                self.message_post(body=_('<div style="background-color:red;color:white;border-radius:5px"><b>Trasferimento DIA fallito: File %s gia presente nel direttorio condiviso</b></div>' % file_new),
                                  message_type='notification')
                return
            with open(file_new, 'wb') as f:
                for lineTXT in new_p:
                    f.write(bytearray(lineTXT, encoding='utf-8'))
        if upd_p:
            if os.path.exists(file_upd):
                self.message_post(body=_('<div style="background-color:red;color:white;border-radius:5px"><b>Trasferimento DIA fallito: File %s gia presente nel direttorio condiviso</b></div>' % file_upd),
                                  message_type='notification')
                return
            with open(file_upd, 'wb') as f:
                for lineTXT in upd_p:
                    f.write(bytearray(lineTXT, encoding='utf-8'))

    @api.onchange('supplier')
    def _change_supplier(self):
        for partner in self:
            if partner.supplier:
                if not partner.dia_ref_vendor:
                    newCode = self.env['ir.sequence'].next_by_code("RDS_PARNER_SEQUENCE")
                    partner.dia_ref_vendor = "261%s" % newCode

    @api.onchange('customer')
    def _change_customer(self):
        for partner in self:
            if not partner.dia_ref_customer:
                newCode = self.env['ir.sequence'].next_by_code("RDS_PARNER_SEQUENCE")
                if partner.country_id.code == "IT":
                    partner.dia_ref_customer = "091%s" % newCode
                else:
                    partner.dia_ref_customer = "081%s" % newCode

    @api.one
    def write(self, vals):
        if vals.get('customer'):
            self._change_customer()
        if vals.get('supplier'):
            self._change_supplier()
        if self.send_to_dia == 'updated' and 'send_to_dia' not in vals:
            vals['send_to_dia'] = vals.get('send_to_dia', 'modifie')
        res = super(stock_picking_custom, self).write(vals)
        return res

    @api.model
    def transfer_customer_to_dia(self, partners, customer=True):
        new_partner = []
        update_partner = []
        for partner in partners:
            is_italian = partner.country_id.code == "IT"
            lineTXT = ""
            if customer:
                ref = partner.dia_ref_customer
                if ref and ref[0:3] not in ['081', '008', '090', '091']:
                    partner.message_post(body=_('<div style="background-color:red;color:white;border-radius:5px"><b>Trasferimento DIA Non Consentito codice fornitore errato deve essere 081, 091</b></div>'),
                                         message_type='notification')
                    continue
            else:
                ref = partner.dia_ref_vendor
                if ref and ref[0:3] not in ['261', '260']:
                    partner.message_post(body=_('<div style="background-color:red;color:white;border-radius:5px"><b>Trasferimento DIA Non Consentito codice fornitore errato deve essere 261</b></div>'),
                                         message_type='notification')
                    continue
            if not ref:
                partner.message_post(body=_('<div style="background-color:red;color:white;border-radius:5px"><b>Trasferimento DIA Non Consentito codice fornitore o client emancande</b></div>'),
                                     message_type='notification')
                continue
            lineTXT += FTCL(ref, 8)  # Codice    1    8    S
            lineTXT += FTCL(str(partner.name)[:30], 30)  # Ragione Sociale    10    30    S
            lineTXT += FTCL(str(partner.name)[30:], 30)  # Ragione Sociale 2    41    30    N
            lineTXT += FTCL(str(partner.street), 60)     # Indirizzo    72    60    N
            lineTXT += FTCL(str(partner.zip), 6)     # Cap    143    6    N
            lineTXT += FTCL(str(partner.city), 60)   # Comune    150    60    N
            lineTXT += FTCL(str(partner.state_id.code), 2)  # Provincia    211    2    N
            if is_italian:  # Nazione    214    2    N    (lasciare vuoto in caso di Italia)
                lineTXT += "  "
            else:
                lineTXT += FTCL(str(partner.country_id.code), 2)
            if partner.company_type == 'person':  # Persona fisica    217    1    S    (P se privato, N se persona giuridica, S se persona fisica)
                lineTXT += "P"
            else:
                lineTXT += "N"
            if is_italian:  # Estero    219    1    S    (I se italiano, E se Estero)
                lineTXT += "I"
            else:
                lineTXT += "E"
            lineTXT += " "   # CEE    221    1    N    (vuoto se italiano, S se Estero CEE, N se Estero extra CEE)
            lineTXT += " "   # Elenchi iva    223    1    N    S / N
            lineTXT += FTCL(str(partner.fiscalcode), 16)  # Codice fiscale    225    16    N
            lineTXT += FTCL(str(partner.vat), 12)  # Partita iva    242    12    N
            lineTXT += FTCL("", 4)   # Codice es.iva.    255    4    N
            lineTXT += FTCL("", 40)  # Dich.es.iva    260    40    N
            lineTXT += FTCL("", 8)  # Scad.es.iva    301    8    N
            lineTXT += FTCL(str(partner.phone), 20)  # Telefono    310    20    N
            delivery_found = False
            for child in partner.child_ids:
                if child.type == 'delivery':
                    lineTXT += FTCL(str(partner.name)[:30], 30)      # Rag.soc.destinaz.    331    30    N
                    lineTXT += FTCL(str(partner.name)[30:], 30)      # Rag.soc.2 destinaz.    362    30    N
                    lineTXT += FTCL(str(child.street), 60)      # Indirizzo destinaz.    393    60    N
                    lineTXT += FTCL(child.zip, 5)        # Cap destinaz.    454    5    N
                    lineTXT += FTCL(child.city, 60)      # Comune destinaz.    485    60    N
                    lineTXT += FTCL(str(child.state_id.code), 2)           # Provincia destinaz.    545    2    N
                    lineTXT += FTCL(str(child.state_id.code), 2)            # Nazione destinaz.    548    2    N
                    delivery_found = True
            if not delivery_found:
                lineTXT += FTCL("", 30)      # Rag.soc.destinaz.    331    30    N
                lineTXT += FTCL("", 30)      # Rag.soc.2 destinaz.    362    30    N
                lineTXT += FTCL("", 60)      # Indirizzo destinaz.    393    60    N
                lineTXT += FTCL("", 5)   # Cap destinaz.    454    5    N
                lineTXT += FTCL("", 60)  # Comune destinaz.    485    60    N
                lineTXT += FTCL("", 2)   # Provincia destinaz.    545    2    N
                lineTXT += FTCL("", 2)   # Nazione destinaz.    548    2    N
            #  property_purchase_currency_id
            #  currency_id
            if partner.currency_id.name == "EUR":  # Valuta estera    551    4    N    (lasciare vuoto in caso di Euro)
                lineTXT += FTCL("", 4)
            else:
                lineTXT += FTCL(str(partner.currency_id.name), 4)
            lineTXT += FTCL(str(partner.property_payment_term_id.name), 6)  # Pagamento    556    6    N
            lineTXT += FTCL(str(""), 6)  # Banca appoggio    563    6    N
            lineTXT += FTCL(str(""), 6)  # Cab (banca appoggio)    570    6    N
            lineTXT += FTCL(str(""), 6)  # Banca bonifici    577    6    N
            lineTXT += FTCL(str(""), 6)  # Cab (banca bonifici)    584    6    N
            lineTXT += FTCL(str(""), 20)  # Conto corrente    591    20    N
            lineTXT += FTCL(str(""), 30)  # Iban    612    30    N
            if customer:
                lineTXT += FTCL(str(""), 6)  # Listino    643    6    N
                lineTXT += FTCL(str(""), 10)  # Sconti 1    651    10    N
                lineTXT += FTCL(str(""), 10)  # Sconti 2    662    10    N
            lineTXT += FTCL(str(""), 4)  # Spedizione    673    4    N
            lineTXT += FTCL(str(""), 18)  # Resa    678    18    N
            if customer:
                lineTXT += FTCL(str(""), 1)  # Raggr.bolle    697    1    N
                lineTXT += FTCL(str(""), 1)  # Raggr.ordini    699    1    N
                lineTXT += FTCL(str(""), 8)  # Conto fatturazione    701    8    N
                lineTXT += FTCL(str(""), 8)  # Conto sped.fatt.    710    8    N
            lineTXT += FTCL(str(""), 1)  # Blocco ordini    719    1    N
            lineTXT += FTCL(str(""), 1)  # Blocco consegne    721    1    N
            lineTXT += "\n"
            if partner.send_to_dia == 'new':
                new_partner.append(lineTXT)
            else:
                update_partner .append(lineTXT)
            partner.send_to_dia = 'updated'
            partner.message_post(body=_('<div style="background-color:green;color:white;border-radius:5px"><b>Trasferimento DIA con successo</b></div>'),
                                 message_type='notification')
        return new_partner, update_partner

    @api.model
    def fix_fiscal_position_dia(self, arg_list):
        codice_dia, id_fiscal_position = arg_list
        for obj in self.search([('dia_ref_customer', '=', codice_dia)]):
            sdt = obj.send_to_dia
            obj.property_account_position_id = int(id_fiscal_position)
            obj.send_to_dia = sdt
            return True
        return False

#     @api.model
#     def fix_tax_from_dia(self):
#         for partner in self.search(['property_account_position_id', '!=', False):
#             partner.


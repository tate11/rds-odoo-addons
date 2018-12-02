# Part of <Odoo Addons for RDS Moulding Technology S.p.A.>. See Attached README.md file.
# Copyright 2018 RDS Moulding Technology S.p.A.

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

from .common import FILE_CLIENTI, UPDATE_FILE_CLIENTI, FILE_FORNITORI, UPDATE_FILE_FORNITORI

class PartnerDIA(models.Model):
    _inherit = ['res.partner', 'dia.transferable']
    _name = 'res.partner'

    dia_ref_customer = fields.Char('Riferimento Dia Cliente')
    dia_ref_vendor = fields.Char('Riferimento Dia Fornitore')

    @api.multi
    def transfer_to_dia(self):
        c_ins, c_upd, s_ins, s_upd = self.get_transfer_data()

        if c_ins:
            if os.path.exists(FILE_CLIENTI):
                self.filtered(lambda x: x.customer and (x.dia_transfer_type == 'insert')).write({'dia_transfer_notes': _('Trasferimento fallito: Il file clienti.txt non è ancora stato processato da DIA!'), 'dia_transfer_status': 'failed'})
            else:
                with open(FILE_CLIENTI, 'wb') as f:
                    for lineTXT in c_ins:
                        f.write(bytearray(lineTXT, encoding='utf-8'))
        if c_upd:
            if os.path.exists(UPDATE_FILE_CLIENTI):
                self.filtered(lambda x: x.customer and (x.dia_transfer_type == 'update')).write({'dia_transfer_notes': _('Trasferimento fallito: Il file u_clienti.txt non è ancora stato processato da DIA!'), 'dia_transfer_status': 'failed'})
            else:
                with open(UPDATE_FILE_CLIENTI, 'wb') as f:
                    for lineTXT in c_upd:
                        f.write(bytearray(lineTXT, encoding='utf-8'))

        #Fornitori

        if s_ins:
            if os.path.exists(FILE_FORNITORI):
                self.filtered(lambda x: x.supplier and (x.dia_transfer_type == 'insert')).write({'dia_transfer_notes': _('Trasferimento fallito: Il file fornitori.txt non è ancora stato processato da DIA!'), 'dia_transfer_status': 'failed'})
            else:
                with open(FILE_FORNITORI, 'wb') as f:
                    for lineTXT in s_ins:
                        f.write(bytearray(lineTXT, encoding='utf-8'))
        if s_upd:
            if os.path.exists(UPDATE_FILE_FORNITORI):
                self.filtered(lambda x: x.supplier and (x.dia_transfer_type == 'update')).write({'dia_transfer_notes': _('Trasferimento fallito: Il file u_fornitori.txt non è ancora stato processato da DIA!'), 'dia_transfer_status': 'failed'})
            else:
                with open(UPDATE_FILE_FORNITORI, 'wb') as f:
                    for lineTXT in s_upd:
                        f.write(bytearray(lineTXT, encoding='utf-8'))
        
        return self.mapped(lambda x: x.dia_transfer_status)


    @api.onchange('supplier')
    def _change_supplier(self):
        for partner in self:
            if partner.supplier:
                if not partner.dia_ref_vendor:
                    partner.dia_ref_vendor = self.env['ir.sequence'].next_by_code("dia.supplier")

    @api.onchange('customer')
    def _change_customer(self):
        for partner in self:
            if not partner.dia_ref_customer:
                if partner.country_id.code != "IT":
                    partner.dia_ref_customer = self.env['ir.sequence'].next_by_code("dia.customer.ext")
                else:
                    partner.dia_ref_customer = self.env['ir.sequence'].next_by_code("dia.customer")

    @api.one
    def write(self, vals):
        if vals.get('customer'):
            self._change_customer()
        if vals.get('supplier'):
            self._change_supplier()
        if (not vals.get('dia_transfer_status')) and (self.dia_transfer_status == 'success'):
            vals['dia_transfer_status'] = vals.get('dia_transfer_status', 'draft')
            vals['dia_transfer_type'] = vals.get('dia_transfer_type', 'update')
            vals['dia_transfer_id'] = self.sudo().env['dia.transfer'].get_next().id
        return super(PartnerDIA, self).write(vals)

    @api.multi
    def get_transfer_data(self):
        i_customers = []
        u_customers = []
        i_suppliers = []
        u_suppliers = []

        for partner in self:
            is_italian = partner.country_id.code == "IT"
            line_common = ""

            ref_c = partner.dia_ref_customer
            ref_s = partner.dia_ref_vendor

            if partner.customer:
                if (ref_c and ref_c[0:3] not in ['081', '008', '090', '091']) or (not ref_c):
                    partner.write({'dia_transfer_status': 'failed', 'dia_transfer_notes': _("Codice Cliente DIA non valido o non impostato!")})
                    continue

            elif partner.supplier:
                if (ref_s and ref_s[0:3] not in ['261', '260']) or (not ref_s):
                    partner.write({'dia_transfer_status': 'failed', 'dia_transfer_notes': _("Codice Fornitore DIA non valido o non impostato!")})
                    continue

            line_common += FTCL(str(partner.name)[:30], 30)  # Ragione Sociale    10    30    S
            line_common += FTCL(str(partner.name)[30:], 30)  # Ragione Sociale 2    41    30    N
            line_common += FTCL(str(partner.street), 60)     # Indirizzo    72    60    N
            line_common += FTCL(str(partner.zip), 6)     # Cap    143    6    N
            line_common += FTCL(str(partner.city), 60)   # Comune    150    60    N
            line_common += FTCL(str(partner.state_id.code), 2)  # Provincia    211    2    N
            if is_italian:  # Nazione    214    2    N    (lasciare vuoto in caso di Italia)
                line_common += "  "
            else:
                line_common += FTCL(str(partner.country_id.code), 2)
            if partner.company_type == 'person':  # Persona fisica    217    1    S    (P se privato, N se persona giuridica, S se persona fisica)
                line_common += "P"
            else:
                line_common += "N"
            if is_italian:  # Estero    219    1    S    (I se italiano, E se Estero)
                line_common += "I"
            else:
                line_common += "E"
            line_common += " "   # CEE    221    1    N    (vuoto se italiano, S se Estero CEE, N se Estero extra CEE)
            line_common += " "   # Elenchi iva    223    1    N    S / N
            line_common += FTCL(str(getattr(partner, 'fiscalcode', "")), 16)  # Codice fiscale    225    16    N
            line_common += FTCL(str(partner.vat), 12)  # Partita iva    242    12    N
            line_common += FTCL("", 4)   # Codice es.iva.    255    4    N
            line_common += FTCL("", 40)  # Dich.es.iva    260    40    N
            line_common += FTCL("", 8)  # Scad.es.iva    301    8    N
            line_common += FTCL(str(partner.phone), 20)  # Telefono    310    20    N
            delivery_found = False
            for child in partner.child_ids:
                if child.type == 'delivery':
                    line_common += FTCL(str(partner.name)[:30], 30)      # Rag.soc.destinaz.    331    30    N
                    line_common += FTCL(str(partner.name)[30:], 30)      # Rag.soc.2 destinaz.    362    30    N
                    line_common += FTCL(str(child.street), 60)      # Indirizzo destinaz.    393    60    N
                    line_common += FTCL(child.zip, 5)        # Cap destinaz.    454    5    N
                    line_common += FTCL(child.city, 60)      # Comune destinaz.    485    60    N
                    line_common += FTCL(str(child.state_id.code), 2)           # Provincia destinaz.    545    2    N
                    line_common += FTCL(str(child.state_id.code), 2)            # Nazione destinaz.    548    2    N
                    delivery_found = True
            if not delivery_found:
                line_common += FTCL("", 30)      # Rag.soc.destinaz.    331    30    N
                line_common += FTCL("", 30)      # Rag.soc.2 destinaz.    362    30    N
                line_common += FTCL("", 60)      # Indirizzo destinaz.    393    60    N
                line_common += FTCL("", 5)   # Cap destinaz.    454    5    N
                line_common += FTCL("", 60)  # Comune destinaz.    485    60    N
                line_common += FTCL("", 2)   # Provincia destinaz.    545    2    N
                line_common += FTCL("", 2)   # Nazione destinaz.    548    2    N
            #  property_purchase_currency_id
            #  currency_id
            if partner.currency_id.name == "EUR":  # Valuta estera    551    4    N    (lasciare vuoto in caso di Euro)
                line_common += FTCL("", 4)
            else:
                line_common += FTCL(str(partner.currency_id.name), 4)
            line_common += FTCL(str(partner.property_payment_term_id.dia_code), 6)  # Pagamento    556    6    N
            line_common += FTCL(str(""), 6)  # Banca appoggio    563    6    N
            line_common += FTCL(str(""), 6)  # Cab (banca appoggio)    570    6    N
            line_common += FTCL(str(""), 6)  # Banca bonifici    577    6    N
            line_common += FTCL(str(""), 6)  # Cab (banca bonifici)    584    6    N
            line_common += FTCL(str(""), 20)  # Conto corrente    591    20    N
            line_common += FTCL(str(""), 30)  # Iban    612    30    N

            customer_line = FTCL(ref_c, 8) + line_common
            supplier_line = FTCL(ref_s, 8) + line_common

            customer_line += FTCL(str(""), 6)  # Listino    643    6    N
            customer_line += FTCL(str(""), 10)  # Sconti 1    651    10    N
            customer_line += FTCL(str(""), 10)  # Sconti 2    662    10    N

            customer_line += FTCL(str(""), 4)  # Spedizione    673    4    N
            customer_line += FTCL(str(""), 18)  # Resa    678    18    N
            supplier_line += FTCL(str(""), 4)  # Spedizione    673    4    N
            supplier_line += FTCL(str(""), 18)  # Resa    678    18    N

            customer_line += FTCL(str(""), 1)  # Raggr.bolle    697    1    N
            customer_line += FTCL(str(""), 1)  # Raggr.ordini    699    1    N
            customer_line += FTCL(str(""), 8)  # Conto fatturazione    701    8    N
            customer_line += FTCL(str(""), 8)  # Conto sped.fatt.    710    8    N

            customer_line += FTCL(str(""), 1)  # Blocco ordini    719    1    N
            customer_line += FTCL(str(""), 1)  # Blocco consegne    721    1    N
            customer_line += "\n"

            supplier_line += FTCL(str(""), 1)  # Blocco ordini    719    1    N
            supplier_line += FTCL(str(""), 1)  # Blocco consegne    721    1    N
            supplier_line += "\n"
            
            if partner.dia_transfer_type == 'insert':
                if partner.customer:
                    i_customers.append(customer_line)
                if partner.supplier:
                    i_suppliers.append(customer_line)

            if partner.dia_transfer_type == 'update':
                if partner.customer:
                    u_customers.append(customer_line)
                if partner.supplier:
                    u_suppliers.append(customer_line)

            partner.write({'dia_transfer_status': 'success', 'dia_transfer_notes': False})

        return i_customers, u_customers, i_suppliers, u_suppliers
# -*- encoding: utf-8 -*-
'''
Created on 28 May 2018

@author: mboscolo
'''
import os
import logging
from datetime import datetime
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo import tools
from io import BytesIO
from odoo.exceptions import UserError

from docutils.parsers.rst.directives import encoding

from .common import safeFTCL
from .common import FTCL
from .common import WRITE_PICK_OUT_PATH, WRITE_PICK_IN_PATH

class StockPickingReason(models.Model):
    _inherit = 'stock.picking.type'

    export_to_dia = fields.Boolean('Esportare a Dia')
    dia_deposit = fields.Char("Deposito DIA", size=2)
    dia_code = fields.Char("Codice DIA", size=4)

class DiaStockDDT(models.Model):
    _inherit = ['stock.ddt', 'dia.transferable']

    @api.multi
    def transfer_to_dia(self):
        outgoing = self.filtered(lambda x: x.ddt_type == 'outgoing')
        if outgoing:
            if os.path.exists(WRITE_PICK_OUT_PATH):
                self.filtered(lambda x: x.ddt_type == 'outgoing').write({'dia_transfer_notes': _('Trasferimento fallito: Il file ddt_vendite.txt non è ancora stato processato da DIA!'), 'dia_transfer_status': 'failed'})
            else:
                with open(WRITE_PICK_OUT_PATH, 'wb') as f:
                    for line in outgoing.get_transfer_to_dia_out():
                        f.write(bytearray(line, encoding='utf-8'))

        
        incoming = self.filtered(lambda x: x.ddt_type == 'incoming')
        if incoming:
            if os.path.exists(WRITE_PICK_IN_PATH):
                self.filtered(lambda x: x.ddt_type == 'incoming').write({'dia_transfer_notes': _('Trasferimento fallito: Il file ddt_acquisti.txt non è ancora stato processato da DIA!'), 'dia_transfer_status': 'failed'})
            else:
                with open(WRITE_PICK_IN_PATH, 'wb') as f:
                    for line in incoming.get_transfer_to_dia_in():
                        f.write(bytearray(line, encoding='utf-8'))

        return self.mapped(lambda x: x.dia_transfer_status)

    @api.multi
    def get_transfer_to_dia_in(self):
        out = []
        for pick in self:
            vendor = pick.partner_id.dia_ref_vendor
            if not vendor:
                pick.write({'dia_transfer_status': 'failed', 'dia_transfer_notes': _("Fornitore non presente su DIA!")})
                continue
            else:
                if vendor[0:3] not in ['261', '260']:
                    pick.write({'dia_transfer_status': 'failed', 'dia_transfer_notes': _("Codice fornitore malformato!")})
                    continue
            
            header = "B0000001"                 # Numero documento    1    8    S    Impostare sempre valore B0000001
            header += FTCL(vendor, 8)           # Codice fornitore    9    8    S
            for line in pick.move_line_ids_without_package:
                lineTXT = header
                lineTXT += FTCL(line.product_id.dia_code or line.product_id.default_code, 16)       # Articolo    17    16    S
                lineTXT += FTCL(line.product_qty, 12)                   # Quantita    33    12    S    usare punto come separatore decimali
                lineTXT += FTCL(datetime.now().strftime("%Y%m%d"), 8)   # Data registrazione    45    8    S    formato yyyymmdd (possiamo preimpostarlo lato nostro con la data odierna)

                reason_code =  pick.picking_type_id.dia_code or 'CARA'

                lineTXT += FTCL(reason_code, 4)                    # Causale    53    4    S    Impostare sempre CARA (verificare con il cliente se va bene usare sempre questa)
                lineTXT += FTCL(pick.picking_type_id.dia_deposit, 2) # Deposito Destinazione 2
                lineTXT += safeFTCL(line.purchase_line_id.price_unit, 12)  # prezzo 12
                lineTXT += "\n"
                out.append(lineTXT)

            pick.write({'dia_transfer_status': 'success', 'dia_transfer_notes': False})

        return out

    @api.multi
    def get_transfer_to_dia_out(self):
        out = []
        for pick in self:
            to_write = []
            if not pick.partner_id.dia_ref_customer:
                pick.write({'dia_transfer_status': 'failed', 'dia_transfer_notes': _("Partner non presente su DIA!")})
                continue

            if not pick.picking_type_id.export_to_dia:
                pick.write({'dia_transfer_status': 'none', 'dia_transfer_notes': _("La Causale DDT è impostata per non essere trasferita a DIA!")})
                continue

            if not pick.name:
                pick.write({'dia_transfer_status': 'failed', 'dia_transfer_notes': _("Numero DDT Mancante!")})
                continue

            stop_transfer = False

            header = ""
            header += FTCL(pick.date.year, 4)       # Anno Bolla    1    4        in rosso i dati di testata (da ripetere su tutte le righe)
            header += FTCL(pick.name, 8)      # Num Bolla    6    8        in verde i dati di riga
            header += FTCL(pick.date.strftime("%Y%m%d"), 8)        # Data Bolla    15    8
            header += FTCL(pick.partner_id.dia_ref_customer, 8)  # Cod.Cliente    24    8
            header += FTCL(pick.picking_type_id.dia_code, 4)   # Causale    33    4
            header += FTCL(pick.get_first_sale().payment_term_id.dia_code, 6)    # Pagamento    38    6        campo di testo
            header += FTCL("", 6)  # TODO: da definire Banca    45    6        mettere un campo nelle banche di odoo che dica quale e’ il nome della banca in dia
            header += "01"                          # Deposito Pr.    52    2        passo sempre 01

            notes = str(pick.notes).replace("\n", "")
            header += FTCL(notes[:60], 60)  # Note1    55    60        note_ddt
            header += FTCL(notes[60:], 60)  # Note2    116    60        note_ddt >60
            i = 0
            for line in pick.move_lines:
                i += 1
                lineTXT = header
                lineTXT += FTCL(i, 4)                               # Riga    177    4        progressivo di righa
                lineTXT += FTCL(line.product_id.dia_code or line.product_id.default_code, 16)   # Articolo    181    16
                if line.quantity_done == 0:
                    continue

                lineTXT += FTCL(line.quantity_done, 12)               # Quantita    198    12
                price = line.sale_line_id.price_unit or 0

                if (type(price) not in [int, float]) or price < 0:
                    pick.write({'dia_transfer_status': 'failed', 'dia_transfer_notes': _("Alcune righe non hanno un prezzo impostato!")})
                    stop_transfer = True

                lineTXT += FTCL(line.sale_line_id.price_unit, 12)             # line.sale_line_id.price_total ?? Prezzo    211    1
                
                ord_our_ref, ord_cust_ref = line.sale_line_id.order_id.name, line.sale_line_id.order_id.client_order_ref
                lineTXT += FTCL((ord_our_ref or '') + (ord_cust_ref and ("Rif.Ordc.: " + ord_cust_ref) or ''), 60)      # note1    224    60        numero ordine vendita cliente da sale order    nove_line.sale_line_id.sale_id.name
                lineTXT += FTCL(line.sale_line_id.order_id.origin, 60)    # note2    285    60        riferimento cliente da sale order    nove_line.sale_line_id.sale_id.origin
                lineTXT += FTCL(line.sale_line_id.order_id.analytic_account_id.name, 12)  # Commessa    346    12        nove_line.sale_id.account_analytic.name
                
                lineTXT += FTCL(pick.reason_id.dia_deposit, 2) # Deposito Destinazione 2
                    
                lineTXT += FTCL(getattr(line, 'data_decorrenza', ""), 8)             # Data decorrenza    345    8    N
                
                delivery_address = pick.delivery_address or pick.partner_id

                lineTXT += FTCL(delivery_address.display_name, 30)    # Ragione sociale destinazione    353    30    N
                lineTXT += FTCL("", 30)           # Ragione sociale 2 destinazione    383    30    N

                lineTXT += FTCL(delivery_address.street, 60)           # Indirizzo destinazione    413    60    N
                lineTXT += FTCL(delivery_address.zip, 6)           # CAP destinazione    473    6    N
                lineTXT += FTCL(delivery_address.city, 60)           # Localita' destinazione    479    60    N
                lineTXT += FTCL(delivery_address.state_id.code, 2)           # Provincia destinazione    539    2    N
                if delivery_address.country_id.code == 'IT':
                    lineTXT += FTCL('  ', 2)           # Nazione destinazione    541    2    N
                else:
                    lineTXT += FTCL(delivery_address.country_id.code, 2)           # Nazione destinazione    541    2    N
                lineTXT += FTCL(pick.partner_id.property_account_position_id.dia_code, 4)           # Codice esenzione iva    543    4    N


                lineTXT += "\n"
                to_write.append(lineTXT)

            if not stop_transfer:
                out += to_write
                pick.write({'dia_transfer_status': 'success', 'dia_transfer_notes': False})

        return out

    def action_done(self):
        res = super(DiaStockPicking, self).action_done()

        if self.reason_id.export_to_dia:
           self.dia_transfer_id = self.sudo().env['dia.transfer'].get_next()
           self.dia_transfer_status = 'draft'

        return res
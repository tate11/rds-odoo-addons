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
try:
    import cx_Oracle
except Exception as ex:
    logging.warning("Unable to import cx_oracle module some functionality may not work %s" % ex)

from_path = '/mnt/dia/odoo'
if not os.path.exists(from_path):
    logging.error("Path mnt/dia not defined")
    from_path = '/tmp/'
WRITE_PICK_OUT_PATH = os.path.join(from_path, 'ddt_vendite.txt')
WRITE_PICK_IN_PATH = os.path.join(from_path, 'ddt_acquisti.txt')
ORACLE_CONNECTION_STRING = ""


class DiaCausale(models.Model):
    _name = 'dia.causale'

    name = fields.Char('Causale')               # CAUSALE
    description = fields.Char('Descrizione')    # DES_CAU
    accounting_doc_type = fields.Char('Tipo Documento Contabile')    # TIPO_DOC_CONTABILE
    code = fields.Char('Codice')                # CODICE
    serie = fields.Char('Serie')                # SERIE
    serie_description = fields.Char('Descrizione Serie')    # DES_SERIE
    last_num = fields.Char('Ultimo Numero')                 # LAST_NUM
    last_day = fields.Char('Data Ultima Scrittura')         # LAST_DAY
    push_to_dia = fields.Boolean('Esportare per dia', default=False)
    causale_type = fields.Selection(selection=[
        ('nessuno', 'Nessuno'),
        ('scarico_carico', 'Scarico + Carico'),
        ('scarico', 'Scarico'),
        ], string=_('Tipo Causale'), default='nessuno')


class stock_picking_custom(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    @api.depends('causale_dia')
    def _compute_lastnumber_dia(self):
        diaLastNumberObj = self.env['dia.lastnumber']
        for pickBrws in self:
            pickBrws.dia_next_number = ''
            pickBrws.dia_last_number_odoo = ''
            pickBrws.dia_next_computed_number = ''
            key, nextCode = pickBrws.getDiaNumber(pickBrws.causale_dia.code)
            if nextCode:
                nextCode = nextCode[0]
            pickBrws.dia_next_number = "%s    %s" % (key, nextCode)
            if key and nextCode:
                for dia_lastNumber in diaLastNumberObj.search([('key', '=', key)]):
                    pickBrws.dia_last_number_odoo = dia_lastNumber.last_number
                pickBrws.dia_next_computed_number = diaLastNumberObj.getNextNumber(key=key, nextNumber=nextCode, create=False)
    causale_dia = fields.Many2one('dia.causale', string="Causale DIA")
    send_to_dia = fields.Selection([('new', 'New'),
                                    ('updated', 'Updated'),
                                    ('error', 'Error')])
    dia_next_number = fields.Char('Ultimo Numero DIA', compute=_compute_lastnumber_dia)
    dia_last_number_odoo = fields.Char('Ultimo Numero DIA Odoo', compute=_compute_lastnumber_dia)
    dia_next_computed_number = fields.Char('Prossimo Numero DIA', compute=_compute_lastnumber_dia)

    @api.multi
    def write(self, vals):
        res = super(stock_picking_custom, self).write(vals)
        if not self.env.context.get('skip_dia_check', False):
            for pickBrws in self:
                if pickBrws.send_to_dia in ['', False]:
                    pickBrws.with_context({'skip_dia_check': True}).send_to_dia = 'new' if pickBrws.causale_dia.push_to_dia else False
        return res

    @api.multi
    def chron_transfer_to_dia(self):
        logging.info("Start chron job for ddt to Dia")
        if os.path.exists(WRITE_PICK_OUT_PATH):
            self.message_post(body=_('<div style="background-color:red;color:white;border-radius:5px"><b>Trasferimento DIA fallito: File %s gia presente nel direttorio condiviso</b></div>' % WRITE_PICK_OUT_PATH),
                              message_type='notification')
            self.send_to_dia = 'error'
            return False
        if os.path.exists(WRITE_PICK_IN_PATH):
            self.message_post(body=_('<div style="background-color:red;color:white;border-radius:5px"><b>Trasferimento DIA fallito: File %s gia presente nel direttorio condiviso</b></div>' % WRITE_PICK_IN_PATH),
                              message_type='notification')
            self.send_to_dia = 'error'
            return False
        dia_causale = self.env['dia.causale'].search([('name', 'in', ['XXXX', 'CARA', 'CARL'])])
        picks = self.env['stock.picking'].search([('send_to_dia', '=', 'new'),
                                                  ('causale_dia', 'not in', dia_causale.ids)])
        if picks:
            with open(WRITE_PICK_OUT_PATH, 'wb') as f:
                for line in self.get_transfer_to_dia_out(picks):
                    f.write(bytearray(line, encoding='utf-8'))
        picks = self.env['stock.picking'].search([('send_to_dia', '=', 'new'),
                                                  ('causale_dia', 'in', dia_causale.ids)])
        if picks:
            with open(WRITE_PICK_IN_PATH, 'wb') as f:
                for line in self.get_transfer_to_dia_in(picks):
                    f.write(bytearray(line, encoding='utf-8'))
        return True

    @api.one
    def transfer_to_dia(self):
        if self:
            if self.causale_dia.name not in ['XXXX', 'CARA', 'CARL']:
                if os.path.exists(WRITE_PICK_OUT_PATH):
                    self.message_post(body=_('<div style="background-color:red;color:white;border-radius:5px"><b>Trasferimento DIA fallito: File %s gia presente nel direttorio condiviso</b></div>' % WRITE_PICK_OUT_PATH),
                                      message_type='notification')
                    self.send_to_dia = 'error'
                    return
                with open(WRITE_PICK_OUT_PATH, 'wb') as f:
                    for line in self.get_transfer_to_dia_out(self, force_price=True):
                        f.write(bytearray(line, encoding='utf-8'))
            if self.causale_dia.name in ['XXXX', 'CARA', 'CARL']:
                if os.path.exists(WRITE_PICK_IN_PATH):
                    self.message_post(body=_('<div style="background-color:red;color:white;border-radius:5px"><b>Trasferimento DIA fallito: File %s gia presente nel direttorio condiviso</b></div>' % WRITE_PICK_IN_PATH),
                                      message_type='notification')
                    self.send_to_dia = 'error'
                    return
                with open(WRITE_PICK_IN_PATH, 'wb') as f:
                    for line in self.get_transfer_to_dia_in(self):
                        f.write(bytearray(line, encoding='utf-8'))

    @api.model
    def get_transfer_to_dia_in(self, picks):
        out = []
        t_purchase_order_line = self.env['purchase.order.line']
        i = 0
        for pick in picks:
            if pick.state not in ['done']:
                continue
            vendor = pick.main_partner_id.dia_ref_vendor
            if not vendor:
                pick.message_post(body=_('<div style="background-color:red;color:white;border-radius:5px"><b>Trasferimento DIA fallito: Manca il codice univoco dia di riferimento Vendor</b></div>'),
                                  message_type='notification')
                pick.send_to_dia = 'error'
                continue
            else:
                if vendor[0:3] not in ['261', '260']:
                    pick.message_post(body=_('<div style="background-color:red;color:white;border-radius:5px"><b>Trasferimento DIA Non Consentito codice fornitore errato deve essere 261</b></div>'),
                                      message_type='notification')
                    pick.send_to_dia = 'error'
                    continue
            for line in pick.move_lines:
                i += 1
                lineTXT = 'B{0:07d}'.format(i)  # Numero documento    1    8    S    Impostare sempre valore B0000001
                lineTXT += FTCL(vendor, 8)  # Codice fornitore    9    8    S
                lineTXT += FTCL(line.product_id.default_code, 16)       # Articolo    17    16    S
                lineTXT += FTCL(line.product_qty, 12)                   # Quantita    33    12    S    usare punto come separatore decimali
                lineTXT += FTCL(datetime.now().strftime("%Y%m%d"), 8)   # Data registrazione    45    8    S    formato yyyymmdd (possiamo preimpostarlo lato nostro con la data odierna)
                if not pick.causale_dia:
                    pick.causale_dia = 'CARA'
                lineTXT += FTCL(pick.causale_dia.name, 4)  # Causale    53    4    S    Impostare sempre CARA (verificare con il cliente se va bene usare sempre questa)
                if pick.causale_dia.causale_type == 'scarico_carico':
                    lineTXT += FTCL("xx", 2)  # Deposito    57    2    S    (possiamo preimpostarlo lato nostro, verificare con il cliente)
                else:
                    lineTXT += FTCL("ZZ", 2)  # Deposito    57    2    S    (possiamo preimpostarlo lato nostro, verificare con il cliente)
                price = line.purchase_line_id
                if not price:
                    order_line_id = line.purchase_order_line_subcontracting_id
                    purchese_order_line = t_purchase_order_line.search([('id', '=', order_line_id)])
                    price = purchese_order_line.price_unit
                price = price * line.product_qty
                lineTXT += safeFTCL(price, 12)   # prezzo 12
                lineTXT += safeFTCL("DDT: " + str(pick.ddt_number), 12)     # Rif.documento    71    12    N
                lineTXT += safeFTCL("DDT Data: " + str(pick.ddt_date), 30)  # Descr.movimento    83    30    N
                lineTXT += "\n"
                out.append(lineTXT)
            pick.send_to_dia = 'updated'
            pick.message_post(body=_('<div style="background-color:green;color:white;border-radius:5px"><b>Trasferimento DIA con successo</b></div>'),
                              message_type='notification')
        return out

    @api.model
    def get_transfer_to_dia_out(self, picks, force_price=True):
        basicErrorDiv = '<div style="background-color:red;color:white;border-radius:5px"><b>%s</b></div>'
        out = []
        for pick in picks:
            if pick.state != 'done':
                pick.message_post(body=basicErrorDiv % _('Trasferimento DIA fallito: Lo stato del DDT deve essere validato.'),
                                  message_type='notification')
                pick.send_to_dia = 'error'
                continue
            to_write = []
            if not pick.main_partner_id.dia_ref_customer:
                pick.message_post(body=basicErrorDiv % _('Trasferimento DIA fallito: Manca il codice univoco dia di riferimento Partner.'),
                                  message_type='notification')
                pick.send_to_dia = 'error'
                continue
            if not pick.causale_dia:
                pick.message_post(body=basicErrorDiv % _('Trasferimento DIA fallito: Manca La causale Dia'),
                                  message_type='notification')
                pick.send_to_dia = 'error'
                continue
            if pick.causale_dia.name == 'XXXX':
                continue
            if not pick.causale_dia.push_to_dia:
                pick.message_post(body=basicErrorDiv % _('Trasferimento DIA fallito: La causale DIA selezionata non è impostata come trasferibile.'),
                                  message_type='notification')
                pick.send_to_dia = 'error'
                continue
            stop_transfer = False
            if not pick.ddt_number:
                pick.message_post(body=basicErrorDiv % _('Trasferimento DIA fallito: Manca il numero DDT'),
                                  message_type='notification')
                pick.send_to_dia = 'error'
                continue
            header = ""
            date_time = datetime.strptime(pick.ddt_date, tools.DEFAULT_SERVER_DATE_FORMAT)
            header += FTCL(date_time.year, 4)       # Anno Bolla    1    4        in rosso i dati di testata (da ripetere su tutte le righe)
            header += FTCL(pick.ddt_number, 8)      # Num Bolla    6    8        in verde i dati di riga
            header += FTCL(date_time.strftime("%Y%m%d"), 8)        # Data Bolla    15    8
            header += FTCL(pick.main_partner_id.dia_ref_customer, 8)  # Cod.Cliente    24    8
            header += FTCL(pick.causale_dia.name, 4)   # Causale    33    4
            header += FTCL(pick.sale_id.payment_term_id.name, 6)    # Pagamento    38    6        campo di testo
            header += FTCL("", 6)  # TODO: da definire Banca    45    6        mettere un campo nelle banche di odoo che dica quale e’ il nome della banca in dia
            header += "01"                          # Deposito Pr.    52    2        passo sempre 01
            ddt_node = str(pick.note_ddt).replace("\n", "")
            header += FTCL(ddt_node[:60], 60)  # Note1    55    60        note_ddt
            header += FTCL(ddt_node[60:], 60)  # Note2    116    60        note_ddt >60
            i = 0
            shippingPartner = pick.partner_id
            if pick.delivery_address:
                shippingPartner = pick.delivery_address
            for line in pick.move_lines:
                i += 1
                lineTXT = header
                lineTXT += FTCL(i, 4)                               # Riga    177    4        progressivo di righa
                lineTXT += FTCL(line.product_id.default_code, 16)   # Articolo    181    16
                if line.quantity_done == 0:
                    continue
                lineTXT += FTCL(line.quantity_done, 12)               # Quantita    198    12
                price = line.sale_line_id.price_unit
                if not price or price < 0:
                    pick.message_post(body=basicErrorDiv % _('Anomalia nel trasferimento dati DIA: Prezzo non settato per il codice prodotto %s' % line.product_id.default_code),
                                      message_type='notification')
                    if not force_price:
                        pick.send_to_dia = 'error'
                        stop_transfer = True
                        break
                lineTXT += FTCL(line.sale_line_id.price_unit, 12)             # line.sale_line_id.price_total ?? Prezzo    211    12
                lineTXT += FTCL(str(line.sale_line_id.order_id.name) or '' + "Rif.Ordc.: " + str(line.sale_line_id.order_id.client_order_ref) or '', 60)      # note1    224    60        numero ordine vendita cliente da sale order    nove_line.sale_line_id.sale_id.name
                lineTXT += FTCL(line.sale_line_id.order_id.origin, 60)    # note2    285    60        riferimento cliente da sale order    nove_line.sale_line_id.sale_id.origin
                lineTXT += FTCL(line.sale_line_id.order_id.analytic_account_id.name, 12)  # Commessa    346    12        nove_line.sale_id.account_analytic.name
                if pick.causale_dia.causale_type == 'scarico_carico':
                    lineTXT += FTCL("xx", 2)  # Deposito Destinazione 2
                else:
                    lineTXT += FTCL("ZZ", 2)  # Deposito Destinazione 2
                lineTXT += FTCL(line.data_decorrenza, 8)             # Data decorrenza    345    8    N
                lineTXT += FTCL(shippingPartner.display_name, 30)    # Ragione sociale destinazione    353    30    N
                lineTXT += FTCL(pick.delivery_address.display_name, 30)           # Ragione sociale 2 destinazione    383    30    N

                lineTXT += FTCL(shippingPartner.street, 60)           # Indirizzo destinazione    413    60    N
                lineTXT += FTCL(shippingPartner.zip, 6)           # CAP destinazione    473    6    N
                lineTXT += FTCL(shippingPartner.city, 60)           # Localita' destinazione    479    60    N
                lineTXT += FTCL(shippingPartner.state_id.code, 2)           # Provincia destinazione    539    2    N
                if shippingPartner.country_id.code == 'IT':
                    lineTXT += FTCL('  ', 2)           # Nazione destinazione    541    2    N
                else:
                    lineTXT += FTCL(shippingPartner.country_id.code, 2)           # Nazione destinazione    541    2    N
                lineTXT += FTCL(pick.main_partner_id.property_account_position_id.dia_code, 4)           # Codice esenzione iva    543    4    N

                lineTXT += "\n"
                to_write.append(lineTXT)
            if not stop_transfer:
                out += to_write
                pick.send_to_dia = 'updated'
                pick.message_post(body=_('<div style="background-color:green;color:white;border-radius:5px"><b>Trasferimento DIA con successo</b></div>'),
                                  message_type='notification')
        return out

    @api.model
    def getDiaNumber(self, code):
        thisYear = datetime.today().year
        whereClouse = """%s%s""" % (thisYear, code)
        sqlSelect = """SELECT LAST_NUM FROM XLDB01.DITTE_PARMS WHERE DITTA_EXP = '1 NP%s'""" % whereClouse
        logging.debug("Execute " + sqlSelect)
        con = None
        row = None
        try:
            con = cx_Oracle.connect('SYSTEM', 'MANAGER', '10.15.0.103/EUR3')
            cur = con.cursor()
            cur.execute(sqlSelect)
            row = cur.fetchone()
        except Exception as ex:
            logging.error("Unable to connect to Oracle/Dia to retrive the ddt number")
        finally:
            if con:
                con.close()
        return whereClouse, row

    @api.model
    def getNumberFromDia(self):
        code = self.causale_dia.code
        if self.causale_dia.code:
            whereClouse, row = self.getDiaNumber(code)
            if not row:
                return None
            return self.env['dia.lastnumber'].getNextNumber(key=whereClouse,
                                                            nextNumber=row[0])
        else:
            raise UserError("Causale Dia non inserita !!")

    @api.model
    def flag_transfer_dia(self):
        for stock_picking_id in self:
            if stock_picking_id.ddt_number and stock_picking_id.causale_dia.push_to_dia:
                stock_picking_id.send_to_dia = 'new'

    @api.one
    def button_ddt_number(self):
        res = super(stock_picking_custom, self).button_ddt_number()
        newNumber = self.getNumberFromDia()
        if newNumber:
            self.ddt_number = newNumber
        self.flag_transfer_dia()
        return res

    @api.multi
    def button_validate(self):
        ret = super(stock_picking_custom, self).button_validate()
        self.flag_transfer_dia()
        return ret


class ProgresNumber(object):
    def __init__(self, value):
        self._value = value
        self._intNumber = int(value[1:])
        self._just = len(value) - 1

    def __gt__(self, other):
        return(self._intNumber > other._intNumber)

    def __lt__(self, other):
        return (self._intNumber < other._intNumber)

    def __le__(self, other):
        return(self._intNumber <= other._intNumber)

    def __ge__(self, other):
        return(self._intNumber >= other._intNumber)

    def __eq__(self, other):
        return (self._intNumber == other._intNumber)

    def __ne__(self, other):
        return not(self.__eq__(other))

    def nextNumber(self):
        self._intNumber += 1
        return self._value[0] + str(self._intNumber).rjust(self._just).replace(" ", "0")

    def __str__(self):
        return self._value


class DiaLastNumber(models.Model):
    _name = 'dia.lastnumber'
    key = fields.Char("Key")
    last_number = fields.Char("Last Number")

    @api.model
    def getNextNumber(self, key, nextNumber, create=True):
        objToNext = ProgresNumber(nextNumber)
        for dia_lastNumber in self.search([('key', '=', key)]):
            lastNumber = dia_lastNumber.last_number
            objToNext = ProgresNumber(lastNumber) if ProgresNumber(lastNumber) > objToNext else objToNext
            if create:
                dia_lastNumber.last_number = objToNext.nextNumber()
                return dia_lastNumber.last_number
            return objToNext.nextNumber()
        if create:
            new_obj = self.create({'key': key,
                                   'last_number': objToNext.nextNumber()})
            return new_obj.last_number
        return objToNext.nextNumber()

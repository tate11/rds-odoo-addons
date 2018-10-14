# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import os
import logging
from odoo import api
from odoo import fields
from odoo import models
from odoo import _
from odoo.exceptions import UserError
from .common import getDiaUOM
from .common import FTCL
try:
    import cx_Oracle
except Exception as ex:
    logging.warning("Unable to import cx_oracle module some functionality may not work %s" % ex)

from_path = '/mnt/dia/odoo'
if not os.path.exists(from_path):
    logging.error("Path mnt/dia not defined")
    from_path = '/tmp/'
WRITE_PRODUCT_PATH = os.path.join(from_path, 'prodotti.txt')
WRITE_PRODUCT_UPDATE_PATH = os.path.join(from_path, 'u_prodotti.txt')


class ProductTemplate(models.Model):

    _inherit = ['product.template']

    legacy_code = fields.Char(string="Dia Code")
    legacy_code_gruppo_merciologico = fields.Char(string="Gruppo Merciologico dia",
                                                  size=2)
    send_to_dia = fields.Selection([('new', 'New'),
                                    ('modifie', 'Modifie'),
                                    ('updated', 'Updated')],
                                   default='new')

    @api.model
    def prendi_dati_da_dia_totale(self):
        self.env['product.template'].search([]).prendi_dati_da_dia()

    @api.multi
    def prendi_dati_da_dia(self):
        try:
            con = cx_Oracle.connect('asal', 'ace0896AC21', '10.15.0.103/EUR3')
            cur = con.cursor()
            for i in self:
                if not i.legacy_code:
                    return
                t = cur.execute("SELECT DES_ART, DES_ART2, ULTIMO_PREZZO, ULTIMO_COSTO, PESO, ORDINABILE, PRODUCIBILE FROM XLDB01.AN_ART WHERE ARTICOLO like '1 " + i.legacy_code + "%'").fetchone()
                if(t):
                    values = {}
                    values['list_price'] = t[2]
                    values['standard_price'] = t[3]
                    values['weight'] = t[4] / 1000
                    values['sale_ok'] = True if t[5] == 'S' else False
                    i.name = (t[0] + t[1]).strip()
                    i.write(values)
        except Exception as ex:
            logging.error(ex)
            raise UserError("Unable to Get Data from DIA")

    @api.model
    def get_dia_line(self, product):
        lineTXT = ""
        code = product.legacy_code if product.legacy_code else product.default_code
        if not code:
            product.message_post(body=_('<div style="background-color:red;color:white;border-radius:5px"><b>Trasferimento DIA fallito: Manca il codice prodotto</b></div>'),
                                 message_type='notification')
            return None
        lineTXT += FTCL(code, 16)                           # Codice    1    16    S
        lineTXT += FTCL(product.name[:30], 30)              # Descrizione    17    30    N
        lineTXT += FTCL(product.name[30:], 30)              # Descrizione 2    47    30    N
        lineTXT += FTCL(getDiaUOM(product.uom_id.id), 2)             # Unità di misura    77    2    S
        lineTXT += FTCL(product.taxes_id.dia_legacy_code, 2)           # Codice iva    79    2    S    (può essere eventualmente inserito un valore di default)
        gruppo_merc = product.legacy_code_gruppo_merciologico
        if not gruppo_merc:
            gruppo_merc = ''    # DEFAULT VALUE NOT SURE IF IT'S CORRECT
            product.legacy_code_gruppo_merciologico = gruppo_merc
        lineTXT += FTCL(gruppo_merc, 2)             # Gruppo merc.  81    2    S    (può essere eventualmente inserito un valore di default)
        acquisto = "A"          # DEFAULT VALUE NOT SURE IF IT'S CORRECT
        for route in product.route_ids:
            if route.name in ['Manufacture']:
                acquisto = "P"
                break
            elif route.name in ['Buy']:
                acquisto = "A"
                break
        lineTXT += acquisto                         # Acquistato/Prodotto    83    1    S    (può essere eventualmente inserito un valore di default)
        lineTXT += "I"                              # deciso con consulente dia di mettere I di default Prod.interno/esterno    84    1    S    I/E (se prodotto) - (può essere eventualmente inserito un valore di default)
        lineTXT += "\n"
        return lineTXT

    @api.one
    def transfer_to_dia(self):
        if self.send_to_dia == 'modifie':
            write_path = WRITE_PRODUCT_UPDATE_PATH
        elif self.send_to_dia == 'new':
            write_path = WRITE_PRODUCT_PATH
        else:
            return
        if os.path.exists(write_path):
            self.message_post(body=_('<div style="background-color:red;color:white;border-radius:5px"><b>Trasferimento DIA fallito: File %s gia presente nel direttorio condiviso</b></div>' % write_path),
                              message_type='notification')
            return
        with open(write_path, 'wb') as f:
            if self:
                line = self.get_dia_line(self)
                if line:
                    f.write(bytearray(line, encoding='utf-8'))
                    self.send_to_dia = 'updated'
                    self.message_post(body=_('<div style="background-color:green;color:white;border-radius:5px"><b>Trasferimento DIA con successo</b></div>'),
                                      message_type='notification')

    @api.multi
    def cron_send_to_dia(self):
        if os.path.exists(WRITE_PRODUCT_UPDATE_PATH):
            self.message_post(body=_('<div style="background-color:red;color:white;border-radius:5px"><b>Trasferimento DIA fallito: File %s gia presente nel direttorio condiviso</b></div>' % WRITE_PRODUCT_UPDATE_PATH),
                              message_type='notification')
            return False
        with open(WRITE_PRODUCT_UPDATE_PATH, 'wb') as f:
            for product_product in self.env['product.template'].search([('send_to_dia', '=', 'modifie')]):
                if product_product:
                    line = self.get_dia_line(product_product)
                    if line:
                        f.write(bytearray(line, encoding='utf-8'))
                        product_product.send_to_dia = 'updated'
                        product_product.message_post(body=_('<div style="background-color:green;color:white;border-radius:5px"><b>Trasferimento DIA con successo</b></div>'),
                                                     message_type='notification')
        if os.path.exists(WRITE_PRODUCT_PATH):
            self.message_post(body=_('<div style="background-color:red;color:white;border-radius:5px"><b>Trasferimento DIA fallito: File %s gia presente nel direttorio condiviso</b></div>' % WRITE_PRODUCT_PATH),
                              message_type='notification')
            return False
        with open(WRITE_PRODUCT_PATH, 'wb') as f:
            for product_product in self.env['product.template'].search([('send_to_dia', '=', 'new')]):
                if product_product:
                    line = self.get_dia_line(product_product)
                    if line:
                        f.write(bytearray(line, encoding='utf-8'))
                        product_product.send_to_dia = 'updated'
                        product_product.message_post(body=_('<div style="background-color:green;color:white;border-radius:5px"><b>Trasferimento DIA con successo</b></div>'),
                                                     message_type='notification')
        return True

    @api.multi
    def write(self, vals):
        if self.send_to_dia == 'updated':
            vals['send_to_dia'] = vals.get('send_to_dia', 'modifie')
        res = super(ProductTemplate, self).write(vals)
        return res

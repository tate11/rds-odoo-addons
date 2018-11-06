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

from .common import PRODUCT_FILE, UPDATE_PRODUCT_FILE



class ProductTemplate(models.Model):
    _inherit = ['dia.transferable', 'product.template']
    _name = "product.template"

    dia_code = fields.Char(string="Codice Articolo DIA")
    legacy_code_gruppo_merciologico = fields.Char(string="Gruppo Merciologico dia",
                                                  size=2)

    @api.multi
    def get_transfer_data(self):
        ins = []
        upd = []
        
        for product in self:
            lineTXT = ""
            code = product.dia_code or product.default_code
            if not code:
                product.write({'dia_transfer_status': 'failed', 'dia_transfer_notes': _("Codice Articolo DIA non valido o non impostato!")})
                continue

            lineTXT += FTCL(code, 16)                           # Codice    1    16    S
            lineTXT += FTCL(product.name[:30], 30)              # Descrizione    17    30    N
            lineTXT += FTCL(product.name[30:], 30)              # Descrizione 2    47    30    N
            lineTXT += FTCL(getDiaUOM(product.uom_id.id), 2)             # Unità di misura    77    2    S
            lineTXT += FTCL(product.taxes_id.dia_code, 2)           # Codice iva    79    2    S    (può essere eventualmente inserito un valore di default)
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
            lineTXT += acquisto                       # Acquistato/Prodotto    83    1    S    (può essere eventualmente inserito un valore di default)
            lineTXT += "I"                              # deciso con consulente dia di mettere I di default Prod.interno/esterno    84    1    S    I/E (se prodotto) - (può essere eventualmente inserito un valore di default)
            lineTXT += "\n"
  
            if product.dia_transfer_type == 'insert':
                ins.append(lineTXT)
            else:
                upd.append(lineTXT)
            
            product.write({'dia_transfer_status': 'success', 'dia_transfer_notes': False})

        return ins, upd

    @api.multi
    def transfer_to_dia(self):
        p_ins, p_upd = self.get_transfer_data()

        if p_ins:
            if os.path.exists(PRODUCT_FILE):
                self.filtered(lambda x: x.customer and (x.dia_transfer_type == 'insert')).write({'dia_transfer_notes': _('Trasferimento fallito: Il file prodotti.txt non è ancora stato processato da DIA!'), 'dia_transfer_status': 'failed'})
            else:
                with open(PRODUCT_FILE, 'wb') as f:
                    for lineTXT in p_ins:
                        f.write(bytearray(lineTXT, encoding='utf-8'))

        if p_upd:
            if os.path.exists(UPDATE_PRODUCT_FILE):
                self.filtered(lambda x: x.customer and (x.dia_transfer_type == 'insert')).write({'dia_transfer_notes': _('Trasferimento fallito: Il file u_prodotti.txt non è ancora stato processato da DIA!'), 'dia_transfer_status': 'failed'})
            else:
                with open(UPDATE_PRODUCT_FILE, 'wb') as f:
                    for lineTXT in p_upd:
                        f.write(bytearray(lineTXT, encoding='utf-8'))

        return self.mapped(lambda x: x.dia_transfer_status)

    @api.multi
    def write(self, vals):
        if (not vals.get('dia_transfer_status')) and (self.dia_transfer_status == 'success'):
            vals['dia_transfer_status'] = vals.get('dia_transfer_status', 'draft')
            vals['dia_transfer_type'] = vals.get('dia_transfer_type', 'update')
            vals['dia_transfer_id'] = self.sudo().env['dia.transfer'].get_next().id

        return super(ProductTemplate, self).write(vals)

    @api.model
    def create(self, vals):
        res = super(ProductTemplate, self).create(vals)

        res.dia_transfer_id = self.sudo().env['dia.transfer'].get_next()
        res.dia_transfer_status = 'draft'

        return res
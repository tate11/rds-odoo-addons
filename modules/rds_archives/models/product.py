# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import os
import logging
from odoo import api
from odoo import fields
from odoo import models
from odoo import _
from odoo.exceptions import UserError

logger = logging.getLogger()

try:
    import cx_Oracle
except Exception as ex:
    logging.warning("Unable to import cx_oracle module some functionality may not work %s" % ex)


class ProductProduct(models.Model):

    _inherit = ['product.product']

    @api.model
    def uom_translate(self, value, strict=False):
        UOM_TRANSLATOR = {
            'KG': self.env.ref("uom.product_uom_kgm"),
            'GR': self.env.ref("uom.product_uom_gram"),
            'LT': self.env.ref("uom.product_uom_litre"),
            'PZ': self.env.ref("uom.product_uom_unit")
        } 
        if strict:
            return UOM_TRANSLATOR.get(value.strip(), False)
        else:
            return UOM_TRANSLATOR.get(value.strip(), self.env.ref("uom.product_uom_unit"))

    @api.model
    def dia2vals(self, code):      
        con = cx_Oracle.connect('asal', 'ace0896AC21', '10.15.0.103/EUR3')
        cur = con.cursor()
        t = cur.execute("""
            SELECT d.DES_ART, d.DES_ART2, d.ULTIMO_PREZZO, d.ULTIMO_COSTO, d.PESO, d.UMIS, d.ULTIMO_ACQ, d.ULTIMA_VEND, d.ARTICOLO_CLI, p.LEAD_TIME_ART
            FROM XLDB01.AN_ART d
            LEFT JOIN XLDB02.AN_ART_TEC p ON d.ARTICOLO = p.PARTE 
            WHERE ARTICOLO LIKE '1 {}%'
            """.format(str(code))).fetchone()

        if not t:
            return False

        vals = {
            'list_price': float(t[2]),
            'standard_price': float(t[3]),
            'weight': float(t[4]) / 1000,
            'sale_ok': bool(t[7].strip()),
            'purchase_ok': bool(t[6].strip()),
            'name': t[0].strip() + (bool(t[1].strip()) and " {}".format(t[1].strip() or "")),
            'default_code': code,
            'uom_id': self.uom_translate(t[5]).id,
            'uom_po_id': self.uom_translate(t[5]).id,
            'produce_delay': float(t[9]),
            'description': bool(t[8].strip) and "Altri Riferimenti:\n   - {}".format(t[8].strip()) or ""
        }

        return vals

    def get_or_make(self, code):
        code = code[2:].strip()
        
        product = self.search([('default_code', '=', code)])
        if product:
            return product[0]
        
        art = self.create(self.dia2vals(code))
        logger.warning("Articolo {} non trovato. Lo creo e discendo la distinta!".format(art.default_code))

        art.build_article()
        return art

    def build_bom_from_dia(self):
        def make_bom_line_vals(bom_line):
            product = self.env['product.product'].get_or_make(bom_line[2])
            uom = self.uom_translate(bom_line[6])

            logger.error("UOM non trovata per bom {},  componente {}, verificare!".format(self.default_code, product.default_code))
            return {
                'product_id': product.id,
                'product_qty': uom and float(bom_line[3]) or float(bom_line[3])*(float(bom_line[7]) if float(bom_line[7]) != 0 else 1),
                'product_uom_id': uom and uom.id or product.uom_id.id
            }

        con = cx_Oracle.connect('asal', 'ace0896AC21', '10.15.0.103/EUR3')
        cur = con.cursor()
        t = cur.execute("""
                            SELECT d.ID_STRUTTURA, d.PADRE, d.COMPONENTE, d.QUANTITA, tpad.UMIS_PROD, tpad.CONV_UM_PROD, tcon.UMIS_PROD, tcon.CONV_UM_PROD
                            FROM XLDB02X.STRUTTURE d
                            LEFT JOIN XLDB02.AN_ART_TEC tpad ON d.PADRE = tpad.PARTE
                            LEFT JOIN XLDB02.AN_ART_TEC tcon ON d.COMPONENTE = tcon.PARTE               
                            WHERE PADRE LIKE '1 {}%'
                        """.format(str(self.default_code))).fetchall()
        if not(t):
            logger.warning("Nessuna distinta ulteriore trovata per {}, risalgo...".format(self.default_code))
            return

        logger.warning("Distinta trovata per {}, creo e discendo...".format(self.default_code))

        boms = set(map(lambda x: x[0], t))

        for bom in boms:
            bom_lines = list(filter(lambda x: x[0] == bom, t))
            uom = self.uom_translate(bom_lines[0][4].strip())
            if not uom:
                if bool(bom_lines[0][4].strip()):
                    logger.error("UOM {} non trovata per {}, verificare!".format(bom_lines[0][4],  self.default_code))
                else:
                    logger.warning("UOM non specificata per {}, verificare!".format(self.default_code))

            vals = {
                'product_tmpl_id': self.product_tmpl_id.id,
                'product_qty': uom and 1 or (float(bom_lines[0][5]) if float(bom_lines[0][5]) != 0 else 1),
                'product_uom_id': uom and uom.id or self.uom_id.id,
                'code': bom.strip(),
                'bom_line_ids': [(0, 0, make_bom_line_vals(line)) for line in bom_lines]
            }
            self.env['mrp.bom'].create(vals)

    @api.multi
    def build_customerinfo(self):
        con = cx_Oracle.connect('asal', 'ace0896AC21', '10.15.0.103/EUR3')
        cur = con.cursor()
        t = cur.execute("""
                            SELECT CONTO, ARTICOLO_CLI, DES_ART_CLI, DES_ART2_CLI, NOTE_ART_CLI, NOTE2_ART_CLI
                            FROM XLDB01X.ART_CLIENTI
                            WHERE ARTICOLO LIKE '1 {}%'
                        """.format(str(self.default_code))).fetchall()

        for row in t:
            cli = self.env['res.partner'].search([('dia_ref_customer', '=', row[0][2:].strip())], limit=1)
            if not cli:
                logger.warning("Cliente {} non trovato. Salto.".format(row[0][2:].strip()))
                continue

            self.env['product.customerinfo'].create({
                                                        'product_tmpl_id': self.product_tmpl_id.id,
                                                        'name': cli[0].id,
                                                        'description': row[2].strip() + row[3].strip(),
                                                        'code': row[1].strip(),
                                                        'notes': row[4].strip() + row[5].strip()
                                                    })

    @api.multi
    def build_pricelists(self):
        con = cx_Oracle.connect('asal', 'ace0896AC21', '10.15.0.103/EUR3')
        cur = con.cursor()
        t = cur.execute("""
                            SELECT d.CONTO, d.PREZZO_PCLI, d.LISTINO, l.DES_LISTINO
                            FROM XLDB01X.PREZZI_ART_CLI d
                            LEFT JOIN XLDB01.LISTINI l ON d.LISTINO = l.LISTINO
                            WHERE ARTICOLO LIKE '1 {}%'
                        """.format(str(self.default_code))).fetchall()
        for row in t:
            cli = self.env['res.partner'].search([('dia_ref_customer', '=', row[0][2:].strip())], limit=1)
            if not cli:
                logger.warning("Cliente {} non trovato. Salto.".format(row[0][2:].strip()))
                continue
            pl = self.env['product.pricelist'].search([('name', 'like', '(CLI-{})%'.format(cli.ids[0]))], limit=1)
            if not pl:
                logger.warning("Listino {} non trovato. Creo.".format(row[2].strip()))
                pl = self.env['product.pricelist'].create({'name': "(CLI-{}) {}".format(cli.ids[0], cli[0].name)})

            cli.property_product_pricelist = pl

            self.env['product.pricelist.item'].create(
                {
                    'product_tmpl_id': self.product_tmpl_id.id,
                    'product_id': self.id,
                    'pricelist_id': pl.ids[0],
                    'fixed_price': float(row[1])
                }
            )

   
    @api.multi
    def build_article(self):
        for i in self:
            vals = self.dia2vals(i.default_code)
            if not vals:
                logger.error("Articolo {} saltato perché non rintracciabile nel DB dia.".format(i.default_code))
                continue
            logger.warning("Inizio articolo {}. Trovati dati in DIA.".format(i.default_code))
            i.write(vals)
            i.build_bom_from_dia()
            logger.warning("Ricostruito in toto articolo {} e relativi sottoarticoli. Ricreo relazioni con clienti...".format(i.default_code))
            i.build_customerinfo()
            logger.warning("Ricreo listini articolo {}...".format(i.default_code))
            i.build_pricelists()
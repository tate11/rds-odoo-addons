# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import os
import logging
from odoo import api
from odoo import fields
from odoo import models
from odoo import _
from odoo.exceptions import UserError, ValidationError

logger = logging.getLogger()

try:
    import cx_Oracle
except Exception as ex:
    logging.warning("Unable to import cx_oracle module some functionality may not work %s" % ex)


class ResPartner(models.Model):

    _inherit = ['res.partner']

    @api.model
    def dia2vals(self, code):

        con = cx_Oracle.connect('asal', 'ace0896AC21', '10.15.0.103/EUR3')
        cur = con.cursor()
        t = cur.execute("""
            SELECT d.CONTO, d.P_IVA, tl.ID_FISC_COD_DF, tl.CFIS_DF
            FROM XLDB01.AN_CLI d
            LEFT JOIN XLDB01.AN_CLIFOR_FISC tl ON tl.CONTO = d.CONTO 
            WHERE d.CONTO LIKE '1 {}%'
            """.format(str(code))).fetchone()

        if not t:
            t = cur.execute("""
                SELECT d.CONTO, d.P_IVA, tl.ID_FISC_COD_DF, tl.CFIS_DF
                FROM XLDB01.AN_FOR d
                LEFT JOIN XLDB01.AN_CLIFOR_FISC tl ON tl.CONTO = d.CONTO 
                WHERE d.CONTO LIKE '1 {}%'
                """.format(str(code))).fetchone()

        if not t:
            return False


        vals = {
            'vat': t[1].strip(),
            'fiscalcode': (t[3] and t[3].strip()) or (t[2] and t[2].strip())
        }

        return vals

    @api.multi
    def customer_fix_vat_fc(self):
        for i in self:
            ref_customer, ref_vendor = getattr(i, 'dia_ref_customer'), getattr(i, 'dia_ref_vendor')
            
            vals = self.dia2vals(ref_customer or ref_vendor)
            if not vals:
                logger.error("Cliente ({}) {} saltato perché non rintracciabile nel DB dia.".format(i.id, i.name))
                continue
            try:
                i.write(vals)
            except ValidationError:
                continue
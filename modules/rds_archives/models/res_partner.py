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



class PaymentTerm(models.Model):
    _inherit = ['account.payment.term']

    def get_or_make(self, code, desc):
        if (not code) or not code.strip():
            return False
        res = self.search([('dia_code', '=', code.strip())])
        if not res:
            res = self.create({'name': desc, 'dia_code': code.strip()})
        return res

class ResPartner(models.Model):

    _inherit = ['res.partner']

    @api.model
    def dia2vals(self, code, mode="cli"):

        con = cx_Oracle.connect('asal', 'ace0896AC21', '10.15.0.103/EUR3')
        cur = con.cursor()

        if mode == "cli":
            t = cur.execute("""
                SELECT d.CONTO, d.P_IVA, d.PAGAMENTO, p.DES_PAG, tl.ID_FISC_COD_DF, tl.CFIS_DF
                FROM XLDB01.AN_CLI d
                LEFT JOIN XLDB01.AN_CLIFOR_FISC tl ON tl.CONTO = d.CONTO
                LEFT JOIN XLDB01.PAGAMENTI p ON p.PAGAMENTO = d.PAGAMENTO 
                WHERE d.CONTO LIKE '1 {}%'
                """.format(str(code))).fetchone()
            pcode = 'property_payment_term_id'

        elif mode == "for":
            t = cur.execute("""
                SELECT d.CONTO, d.P_IVA, d.PAGAMENTO, p.DES_PAG, tl.ID_FISC_COD_DF, tl.CFIS_DF
                FROM XLDB01.AN_FOR d
                LEFT JOIN XLDB01.AN_CLIFOR_FISC tl ON tl.CONTO = d.CONTO
                LEFT JOIN XLDB01.PAGAMENTI p ON p.PAGAMENTO = d.PAGAMENTO
                WHERE d.CONTO LIKE '1 {}%'
                """.format(str(code))).fetchone()
            pcode = 'property_supplier_term_id'

        if not t:
            return False


        vals = {
            'vat': t[1].strip(),
            'fiscalcode': (t[5] and t[5].strip()) or (t[4] and t[4].strip()) or "",
            pcode: self.env['account.payment.term'].get_or_make(t[2], t[3]).id
        }

        return vals

    @api.multi
    def customer_fix_vat_fc(self):
        for i in self:
            vals = False
            ref_customer, ref_vendor = getattr(i, 'dia_ref_customer'), getattr(i, 'dia_ref_vendor')


            if ref_vendor:
                vals = self.dia2vals(ref_vendor, mode="for")

            if ref_customer:
                f_vals = self.dia2vals(ref_customer)
                if vals:
                    for key in f_vals.keys():
                        vals[key] = f_vals[key]

            if not vals:
                logger.error("Cliente ({}) {} saltato perché non rintracciabile nel DB dia.".format(i.id, i.name))
                continue
            try:
                i.write(vals)
            except ValidationError:
                continue

import logging
from odoo import api, fields, models

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, float_compare
from datetime import datetime, timedelta, time

try:
    import cx_Oracle
except Exception as ex:
    logging.warning("Unable to import cx_oracle module some functionality may not work %s" % ex)


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ['sale.order', 'rds.mixin']

    def controlla_dati_per_dia(self):
        con = cx_Oracle.connect('asal', 'ace0896AC21', '10.15.0.103/EUR3')
        cur = con.cursor()

        conto_cont = bool(cur.execute("SELECT COUNT(*)  FROM XLDB01.AN_CLI WHERE CONTO like '1 %s" % self.partner_id.ref).fetchone()[0][0]) #RAG. SOC
        conto_fatt = bool(cur.execute("SELECT COUNT(*) FROM XLDB01.AN_CLI WHERE CONTO like '1 %s" % self.partner_invoice_id.ref).fetchone()[0][0]) #RAG. SOC
        conto_sped = bool(cur.execute("SELECT COUNT(*) FROM XLDB01.AN_CLI WHERE CONTO like '1 %s" % self.partner_shipping_id.ref).fetchone()[0][0])  #RAG. SOC

        i_ok = False
        for i in self.order_line:
            i_ok = bool(cur.execute("SELECT COUNT(*) FROM XLDB01.AN_ART WHERE ARTICOLO like '1 %s" % i.product_id.legacy_code).fetchall()[0][0])
            if i_ok is False:
                break

        con.close()
        if conto_cont & conto_fatt & conto_sped & i_ok:
            self.carica_dati_a_dia()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_old_dia_qty = fields.Float("Qty Dia")
    dia_product_delivery_date = fields.Datetime('Data Dia')
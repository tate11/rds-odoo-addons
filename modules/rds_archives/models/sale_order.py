# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import os
import logging
from odoo import api
from odoo import fields
from odoo import models
from odoo import _
from odoo.exceptions import UserError, ValidationError
import csv, itertools
_logger = logging.getLogger()

try:
    import psycopg2
except Exception as ex:
    logging.warning("Unable to import psycopg2 module. some functionality may not work %s" % ex)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def load_from_csv(self, mode='dry_run'):
        ORDER = self
        LINE = self.env['sale.order.line']
        PARTNER = self.env['res.partner']
        PRODUCT = self.env['product.product']

        """
-- CSV Generation Query
COPY (
    SELECT 
        o.id order_id, o.name order_name, o.client_order_ref, -- 0, 1, 2
        p.dia_ref_customer order_partner, p.name, p.vat, -- 3, 4, 5
        ps.dia_ref_customer shipping_partner, ps.name, ps.vat, -- 6, 7, 8
        pf.dia_ref_customer invoice_partner, pf.name, pf.vat, -- 9, 10, 11
        l.id line_id, l.name line_description, prd.default_code, l.product_uom_qty, l.price_unit, l.qty_delivered, -- 12, 13, 14, 15, 16, 17
        o.date_order, (o.date_order + CONCAT(l.customer_lead::text, ' day')::interval) commitment_date, l.requested_date -- 18, 19, 20
    FROM sale_order_line l 
        LEFT JOIN sale_order o ON l.order_id = o.id 
        LEFT JOIN res_partner p ON p.id = o.partner_id
        LEFT JOIN res_partner ps ON ps.id = o.partner_shipping_id
        LEFT JOIN res_partner pf ON pf.id = o.partner_invoice_id
        LEFT JOIN product_product prd ON l.product_id = prd.id
    WHERE l.state='sale' AND l.product_uom_qty > l.qty_delivered AND prd.default_code<>'Delivery'
) TO '/tmp/test.csv' WITH CSV HEADER DELIMITER ',';
        """
        
        partner_errors = list()
        product_errors = list()
        log_stream = list()

        def get_partner(ref, name, vat, fallback=False):
            result = False
            if ref:
                result = PARTNER.search([('dia_ref_customer', '=', ref)], limit=1)
            
            if not result:
                if [ref, name, vat] not in partner_errors:
                    partner_errors.append([ref, name, vat])
                log_stream.append("Missing partner {} ({})".format(name, vat) + (ref and ", Dia Ref. {}!".format(ref) or "!"))
            return result or fallback

        def get_product(ref, desc):
            result = False
            if ref:
                result = PRODUCT.search([('default_code', '=', ref)], limit=1) 
            if not result:
                if [ref, desc] not in product_errors:
                    product_errors.append([ref, desc])
                log_stream.append("Missing product {} ({})!".format(desc, ref))

            return result

        with open("/tmp/order_lines.csv") as file:
            raw_data = list(csv.reader(file))[1:]

        created_orders = ORDER
        created_lines = LINE

        for i in raw_data:
            p_ord = get_partner(i[3], i[4], i[5])
            if not p_ord:
                log_stream.append("[GRAVE] Missing order partner. Skipping order ({}) {}, line ({}) {}.".format(i[0], i[1], i[10], i[11]))
                continue

            p_ship = get_partner(i[6], i[7], i[8], p_ord)
            p_fact = get_partner(i[9], i[10], i[11], p_ord)

            product = get_product(i[14], i[13])
            if not product:
                if mode != "force":
                    log_stream.append("[GRAVE] Missing line product. Skipping order ({}) {}, line ({}) {}.".format(i[0], i[1], i[10], i[11]))
                    continue

                product = PRODUCT.create({'default_code': i[14], 'name': 'foo', 'type': 'service'})


            if mode == 'test_static':
                continue

            elif mode == 'dry_run':
                order = ORDER.search([
                    ('partner_id', '=', p_ord.id),
                    ('partner_shipping_id', '=', p_ship.id),
                    ('partner_invoice_id', '=', p_fact.id),
                    ('client_order_ref', '=', i[2]),
                    ('commitment_date', 'like', '{}%'.format(max(i[19][:10], i[20][:10]))),
                    ('date_order', 'like', '{}%'.format(i[18][:10])),
                ], limit=1)

                if not order:
                    order = ORDER.new({
                    'name': i[1],
                    'partner_id': p_ord.id,
                    'partner_shipping_id': p_ship.id,
                    'partner_invoice_id': p_fact.id,
                    'client_order_ref': i[2],
                    'commitment_date': max(i[19][:10], i[20][:10]),
                    'date_order': i[18][:10],
                    })
                
                line = LINE.new({
                    'order_id': order.id,
                    'product_id': product.id,
                    'name': i[13],
                    'product_uom_qty': float(i[15]) - float(i[17]),
                    'price_unit': float(i[16])
                })
                created_orders += (order if order.id not in created_orders.ids else ORDER)
                created_lines += (line if line.id not in created_lines.ids else LINE)
            
            else:
                order = ORDER.search([
                    ('partner_id', '=', p_ord.id),
                    ('partner_shipping_id', '=', p_ship.id),
                    ('partner_invoice_id', '=', p_fact.id),
                    ('client_order_ref', '=', i[2]),
                    ('commitment_date', 'like', '{}%'.format(max(i[19][:10], i[20][:10]))),
                    ('date_order', 'like', '{}%'.format(i[18][:10])),
                ], limit=1)

                if not order:
                    order = ORDER.create({
                    'name': i[1],
                    'partner_id': p_ord.id,
                    'partner_shipping_id': p_ship.id,
                    'partner_invoice_id': p_fact.id,
                    'client_order_ref': i[2],
                    'commitment_date': max(i[19][:10], i[20][:10]),
                    'date_order': i[18][:10],
                    })

                    order.message_post(body="""
                        <div style="background: #7caeff;text-align:center; padding:1em">
                            <h2><b><font style="color: rgb(66, 66, 66);">Ordine Importato </font></b></h2>
                            <p><font style="color: rgb(66, 66, 66);"><b>L'ordine è stato importato da ODOO v11.</b></font></p>
                            <p></p>
                            <p>
                                <a href="https://odoo-old.rdsmoulding.com/web#id={}&amp;view_type=form&amp;model=sale.order&amp;action=374&amp;menu_id=255" class="btn btn-default" target="_blank" data-original-title="" title="" aria-describedby="tooltip650682"><b><font class="text-alpha" style="">Visualizza ordine originale</font></b></a>
                                <br>
                                </p><p>
                            </p>
                        </div>   
                    """.format(i[0]))
                
                line = LINE.create({
                    'order_id': order.id,
                    'product_id': product.id,
                    'name': i[13],
                    'product_uom_qty': float(i[15]) - float(i[17]),
                    'price_unit': float(i[16])
                })
                created_orders += (order if order.id not in created_orders.ids else ORDER)
                created_lines += (line if line.id not in created_lines.ids else LINE)

        log_stream.append("Created {} lines across {} orders, out of {} datafile lines.".format(len(created_lines), len(created_orders), len(raw_data)))


        with open("/tmp/partner_errors.csv", 'w', newline='') as file:
            wr = csv.writer(file, quoting=csv.QUOTE_ALL)
            wr.writerows(partner_errors) 
        
        with open("/tmp/product_errors.csv", 'w', newline='') as file:
            wr = csv.writer(file, quoting=csv.QUOTE_ALL)
            wr.writerows(product_errors) 

        with open("/tmp/log.log", 'w') as file:
            file.write("\n".join(log_stream)) 

        '''
        for i in data_refined.keys():
            order = data_refined[i][0]
            
           
            s_ord = 
            f_ord = order[5] and PARTNER.search([('dia_ref_customer', '=', order[5])], limit=1)
            commitment_date = order[-2] if order[-2] >= order[-1] else order[-1]
            err = []

            if not p_ord:
                p_ord = PARTNER.browse(1)
                err += ['Partner principale mancante']

            vals = {'partner_id': p_ord.id, 'commitment_date': commitment_date}

            if s_ord:
                vals['partner_shipping_id'] = s_ord.id
            elif order[4]:
                err.append('Partner di spedizione mancante.')

            if f_ord:
                vals['partner_invoice_id'] = f_ord.id
            elif order[5]:
                err.append('Partner di fatturazione mancante.')

            new_ord = ORDER.create(vals)

            body="""<p>Ordine creato da&nbsp;<a href="https://odoo.rdsmoulding.com/web#id={}&amp;view_type=form&amp;model=sale.order&amp;menu_id=255&amp;action=377" class="btn btn-outline-alpha" target="_blank">SO0001</a>.</p>""".format(order)[0]

            if err:
                body += "<p>Sono stati incontrati degli errori:</p><ul>{}</ul>".format("".join(["<li>" + x + "</li>" for x in err]))

            new_ord.message_post(body=body)
        '''
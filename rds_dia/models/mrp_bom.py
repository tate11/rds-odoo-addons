'''
Created on 29 May 2018

@author: mboscolo
'''
import logging
from odoo import api
from odoo import fields
from odoo import models
from odoo.exceptions import UserError
import glob
import os
import base64

PATH_TO_READ = "/mnt/quality/E*.pdf"


class mrp_bom(models.Model):
    _inherit = 'mrp.bom'

    @api.model
    def uploadRoutindDocuments(self):
        product_product_obj = self.env['product.product']
        for pdf_file in glob.glob(PATH_TO_READ):
            name = os.path.basename(pdf_file)
            name = name.replace(".pdf", "")
            for product_product_id in product_product_obj.search([('default_code', '=', name)]):
                for bom_id in product_product_id.bom_ids:
                    for operation in bom_id.routing_id.operation_ids:
                        if operation.name == 'ALAUT':
                            with open(pdf_file, 'rb') as f:
                                operation.worksheet = base64.b64encode(f.read())
                                logging.info("Uploaded data to operation %r" % operation.display_name)
        return True

    @api.model
    def uploadSubcontracting(self, datas=[]):
        uom_ids = {}
        for uom_id in self.env['product.uom'].search([]):
            uom_ids[uom_id.name] = uom_id.id
        errors = []
        product_product_obj = self.env['product.product']
        res_partner_obj = self.env['res.partner']
        product_supplierinfo_obj = self.env['product.supplierinfo']
        datasLen = len(datas)
        for data in datas:
            logging.info('Evaluating [%s / %s]' % (datas.index(data), datasLen))
            codice = data.get('codice_articolo', '')
            product_product_id = product_product_obj.search([('default_code', '=', codice)],
                                                            limit=1)
            if not product_product_id:
                msgErr = "Product %r not present in odoo " % codice
                errors.append(msgErr)
                continue
            bom_id = product_product_id.bom_ids
            if not bom_id:
                msgErr = "bom for product %r not present in odoo " % codice
                errors.append(msgErr)
                continue
            fornitore = data.get('fornitore', '')
            res_partner_id = res_partner_obj.search([('dia_ref_vendor', '=', fornitore)],
                                                    limit=1)
            if not res_partner_id:
                msgErr = "res partner %r not present in odoo " % fornitore
                errors.append(msgErr)
                continue
            s_codice = "S-" + codice
            service_product_product_id = product_product_obj.search([('default_code', '=', s_codice)],
                                                                    limit=1)
            if not service_product_product_id:
                uom_id = uom_ids.get(data.get('unita_misura', 'PZ'), 1)
                service_product_product_id = product_product_obj.create({'default_code': s_codice,
                                                                         'name': data.get('descrizione', ''),
                                                                         'type': 'service',
                                                                         'uom_id': uom_id,
                                                                         'uom_po_id': uom_id,
                                                                         'standard_price': data.get('costo', -1)})
            bom_id.external_product = service_product_product_id

            if not service_product_product_id.seller_ids:
                product_supplierinfo_obj.create({'name': res_partner_id.id,
                                                 'product_tmpl_id': service_product_product_id.product_tmpl_id.id,
                                                 'price': data.get('costo', 0.0)})
            else:
                found = False
                for supplierinfo_id in service_product_product_id.seller_ids:
                    if supplierinfo_id.name.id == res_partner_id.id and supplierinfo_id.product_tmpl_id.id == service_product_product_id.product_tmpl_id.id:
                        # and supplierinfo_id.price == data.get('costo', 0.0):
                        # Removed price because supplier is always created
                        found = True
                        break
                if not found:
                    product_supplierinfo_obj.create({'name': res_partner_id.id,
                                                     'product_tmpl_id': service_product_product_id.product_tmpl_id.id,
                                                     'price': data.get('costo', 0.0)})

        logging.info('Finished import suppliers for products')
        return errors

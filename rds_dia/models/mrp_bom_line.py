'''
Created on 29 May 2018

@author: mboscolo
'''
import logging
from odoo import api
from odoo import fields
from odoo import models
from odoo.exceptions import UserError
from gevent.corecext import child


class plm_relation_line(models.Model):
    _inherit = 'mrp.bom.line'
    dia_row_id = fields.Char('Dia Row Id')  # utile solo per la fase di import

    @api.model
    def fixUomId(self, values):
        out = []
        product_cache = {}
        product_product_obj = self.env['product.product']

        def getProductFromCode(default_code):
            product_product_id = product_cache.get(default_code, False)
            if not product_product_id:
                product_product_id = product_product_obj.search([('default_code', '=', default_code)])
            if not product_product_id:
                msg = "Product %r not found in the system" % default_code
                logging.error(msg)
                out.append(msg)
            product_cache[default_code] = product_product_id
            return product_product_id

        for parent, child, uom_id in values:
            parent_obj = getProductFromCode(parent)
            child_obj = getProductFromCode(child)
            if parent_obj:
                for bom_id in parent_obj.bom_ids:
                    bom_lines = self.search([('bom_id', '=', bom_id.id),
                                            ('product_id', '=', child_obj.id)])
                    if not bom_lines:
                        msg = "parent_obj %r child_obj %r " % (parent_obj.id, child_obj.id)
                        logging.error(msg)
                        out.append(msg)
                    for bom_line in bom_lines:
                        if bom_line.product_uom_id.id != uom_id:
                            bom_line.product_uom_id = uom_id
                            logging.info("FIXED --->>>>>>>>>>>>>")
        return out

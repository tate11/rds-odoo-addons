'''
Created on 20 Jul 2018

@author: mboscolo
'''
import logging
from odoo import _
from odoo import api
from odoo import models
from odoo import fields
from odoo.exceptions import UserError

MATEROZZA_DATA = [{'pano': '9050012', 'materozza': '9050107'},
                  {'pano': '050005', 'materozza': '9050105'},
                  {'pano': '9050002', 'materozza': '9050102'},
                  {'pano': '9050001', 'materozza': '9050101'},
                  {'pano': '9050015', 'materozza': '9050115'},
                  {'pano': '9050017', 'materozza': '9050117'},
                  {'pano': '9050006', 'materozza': '9050106'},
                  {'pano': '9050010', 'materozza': '9050108'},
                  {'pano': '9050018', 'materozza': '9050118'},
                  {'pano': '9050016', 'materozza': '9050116'},
                  {'pano': '9050014', 'materozza': '9050114'}]


def getPano(value):
    for dict_val in MATEROZZA_DATA:
        if dict_val.get('materozza') == value:
            return dict_val.get('pano')


def getMaterozza(value):
    for dict_val in MATEROZZA_DATA:
        if dict_val.get('pano') == value:
            return dict_val.get('materozza')

# '9050012'           Pani alluminio      L 91
# '9050107'           Matarozze alluminio         L 91
#
# '050005'           Pani alluminio     EN-AB-47100
# '9050105'          Matarozze alluminio     EN-AB-47100
#
# '9050014'           Pani alluminio     EN AB 44400
# '9050114'
#
# '9050002'           Pani alluminio          EN-AB-46000/46100
# '9050102'           Matarozze alluminio     EN-AB-46000/46100
#
#
# '9050001'           Pani alluminio             EN-AB-46100
# '9050101'           Matarozze alluminio        EN-AB-46100
#
# '9050015' Pani alluminio         A-380,0 - 46500
# '9050115' Matarozze alluminio    A-380,0 - 46500
#
# '9050017' Pani alluminio       83 MG
# '9050117' Matarozze alluminio  83 MG
#
# '9050006' Pani alluminio      EN-AB-44100
# '9050106' Matarozze alluminio EN-AB-44100
#
# '9050010'           Pani alluminio         EN-AB-44300
# '9050108'           Matarozze alluminio     EN-AB-44300
#
# '9050018'           Pani alluminio         EN-AB-43500
# '9050118'           Matarozze alluminio     EN-AB-43500


# sprue

class ProductMouldConfiguration(models.Model):
    _inherit = "omnia_mold.mold_configuration"

    @api.multi
    def createMaterozza(self):
        out = []
        product_product_obj = self.env['product.product']
        for mold_id in self.env['maintenance.equipment'].search([('is_mold', '=', True)]):
            to_perform = {}
            to_perform_uom = {}
            ref_prod = {}
            for index, mold_configuration in enumerate(mold_id.mold_configuration):
                logging.info("[ %r ] : Work on mold: %r" % (mold_id.name, mold_configuration.mold_id.name))
                product_id = mold_configuration.product_id
                for bom_id in product_id.bom_ids:
                    for bom_line in bom_id.bom_line_ids:
                        prod_name = bom_line.product_id.default_code
                        sprue_name = getMaterozza(prod_name)
                        if not sprue_name:
                            if prod_name[0] != '9':
                                continue
                            out.append("mold: %r unable to retrieve sprue from %r" % (mold_id.name, bom_line.product_id.default_code))
                            break
                        ref_prod[sprue_name] = bom_line.product_id.id
                        to_perform_uom[sprue_name] = bom_line.product_uom_id.id
                        if sprue_name in to_perform:
                            to_perform[sprue_name] += bom_line.product_qty
                        else:
                            to_perform[sprue_name] = bom_line.product_qty
            try:
                for sprue_name, qty in to_perform.items():
                    qty = qty * 0.1  # 10 %
                    sprue_id = product_product_obj.search([('default_code', '=', sprue_name)])
                    if sprue_id:
                        mold_id.product_sprue_id = sprue_id.id
                        mold_id.product_sprue_qty = qty
                        mold_id.product_sprue_uom = to_perform_uom[sprue_name]
                    else:
                        logging.error("Sprue not found %r" % sprue_name)
                        out.append(sprue_name)
                        continue
                    if to_perform.get(sprue_name, False):
                        mold_id.product_raw_sprue_id = ref_prod[sprue_name]
                        mold_id.product_raw_sprue_qty = qty
                        mold_id.product_raw_sprue_uom = to_perform_uom[sprue_name]
                    else:
                        logging.error("Raw material not found %r" % sprue_name)
                        out.append(sprue_name)
                        continue
            except Exception as ex:
                logging.error(ex)
                out.append(str(ex))
        return out

# -*- encoding: utf-8 -*-
'''
Created on 28 May 2018

@author: mboscolo
'''
import os
import logging
from datetime import datetime
from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo import tools
from io import BytesIO
from odoo.exceptions import UserError
from docutils.parsers.rst.directives import encoding


# TODO: METTERE A POSTO QUESTO PER IL DB DI PRODUZIONE IN CASO GLI ID SIANO DIFFERENTI
parent_partner_location_id = 2
parent_customer_location_id = 9


class stock_picking_custom(models.Model):
    _inherit = 'stock.location'
    dia_location = fields.Char(size=2,
                               string="Dia Location")

    @api.model
    def import_dia(self, items):
        """
        72,STOCCO & TOGNON,1 26021154
        72,STOCCO & TOGNON,1 26021154
        {'dia_ref': , 'ref_name':, 'customer_id':}
        """
        res_partner = self.env['res.partner']
        for item in items:
            create_vals = {'usage': 'internal'}
            create_vals['dia_location'] = item.get('dia_ref')
            create_vals['name'] = item.get('ref_name')
            dia_customer_ref = item.get('customer_id')
            for partner in res_partner.search([('dia_ref_vendor', '=', dia_customer_ref)]):
                create_vals['partner_id'] = partner.id
                break
            pass
            if create_vals.get('partner_id'):
                create_vals['location_id'] = parent_partner_location_id
            self.create(create_vals)
        return True

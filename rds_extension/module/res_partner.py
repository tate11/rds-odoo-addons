'''
Created on Aug 1, 2018

@author: daniel
'''

import logging
from odoo import api
from odoo import fields
from odoo import models
from odoo import _
from odoo.exceptions import UserError


class PartnerExtension(models.Model):
    _inherit = 'res.partner'

    effective_consumed_material = fields.Boolean('Mostra materiale effettivamente consumato nel DDT')

    @api.onchange('vat')
    def changeVatNumber(self):
        for partnerBrws in self:
            partnerBrws.checkFieldAlreadyExists('vat', partnerBrws.vat)
         
    @api.onchange('dia_ref_customer')
    def changeDiaRefCustomer(self):
        for partnerBrws in self:
            partnerBrws.checkFieldAlreadyExists('dia_ref_customer', partnerBrws.dia_ref_customer)
         
    @api.onchange('dia_ref_vendor')
    def changeDiaRefVendor(self):
        for partnerBrws in self:
            partnerBrws.checkFieldAlreadyExists('dia_ref_vendor', partnerBrws.dia_ref_vendor)

    @api.multi
    def checkFieldAlreadyExists(self, fieldName, fieldVal):
        if fieldVal and not self.company_type == 'person':
            partners = self.search([(fieldName, '=', fieldVal), ('company_type', '=', 'company')])
            if len(partners) >= 1:
                raise UserError('Esiste già un partner con il valore %r per il campo %r' % (fieldVal, fieldName))

    @api.multi
    def checkFields(self, vals):
        checkFields = ['vat', 'dia_ref_customer', 'dia_ref_vendor']
        for fieldName in checkFields:
            fieldVal = vals.get(fieldName, None)
            if fieldVal:    # If value is false I don't have to check
                self.checkFieldAlreadyExists(fieldName, fieldVal)
        
    @api.multi
    def write(self, vals):
        for partnerBrws in self:
            partnerBrws.checkFields(vals)
        return super(PartnerExtension, self).write(vals)
    
    @api.model
    def create(self, vals):
        if vals.get('company_type', '') == 'company':
            self.checkFields(vals)
        return super(PartnerExtension, self).create(vals)
    
    
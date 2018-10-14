'''
Created on 11 Jun 2018

@author: mboscolo
'''
import math
import logging
import datetime
from dateutil.relativedelta import relativedelta

from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo import tools
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class MrpProductionWizard(models.TransientModel):

    _inherit = "mrp.production.externally.wizard"

    def updatePickIN(self, values, partner_id, localStockLocation, customerProductionLocation):
        """
            this function can be overloaded in order to customize the
        """
        objCARL = self.env['dia.causale'].search([('name', '=', 'CARL')])
        values['causale_dia'] = objCARL.id  # CONTO LAVORO
        return values

    def updatePickOUT(self, values, partner_id, localStockLocation, customerProductionLocation):
        """
            this function can be overloaded in order to customize the
        """
        objCARL = self.env['dia.causale'].search([('name', '=', 'TRAS')])
        values['causale_dia'] = objCARL.id  # CONTO LAVORO
        return values

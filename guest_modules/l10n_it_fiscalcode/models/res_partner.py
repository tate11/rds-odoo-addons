# -*- coding: utf-8 -*-
# Copyright 2018 Teuron (<http://www.teuron.it>)

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

try:
    import codicefiscale
except ImportError:
    _logger.warning(
        'codicefiscale library not found. '
        'If you plan to use it, please install the codicefiscale library '
        'from https://pypi.python.org/pypi/codicefiscale')


class ResPartner(models.Model):
    _inherit = 'res.partner'

    fiscalcode = fields.Char(
        string='Fiscal Code', size=16, help="Italian Fiscal Code")
    individual = fields.Boolean(
        string='Individual', default=False,
        help="If checked the C.F. is referred to a Individual Person")

    @api.multi
    @api.constrains('fiscalcode')
    def _check_fiscalcode(self):

        for partner in self:
            if partner.commercial_partner_id:
                continue
            if partner.fiscalcode:
                if partner.is_company and not partner.individual:
                    error = False
                    if partner.vat and partner.vat[:2].lower() == 'it':
                        if not partner.fiscalcode.isdigit() or len(partner.fiscalcode) > 11:
                            error = True
                    elif not partner.fiscalcode.isdigit():
                        error = True
                    if error:
                        raise ValidationError(
                            _("Only digits are allowed in company fiscalcode")
                        )
                else:
                    if len(partner.fiscalcode) != 16 \
                            and not codicefiscale.isvalid(partner.fiscalcode):
                        raise ValidationError(
                            _("The fiscal code doesn't seem to be correct.")
                        )
    @api.model
    def _commercial_fields(self):
        """ Returns the list of fields that are managed by the commercial entity
        to which a partner belongs. These fields are meant to be hidden on
        partners that aren't `commercial entities` themselves, and will be
        delegated to the parent `commercial entity`. The list is meant to be
        extended by inheriting classes. """
        return super(ResPartner,self)._commercial_fields() + ['fiscalcode']
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.osv import expression

import xml.etree.ElementTree as ET
from lxml import etree
import lxml.html

import base64
import logging

class OrgChartPrinter(models.TransientModel):
    _name = 'orgchart.printer'

    product_tmpl_id = fields.Many2one('product.template')

    def print_org_chart(self):
        return self.env.ref('rds_hr.rds_employee_print_org_chart').report_action(self)
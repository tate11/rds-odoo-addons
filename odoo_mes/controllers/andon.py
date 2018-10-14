# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.addons.portal.controllers.portal import _build_url_w_params
from odoo.http import request, route

import json

class Andon(http.Controller):

    @http.route('/andon', type='http', auth='public', website=True)
    def andon_dashboard(self):
        response = dict()
        response['workcenters'] = request.env['mrp.workcenter'].sudo().search([])

        return http.request.render("odoo_mes.home", response)
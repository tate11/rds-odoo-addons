# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.addons.portal.controllers.portal import _build_url_w_params
from odoo.http import request, route
from odoo.tools.mimetypes import guess_mimetype

import base64, json, logging

class KioskController(http.Controller):

    @http.route('/hr/kiosk/deferred_login', type='http', auth='public')
    def deferred_login(self, tmbs):
        result = []
        tmbs = tmbs.split('*')
        for i in tmbs:
            if i:
                vals = i.split('@')
                try:
                    result += request.env['hr.employee'].sudo().rds_attendance_scan(vals[1], vals[0], request.httprequest.environ['REMOTE_ADDR'])
                except Exception:
                    continue

        return 'OK'

    @http.route('/hr/kiosk/login', type='http', auth='public')
    def try_login(self, barcode, time):
        result = request.env['hr.employee'].sudo().rds_attendance_scan(barcode, time, request.httprequest.environ['REMOTE_ADDR'])

        return json.dumps(result)

    @http.route('/hr/kiosk', type='http', auth='public', website=True)
    def show_kiosk(self):
        return http.request.render('rds_hr_attendance.index')

    @http.route('/hr/portrait', type='http', auth='public', website=True)
    def employee_portrait(self, uid=0):
        employee = request.env['hr.employee'].sudo().browse(int(uid))
        image = employee['image']
        mimetype = guess_mimetype(base64.b64decode(image), default='image/png')
        headers = [('Content-Type', mimetype), ('X-Content-Type-Options', 'nosniff')]
        
        content_base64 = base64.b64decode(image)
        headers.append(('Content-Length', len(content_base64)))
        response = request.make_response(content_base64, headers)

        return response

    @http.route('/service/ping', type='http', auth='public', website=True)
    def service_ping(self, uid=0):
        return 'true'
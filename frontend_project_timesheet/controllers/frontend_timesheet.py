# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.addons.portal.controllers.portal import _build_url_w_params
from odoo.http import request, route

import json
class FrontendTimesheet(http.Controller):
    
    @http.route('/fetimesheets/', type='http', auth='public', website=True)
    def frontend_timesheet_login(self):
        values = dict()

        return http.request.render("frontend_project_timesheet.login", values)

    @http.route('/fetimesheets/login', type='http', auth='public')
    def frontend_try_login(self, barcode):
        result = dict()

        try:
            emp = request.env['hr.employee'].sudo().search([('barcode', '=', barcode)], limit=1)

            if emp:
                result['type'] = 'success'
                result['employee'] = emp.ids[0]
                result['message'] = 'Welcome {}! Logging you in...'.format(emp[0].name)
            else:
                result['type'] = 'warning'
                result['employee'] = None
                result['message'] = 'No matching employee. Try again or contact HR office.'
        except Exception as e:
                result['type'] = 'danger'
                result['employee'] = None
                result['message'] = str(e)

        return json.dumps(result)

    @http.route('/fetimesheets/home', type='http', auth='public', website=True)
    def frontend_timesheet(self, eid):
        page = dict()
        eid = int(eid)
        KANBANSTATES = {'normal': 0, 'blocked': 1}
        page['employee'] = request.env['hr.employee'].sudo().browse(eid)
        page['tasks'] = request.env['project.task'].sudo().with_context(tz="Europe/Rome", lang="it_IT")\
                        .search([('employee_id', '=', eid), ('kanban_state', '!=', 'done')])\
                        .sorted(lambda x: (KANBANSTATES[x.kanban_state], bool(x.date_deadline), x.date_deadline))

        return http.request.render("frontend_project_timesheet.home", page)


    @http.route('/fetimesheets/start', type='http', auth='public', website=True)
    def start_work(self, task_id):
        result = dict()

        try:
            result = request.env['project.task'].sudo().browse(int(task_id)).start_work()
        except Exception as e:
            result['type'] = 'error'
            result['message'] = str(e)

        return json.dumps(result)

    @http.route('/fetimesheets/block', type='http', auth='public', website=True)
    def block_task(self, task_id):
        result = dict()

        try:
            result = request.env['project.task'].sudo().browse(int(task_id)).block()
        except Exception as e:
            result['type'] = 'error'
            result['message'] = str(e)

        return json.dumps(result)

    @http.route('/fetimesheets/done', type='http', auth='public', website=True)
    def done(self, task_id):
        result = dict()

        try:
            result = request.env['project.task'].sudo().browse(int(task_id)).done()
        except Exception as e:
            result['type'] = 'error'
            result['message'] = str(e)

        return json.dumps(result)
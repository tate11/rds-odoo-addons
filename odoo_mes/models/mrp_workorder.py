'''
Created on 3 Aug 2018

@author: mboscolo
'''


import datetime
from odoo import api
from odoo import fields
from odoo import models
from odoo import _
from odoo.tools import float_compare, float_round
from odoo.exceptions import UserError
import logging
from dateutil.relativedelta import relativedelta

datetime = fields.Datetime

class MrpWorkOrder(models.Model):
    _inherit = 'mrp.workorder'

    auto_tracking = fields.Boolean("Allow Manual Timetracking", related="workcenter_id.auto_tracking")

    @api.multi
    def advance(self):
        for wko in self:
            wko.qty_producing += 1
            wko.record_production()

    @api.multi
    def button_start(self):
        self.ensure_one()
        # As button_start is automatically called in the new view
        if self.state in ('done', 'cancel'):
            return True

        # Need a loss in case of the real time exceeding the expected
        timeline = self.env['mrp.workcenter.productivity']
        if self.duration < self.duration_expected:
            loss_id = self.env['mrp.workcenter.productivity.loss'].search([('loss_type','=','productive')], limit=1)
            if not len(loss_id):
                raise UserError(_("You need to define at least one productivity loss in the category 'Productivity'. Create one from the Manufacturing app, menu: Configuration / Productivity Losses."))
        else:
            loss_id = self.env['mrp.workcenter.productivity.loss'].search([('loss_type','=','performance')], limit=1)
            if not len(loss_id):
                raise UserError(_("You need to define at least one productivity loss in the category 'Performance'. Create one from the Manufacturing app, menu: Configuration / Productivity Losses."))
        for workorder in self:
            if workorder.production_id.state != 'progress':
                workorder.production_id.write({
                    'state': 'progress',
                    'date_start': datetime.now(),
                })
            if workorder.auto_tracking:
                timeline.create({
                    'workorder_id': workorder.id,
                    'workcenter_id': workorder.workcenter_id.id,
                    'description': _('Time Tracking: ')+self.env.user.name,
                    'loss_id': loss_id[0].id,
                    'date_start': datetime.now(),
                    'user_id': self.env.user.id
                })
        return self.write({'state': 'progress',
                    'date_start': datetime.now(),
        })

    @api.multi
    def end_previous(self, doall=False):
        if self.auto_tracking:
            return super(MrpWorkOrder, self).end_previous(doall)
        else:
            return True
# -*- coding: utf-8 -*-
# This file and any file found in child directories are part of RDS Moulding Technology SpA Addons for Odoo. 
# See LICENSE file in the parent folder for full copyright and licensing details.

from odoo import api, fields, models, _

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    project_id = fields.Many2one('project.project', string='Analytic Account')

class Maintenance(models.Model):
    _inherit = 'maintenance.request'

    task_id = fields.Many2one('project.task', string='Task')
    description = fields.Html(string='Description')
    project_id = fields.Many2one('project.project', related="equipment_id.project_id", readonly=True, string='Analytic Account')

    def action_create_task(self):
        self.task_id = self.env['project.task'].create({'name': self.name, 'description': self.description, 
                                         'date_deadline': self.schedule_date, 'planned_hours': self.duration,
                                         'project_id': self.project_id.id})

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    project_id = fields.Many2one('project.project', string='Analytic Account', help="If set, overrides the machine's analytic account.")
    task_id = fields.Many2one('project.task', string='Task')
    tag_ids = fields.Many2many('account.analytic.tag', 'mrp_production_line_tag_rel', 'line_id', 'tag_id', string='Tags', copy=True)

    def _prepare_wc_analytic_line(self, wc_line):
        wc = wc_line.workcenter_id
        hours = wc_line.duration / 60.0
        value = hours * wc.costs_hour
        account = (self.project_id and self.project_id.id) or wc.costs_hour_account_id.id
        return {
            'name': wc_line.name + ' (H)',
            'amount': -value,
            'account_id': account,
            'tags_ids': [(4, x) for x in self.workcenter_id.analytic_tags_ids.ids] + [(4, x) for x in self.analytic_tags_ids.ids],
            'task_id': self.task_id.id,
            'ref': wc.code,
            'unit_amount': hours,
        }

    def _costs_generate(self):
        """ Calculates total costs at the end of the production.
        :param production: Id of production order.
        :return: Calculated amount.
        """
        self.ensure_one()
        AccountAnalyticLine = self.env['account.analytic.line']
        amount = 0.0
        for wc_line in self.workorder_ids:
            wc = wc_line.workcenter_id
            if wc.costs_hour_account_id:
                # Cost per hour
                hours = wc_line.duration / 60.0
                value = hours * wc.costs_hour
                if value:
                    amount -= value
                    # we user SUPERUSER_ID as we do not guarantee an mrp user
                    # has access to account analytic lines but still should be
                    # able to produce orders
                    AccountAnalyticLine.sudo().create(self._prepare_wc_analytic_line(wc_line))
        return amount


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    tag_ids = fields.Many2many('account.analytic.tag', 'mrp_workcenter_tag_rel', 'line_id', 'tag_id', string='Tags', copy=True)
'''
Created on 29 Mar 2018

@author: mboscolo
'''
import math
import logging
from dateutil.relativedelta import relativedelta

from odoo import models
from odoo import fields
from odoo import api
from odoo import _
from odoo import osv
from odoo import tools
from odoo.exceptions import UserError


class merge_manufactoring(models.TransientModel):
    _name = 'merge_mold_production'
    manufactory_ids = fields.Many2many('mrp.production',
                                       string='Orders')
    mold_id = fields.Many2one('maintenance.equipment',
                              string='Mold')
    mold_routing_id = fields.Many2one('mrp.routing',
                                      string="Mold Routing",)
    check_result = fields.Html("Mold check result ")
    number_of_shut = fields.Integer("Number of Shuts")
    product_id = fields.Many2one("product.product",
                                 "Product to use")
    location_src_id = fields.Many2one("stock.location",
                                      "Raw location")

    @api.model
    def getActionMergeWizard(self, production_ids):
        """
        get default action wizard
        """
        vals = {}
        for production_id in self.env['mrp.production'].browse(production_ids):
            vals['location_src_id'] = production_id.location_src_id.id
            vals['mold_id'] = production_id.mold_id.id
            vals['manufactory_ids'] = [(6, 0, production_ids)]
            vals['product_id'] = production_id.product_id.id
            vals['mold_routing_id'] = production_id.routing_id.id
            break
        if not vals.get('mold_id'):
            for mold in self.env['omnia_mold.mold_configuration'].search([('product_id', '=', self.product_id.id)]):
                vals['mold_id'] = mold.mold_id.id
                break
        newObj = self.create(vals)
        action = {'name': 'Merge Production',
                  'view_type': 'form',
                  'view_mode': 'form',
                  'target': 'new',
                  'res_id': newObj.id,
                  'res_model': 'merge_mold_production',
                  'type': 'ir.actions.act_window'}
        return action

    @api.multi
    def action_merge(self):
        new_ref = ""
        temp_bom_id = False
        toCancel = []
        for order in self.manufactory_ids:
            new_ref = new_ref + "%r-%r " % (order.name, order.origin)
            logging.debug("Create new order as %r" % new_ref)
            if order.product_id.id == self.product_id.id:
                temp_bom_id = order.bom_id.id
            else:
                raise UserWarning("Unable to merge manufacture order %r" % order.name)
            toCancel.append(order)

        creation_vals = {'origin': new_ref,
                         'mold_id': self.mold_id.id,
                         'bom_id': temp_bom_id,
                         'routing_id': self.mold_routing_id.id,
                         'mold_routing_id': self.mold_routing_id.id,
                         'product_uom_id': self.product_id.uom_id.id,
                         'product_id': self.product_id.id,
                         'product_qty': self.number_of_shut,
                         'location_src_id': self.location_src_id.id}
        newMo = self.env['mrp.production'].create(creation_vals)

        for move in newMo.move_raw_ids + newMo.move_finished_ids:
            move._action_cancel()
            move.unlink()

        productionRawMove = {}
        newLineOut = {}
        for order in toCancel:
            for move in order.move_raw_ids:
                product_move_id = move.product_id.id
                if move.product_id.id not in productionRawMove:
                    newMove = move.copy({'raw_material_production_id': newMo.id})
                    productionRawMove[product_move_id] = newMove
                else:
                    productionRawMove[product_move_id].product_uom_qty = productionRawMove[product_move_id].product_uom_qty + move.product_uom_qty

            for move in order.move_finished_ids:
                product_move_id = move.product_id.id
                if move.product_id.id not in newLineOut:
                    newMove = move.copy({'production_id': newMo.id})
                    newLineOut[product_move_id] = newMove
                else:
                    newLineOut[product_move_id].product_uom_qty = newLineOut[product_move_id].product_uom_qty + move.product_uom_qty
            order.action_cancel()
        if newMo.id:
            action = {'name': 'Production Order',
                      'view_type': 'form',
                      'view_mode': 'form',
                      'res_id': newMo.id,
                      'res_model': 'mrp.production',
                      'type': 'ir.actions.act_window'}
            return action

    @api.multi
    def action_compute(self):
        def getAllMold(order, product_id):
            out = "<table>"
            mold_done = []
            for src_configurations in self.env['omnia_mold.mold_configuration'].search([('product_id', '=', product_id.id)]):
                mold_id = src_configurations.mold_id
                if mold_id not in mold_done:
                    for configuration in mold_id.mold_configuration:
                        mold_name = configuration.mold_id.name
                        qty = order.product_qty
                        product_name = configuration.product_id.display_name
                        out = out + """<tr><td>Mold: %r Product %r Qty %r</td></tr>""" % (mold_name, qty, product_name)
                    mold_done.append(mold_id)
            return out + "</table>"
        msg = ""
        for order in self.manufactory_ids:
            product_id = order.product_id
            msg = msg + "<div> Manufactory Order: %r" % order.name
            msg = msg + getAllMold(order, product_id)
            msg = msg + "</div>"
        self.check_result = msg
        return {'name': _('Merge Tool'),
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'merge_mold_production',
                'target': 'new',
                'res_id': self.ids[0],
                'type': 'ir.actions.act_window',
                'domain': "[]"}

    @api.model
    def default_get(self, fields):
        """ To get default values for the object.
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param fields: List of fields for which we want default values
        @param context: A standard dictionary
        @return: A dictionary which of fields with values.
        """
        res = {}
        record_ids = self.env.context.get('active_ids')
        res['manufactory_ids'] = record_ids
        return res

    @api.multi
    def act_merge_bom(self):
        """
            Create and populate the merge bom tool
        """

        ids = self.ids
        if len(ids) < 1:
            return False

        return {'name': _('Merge Tool'),
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'merge_mold_production',
                'target': 'new',
                'res_id': self.ids[0],
                'type': 'ir.actions.act_window',
                'domain': "[]"}


class RdsWorkOrerReplan(osv.osv.osv_memory):
    _name = "workorder_replan"
    _table = "workorder_replan"

    from_date_plan = fields.Datetime(string=_("From date"))
    work_order_ids = fields.Many2many('mrp.workorder', string=_('work Order to plan'))

    @api.model
    def action_replan_workorder(self):
        WorkOrder = self.env['mrp.workorder']
        self.workorder_ids.write({'date_planned_start': False, 'date_planned_finished': False})
        start_date = self.from_date_plan
        from_date_set = False
        for workOrder_id in self.work_order_ids:
            workcenter = workOrder_id.workcenter_id
            wos = WorkOrder.search([('workcenter_id', '=', workcenter.id), ('date_planned_finished', '<>', False),
                                    ('state', 'in', ('ready', 'pending', 'progress')),
                                    ('date_planned_finished', '>=', start_date.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT))], order='date_planned_start')
            from_date = start_date
            intervals = workcenter.resource_calendar_id.attendance_ids and workcenter.resource_calendar_id._schedule_hours(workOrder_id.duration_expected / 60.0, from_date)
            if intervals:
                to_date = intervals[-1][1]
                if not from_date_set:
                    from_date = intervals[0][0]
                    from_date_set = True
            else:
                to_date = from_date + relativedelta(minutes=workOrder_id.duration_expected)
            # Check interval
            for wo in wos:
                if from_date < fields.Datetime.from_string(wo.date_planned_finished) and (to_date > fields.Datetime.from_string(wo.date_planned_start)):
                    from_date = fields.Datetime.from_string(wo.date_planned_finished)
                    to_date = workcenter.resource_calendar_id.attendance_ids and workcenter.resource_calendar_id.plan_hours(workOrder_id.duration_expected / 60.0, from_date)
                    if not to_date:
                        to_date = from_date + relativedelta(minutes=workOrder_id.duration_expected)
            workOrder_id.write({'date_planned_start': from_date, 'date_planned_finished': to_date})

            if (workOrder_id.operation_id.batch == 'no') or (workOrder_id.operation_id.batch_size >= workOrder_id.qty_production):
                start_date = to_date
            else:
                qty = min(workOrder_id.operation_id.batch_size, workOrder_id.qty_production)
                cycle_number = math.ceil(qty / workOrder_id.production_id.product_qty / workcenter.capacity)
                duration = workcenter.time_start + cycle_number * workOrder_id.operation_id.time_cycle * 100.0 / workcenter.time_efficiency
                to_date = workcenter.resource_calendar_id.attendance_ids and workcenter.resource_calendar_id.plan_hours(duration / 60.0, from_date)
                if not to_date:
                    start_date = from_date + relativedelta(minutes=duration)


class PostQtyLine(osv.osv.osv_memory):
    _name = "mold_post_qty_line"
    product_id = fields.Many2one("product.product",
                                 "Product")
    qty = fields.Integer("Quantity")
    move_orign_qty = fields.Integer("Quantity")
    # origin_move_id = fields.Integer('Move Id')
    # move_id = fields.Many2one('stock.move')
    mold_post_qty_id = fields.Many2one('mold_post_qty')


class PostQty(osv.osv.osv_memory):
    _name = "mold_post_qty"
    production_id = fields.Many2one("mrp.production",
                                    "Product")

    lines = fields.One2many('mold_post_qty_line', 'mold_post_qty_id')
    create_report = fields.Boolean('Create Report', default=False)
    post_move = fields.Boolean('Post Move', default=True)

    @api.model
    def populate(self, items):
        for product_id, qty in items:
            self.lines = [(0, 0, {'product_id': product_id,
                                  'qty': qty})]

    def summrizeLines(self):
        linesProdRel = {}
        for line in self.lines:
            if line.product_id not in linesProdRel:
                linesProdRel[line.product_id] = line
            else:
                linesProdRel[line.product_id].qty += line.qty
                line.unlink()

    def checkQty(self):
        linesProdRel = {}
        for finishedMove in self.production_id.move_finished_ids.filtered(lambda x: x.state not in ('done', 'cancel')):
            if finishedMove.product_id not in linesProdRel:
                linesProdRel[finishedMove.product_id] = finishedMove.quantity_done
            else:
                linesProdRel[finishedMove.product_id] += finishedMove.quantity_done
        for lineBrws in self.lines:
            if lineBrws.product_id in linesProdRel.keys():
                if lineBrws.qty > linesProdRel[lineBrws.product_id]:
                    raise UserError(_("L'ordine di produzione prevedeva per il prodotto %r un massimo di %s, mentre si sta cercando di valorizzare una quantità maggiore (%s)." % (lineBrws.product_id.display_name, linesProdRel[lineBrws.product_id], lineBrws.qty)))

    @api.multi
    def post_report(self):
        if self.lines:
            return self.env['ir.actions.report']._get_report_from_name('omnia_mold.mrp_production_lables').report_action(self.lines, config=False)

    def post_and_report(self):
        self.create_report = True
        return self.post()
        
    def post(self):
        if self.post_move:
            self.summrizeLines()
            self.checkQty()
            for line in self.lines:
                self.production_id.post_inventory_product(line.product_id, line.qty)
        if self.create_report:
            return self.env['ir.actions.report']._get_report_from_name('omnia_mold.mrp_production_lables').report_action(self.lines, config=False)

    @api.model
    def getActionPostWizardWk(self, workorder_ids):
        for workorder_id in self.env['mrp.workorder'].browse(workorder_ids):
            return self._getActionPostWizard(workorder_id.production_id)

    @api.model
    def getActionPostWizard(self, production_ids):
        """
        get default action wizard
        """
        for production_id in self.env['mrp.production'].browse(production_ids):
            return self._getActionPostWizard(production_id)

    @api.model
    def _getActionPostWizard(self, production_id):
        """
        get default action wizard
        """
        linesProdRel = {}
        objNew = self.create({'production_id': production_id.id})
        for move in production_id.move_finished_ids:
            if move.state not in ['done', 'cancelled']:
                qty = move.quantity_done
                if qty > 0:
                    if move.product_id not in linesProdRel:
                        linesProdRel[move.product_id] = {
                            'product_id': move.product_id.id,
                            'qty': qty,}
                    else:
                        linesProdRel[move.product_id]['qty'] += qty
                        
        for vals in linesProdRel.values():
            objNew.lines = [(0, 0, vals)]
        action = {'name': 'Post Production',
                  'view_type': 'form',
                  'view_mode': 'form',
                  'target': 'new',
                  'res_id': objNew.id,
                  'res_model': 'mold_post_qty',
                  'type': 'ir.actions.act_window'}
        return action

'''
Created on 6 Mar 2018

@author: mboscolo
'''
from odoo import tools, _
from odoo import api
from odoo import models
from odoo import fields
from odoo.exceptions import UserError
import logging

class ProductMouldConfiguration(models.Model):
    _name = "omnia_mold.mold_configuration"

    name = fields.Char('Name',
                       size=64)
    exclude = fields.Boolean(_("Exclude"))
    product_id = fields.Many2one('product.product',
                                 string=_('Reference Product'))
    description = fields.Char(_("Notes"))
    product_uom = fields.Char(related='product_id.uom_id.name',
                              string=_("UOM"),
                              readonly=True)

    mold_id = fields.Many2one('maintenance.equipment',
                              string=_('Mold'))

    def _generate_finished_moves(self, production_id):
        move = self.env['stock.move'].create({
            'name': production_id.name,
            'date': production_id.date_planned_start,
            'date_expected': production_id.date_planned_start,
            'product_id': self.product_id.id,
            'product_uom': self.product_id.uom_id.id,
            'product_uom_qty': production_id.getNImpronte(self.product_id) * production_id.product_qty,
            'location_id': production_id.product_id.property_stock_production.id,
            'location_dest_id': production_id.location_dest_id.id,
            'company_id': production_id.company_id.id,
            'production_id': production_id.id,
            'origin': production_id.name,
            'group_id': production_id.procurement_group_id.id,
            'propagate': production_id.propagate,
            'move_dest_ids': [(4, x.id) for x in production_id.move_dest_ids],
        })
        move._action_confirm()
        return move


class TrackedProduct(models.Model):
    _name = "omnia_mold.mold_tracked"
    exclude = fields.Boolean("Escludi")
    product_id = fields.Many2one('product.product',
                                 string='Prodotto di Riferimento',
                                 required=True)
    lot_id = fields.Many2one('stock.production.lot',
                             string='Serial Number')

    actual_shot = fields.Integer(related='lot_id.n_shots')
    actual_shot_guarantee = fields.Integer(related='lot_id.n_shots_guarantee')

    @api.model
    def guaranteeExpired(self):
        return self.lot_id.no_more_guarantee

    @api.multi
    def register_shot(self):
        for omnia_mold_mold_tracked in self:
            omnia_mold_mold_tracked.lot_id.register_shot()

# aggiungere wf
# bozza confermato (amministratore puo tornare indietro)


MOLD_STATE = [('draft', _('Draft')),
              ('confirmed', _('Confirmed')),
              ('suspended', _('Suspended'))]

USEDIC_MOLD_STATE = dict(MOLD_STATE)


class ToolKitLine(models.Model):
    _name = "omnia_mold.toolkit_line"

    equipment_id = fields.Many2one('maintenance.equipment',
                                   required=True,
                                   string='Attrezzatura di Riferimento',
                                   ondelete='cascade')

    kit_equimpent_id = fields.Many2one('maintenance.equipment',
                                       string="Attrezzatura",
                                       ondelete='cascade',
                                       required=True,)

    workcenter_id = fields.Many2one('mrp.workcenter',
                                    string='Centro di Lavoro', ondelete='cascade')

    def is_mo_tooled(self, mo, mode="text"):
        if self.kit_equimpent_id in self.workcenter_id.equipment_ids:
            if mode == "bit":
                return "1"
            return "INSTALLATO"
        else:
            if mode == "bit":
                return "0"
            return "DA INSTALLARE"


class Mold(models.Model):
    _name = "maintenance.equipment"
    _inherit = 'maintenance.equipment'

    is_mold = fields.Boolean('Attrezzatura di Produzione')

    owner_partner_id = fields.Many2one('res.partner', 'Propietario', oldname="owner_partner")
    
    warranty_type = fields.Selection([
                                        ('none', 'Nessuna'),
                                        ('date', 'Data'),
                                        ('component', 'Su componente'),
                                        ('process', 'N. di Processi')
                                      ], 'Tipo di Garanzia', default="none", required=True)

    warranted_processes = fields.Integer('Numero di Processi Garantiti')
    sustained_processes = fields.Integer('Numero di Processi Subiti', readonly=True)

    toolkit_lines = fields.One2many('omnia_mold.toolkit_line',
                                    string='Attrezzatura di Corredo', inverse_name="equipment_id")

    bom_id = fields.Many2one('mrp.bom',
                             string='Distinta Tecnica Attrezzatura')


    mold_configuration = fields.One2many('omnia_mold.mold_configuration',
                                         'mold_id',
                                         string="Impronte")
    mold_tracking = fields.Many2many('omnia_mold.mold_tracked',
                                     string='Prodotti soggetti a usura')
    state = fields.Selection(MOLD_STATE,
                             string=_('Condizione'),
                             default='draft')

    routings_ids = fields.Many2many('mrp.routing',
                                    string="Routings")

    product_sprue_id = fields.Many2one('product.product',
                                       string=_('Sprue Product'))
    product_sprue_qty = fields.Float("Qty of Sprue")
    product_sprue_uom = fields.Many2one('product.uom', 'Reference Unit of Measure')
    product_raw_sprue_id = fields.Many2one('product.product',
                                           string=_('Raw Sprue Product'))
    product_raw_sprue_qty = fields.Float("Qty of Sprue")

    product_raw_sprue_uom = fields.Many2one('product.uom', 'Reference Unit of Measure')

    image = fields.Binary(
        "Photo", attachment=True,
        help="This field holds the image used as photo for the tool, limited to 1024x1024px.")
    image_medium = fields.Binary(
        "Medium-sized photo", attachment=True,
        help="Medium-sized photo of the employee. It is automatically "
             "resized as a 128x128px image, with aspect ratio preserved. "
             "Use this field in form views or some kanban views.")
    image_small = fields.Binary(
        "Small-sized photo", attachment=True,
        help="Small-sized photo of the employee. It is automatically "
             "resized as a 64x64px image, with aspect ratio preserved. "
             "Use this field anywhere a small image is required.")

    @api.multi
    def _get_products(self):
        for i in self:
            i.product_ids = i.mold_configuration.mapped(lambda x: x.product_id)

    product_ids = fields.One2many('product.product', string=_('Products'), compute="_get_products")

    @api.one
    def fixMoldConsume(self):
        uom_id = self.env['product.uom'].search([('name', '=', 'PZ')])
        product_product_obj = self.env['product.product']
        mold_product_id = product_product_obj.search([('default_code', '=', self.name)])
        if not mold_product_id:
            moldProductVals = {'name': 'Stampo',
                               'default_code': self.name,
                               'uom_id': uom_id.id,
                               'uom_po_id': uom_id.id,
                               }
            mold_product_id = product_product_obj.create(moldProductVals)
        c_name = "C-" + self.name
        consume_product_id = product_product_obj.search([('default_code', '=', c_name)])
        if not consume_product_id:
            consumeProductVals = {'name': 'Consumo',
                                  'default_code': c_name,
                                  'uom_id': uom_id.id,
                                  'uom_po_id': uom_id.id,
                                  'tracking': 'serial'}
            consume_product_id = product_product_obj.create(consumeProductVals)
        product_tmpl_id = mold_product_id.product_tmpl_id.id
        bom_id = self.env['mrp.bom'].search([('product_tmpl_id', '=', product_tmpl_id)])
        if not bom_id:
            bom_id_vals = {'product_tmpl_id': product_tmpl_id,
                           'type': 'normal',
                           'state': 'draft',
                           'product_uom_id': uom_id.id}
            bom_id = self.env['mrp.bom'].create(bom_id_vals)
            bom_line_vals = {'bom_id': bom_id.id,
                             'product_id': consume_product_id.id,
                             'type': 'normal',
                             'product_qty': 1}
            self.env['mrp.bom.line'].create(bom_line_vals)
            self.bom_id = bom_id.id
            self.extractBittedObject()

    @api.model
    def fixMoldConsumes(self):
        for idToFix in self.search([]):
            idToFix.fixMoldConsume()
        return True

    @api.multi
    def _warranty_expired(self):
        for i in self:
            if i.warranty_type == 'none':
                i.warranty_type = False
            elif i.warranty_type == 'date':
                i.warranty_type = False if i.warranty >= fields.datetime.today() else True
            elif i.warranty_type == 'process':
                i.warranty_type = False if i.warranted_processes <= i.sustained_processes else True
            elif i.warranty_type == 'component':
                i.warranty_type = False
                for track in i.mold_tracking:
                    if track.guaranteeExpired():
                        i.warranty_type = True
    warranty_expired = fields.Boolean(compute=_warranty_expired,
                                      string=_("Warranty Expired"))

    @property
    @api.multi
    def getMoldProdIds(self):
        outIds = []
        for configBrws in self.mold_configuration:
            outIds.append(configBrws.product_id.id)
        return outIds

    @api.one
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        res = super(Mold, self).copy(default)
        res.analitic_id = False
        return res

    @api.multi
    def toConfirm(self):
        self.moveState('confirm')

    @api.multi
    def toDraft(self):
        self.moveState('draft')

    @api.multi
    def toSuspended(self):
        self.moveState('suspended')

    @api.multi
    def moveState(self, toState):
        if toState in USEDIC_MOLD_STATE:
            for obj in self:
                obj.state = toState
        else:
            raise UserError(_("State not allowed %r " % (self.toState)))

    @api.model
    def create(self, vals):
        if not self.project_id:
            accountObject = self.env['project.project'].create({'name': vals.get('name')})
            vals['project_id'] = accountObject.id
        tools.image_resize_images(vals)
        return super(Mold, self).create(vals)

    @api.multi
    def write(self, vals):
        tools.image_resize_images(vals)
        return super(Mold, self).write(vals)

    def trackedItems(self, parentBom):
        """
        Get all the product in the bom that are traked
        :return: All the product ids
        """
        out_product = []
        for bomLine in parentBom.bom_line_ids:
            if bomLine.product_id.tracking == 'serial':
                out_product.append(bomLine.product_id.id)
            for child_bom in bomLine.child_bom_id:
                out_product = out_product + self.trackedItems(child_bom)
        return out_product

    @api.multi
    def extractBittedObject(self):
        for item in self:
            trackedItems = self.trackedItems(item.bom_id)
            already_tracked = []
            for tracked in self.mold_tracking:
                product_id = tracked.product_id.id
                if product_id in trackedItems:
                    already_tracked.append(product_id)
            trackedToWrite = []
            for product_id in trackedItems:
                if product_id not in already_tracked:
                    trackedToWrite.append(self.env['omnia_mold.mold_tracked'].create({'product_id': product_id}))
            for wId in trackedToWrite:
                self.mold_tracking = [(4, wId.id)]

    @api.model
    def have_cavity_closed(self):
        for moldConfiguration in self.mold_configuration:
            if moldConfiguration.exclude:
                return True
        return False

    @api.model
    def have_active_maintenance(self):
        for request in self.maintenance_ids:
            if not request.stage_id.done:
                return True
        return False

    def _generate_sprue_finished_moves(self, production_id):
        if not self.product_sprue_id:
            return
            #raise UserError("Missing Sprue Product for mold %r" % production_id.mold_id.name)
        move = self.env['stock.move'].create({
            'name': production_id.name,
            'date': production_id.date_planned_start,
            'date_expected': production_id.date_planned_start,
            'product_id': self.product_sprue_id.id,
            'product_uom': self.product_sprue_uom.id,
            'product_uom_qty': self.product_sprue_qty * production_id.product_qty,
            'location_id': production_id.product_id.property_stock_production.id,
            'location_dest_id': production_id.location_dest_id.id,
            'company_id': production_id.company_id.id,
            'production_id': production_id.id,
            'origin': production_id.name,
            'group_id': production_id.procurement_group_id.id,
            'propagate': production_id.propagate,
            'move_dest_ids': [(4, x.id) for x in production_id.move_dest_ids],
            'is_materozza': True,
            'unit_factor': self.product_sprue_qty,
        })
        move._action_confirm()
        return move

    @api.multi
    def register_shot(self):
        for maintenance_equipment_id in self:
            maintenance_equipment_id.mold_tracking.register_shot()
            maintenance_equipment_id.sustained_processes += 1

    @api.multi
    def fix_process_time(self, domain=[]):
        all_molds = self.search(domain)

        ids = []
        for mold in all_molds:
            if not mold.mold_configuration:
                continue
                
            n_items = len(mold.mold_configuration)
            

            for rt in mold.routings_ids:
                for op in rt.operation_ids:
                    if op.id in ids:
                        continue
                    else:
                        ids.append(op.id)

                    if op.name == "ALPREP":
                        op.user_time_percentage = 1

                    elif op.name == "ALAUT":
                        op.time_cycle_manual = op.time_cycle_manual*(0.6)*n_items
                        op.time_cycle = op.time_cycle_manual
                        op.user_time_percentage = 0.33

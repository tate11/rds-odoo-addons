from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class StockPickingGoodsDescription(models.Model):
    _name = 'stock.picking.goods_description'
    _description = "Description of Goods"

    name = fields.Char('Description of Goods', required=True, readonly=False)
    note = fields.Text('Notes')

class TransferDocument(models.Model):
    _name = 'stock.ddt'
    _description = 'Transfer Document'

    _inherit = ['mail.thread']

    partner_id = fields.Many2one('res.partner', "Partner", readonly=True, required=True, states={'draft': [('readonly', False)]})
    partner_invoice_id = fields.Many2one('res.partner', "Invoice Address", readonly=True, states={'draft': [('readonly', False)]})

    name = fields.Char(string="DDT No.", copy=False, default=_("New"))
    state = fields.Selection(selection=[('draft', 'Draft'), ('waiting', 'Waiting'), ('done', 'Done'), ('cancel', 'Cancelled')], string="State", required=True, default='draft')  

    date = fields.Date("Document Date", default=fields.Date.today(), readonly=True, states={'draft': [('readonly', False)], 'waiting': [('readonly', False)]})

    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Operation Type',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]})
    picking_type_code = fields.Selection([
        ('incoming', 'Vendors'),
        ('outgoing', 'Customers'),
        ('internal', 'Internal')], related='picking_type_id.code',
        readonly=True)

    transport_partner_id = fields.Many2one('res.partner', "Carrier Address", readonly=True, related="carrier_id.transport_partner_id")
    carrier_id = fields.Many2one("delivery.carrier", string="Carrier", readonly=True, states={'draft': [('readonly', False)], 'waiting': [('readonly', False)]})

    goods_description_id = fields.Many2one('stock.picking.goods_description', 'Description of goods', readonly=True, states={'draft': [('readonly', False)], 'waiting': [('readonly', False)]})

    incoterm = fields.Many2one(
        'account.incoterms', 'Incoterms',
        help="International Commercial Terms are a series of predefined commercial terms used in international transactions.", readonly=True, states={'draft': [('readonly', False)], 'waiting': [('readonly', False)]})

    picking_ids = fields.Many2many(comodel_name='stock.picking', relation='picking_ddt_rel', string='Transfers', copy=False, readonly=True, states={'draft': [('readonly', False)], 'waiting': [('readonly', False)]})

    def _get_move_lines_no_package(self):
        for i in self:
            i.move_line_ids_without_package = i.picking_ids.mapped(lambda x: x.move_line_ids_without_package)

    move_line_ids_without_package = fields.Many2many('stock.move.line', compute=_get_move_lines_no_package)

    @api.one
    @api.depends('picking_ids', 'shipping_weight_free')
    def _compute_shipping_weight(self):
        if bool(self.shipping_weight_free):
            self.shipping_weight = self.shipping_weight_free
        else:
            self.shipping_weight = sum([pick.shipping_weight for pick in self.picking_ids])
        
    def _set_shipping_weight(self):
        self.shipping_weight_free = self.shipping_weight

    shipping_weight_free = fields.Float("Weight in Kilograms")
    shipping_weight = fields.Float(compute=_compute_shipping_weight, inverse=_set_shipping_weight, readonly=True, states={'draft': [('readonly', False)], 'waiting': [('readonly', False)]})

    number_of_packages = fields.Integer("Number of Packages", readonly=True, states={'draft': [('readonly', False)], 'waiting': [('readonly', False)]})

    note = fields.Text(string="Notes", copy=False,  readonly=True, states={'draft': [('readonly', False)], 'waiting': [('readonly', False)]})

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['stock.picking.type'].browse(vals.get('picking_type_id')).sequence_ddt_id.next_by_id()
        
        return super(TransferDocument, self).create(vals)

    @api.multi
    def unlink(self):
        for i in self:
            if i.state == 'done':
                raise UserError(_("You cannot delete a confirmed DDT."))

        return super(TransferDocument, self).unlink()

    @api.multi
    def action_print(self):
        return self.env.ref('l10n_it_picking_ddt.action_report_ddt').report_action(self)

    @api.multi
    def action_cancel(self):
        for doc in self:
            doc.write({'state': 'cancel'})
   
    @api.multi
    def action_done(self):
        for doc in self:
            for pick in doc.picking_ids:
                if pick.state != 'done':
                    raise ValidationError(_("All pickings must be validated!"))

                pick.write({'is_locked': True})

            doc.write({'state': 'done'})

    def get_lines_layouted(self):
        self.ensure_one()
        references = self.move_line_ids_without_package.mapped(lambda x: (x.move_id.sale_line_id and x.move_id.sale_line_id.order_id.client_order_ref))

        lines_layouted = list()

        for ref in references:
            if type(ref) != bool:
                lines_layouted.append((ref, self.move_line_ids_without_package.filtered(lambda x: x.move_id.sale_line_id and (x.move_id.sale_line_id.order_id.client_order_ref == ref))))
            else:
                lines_layouted.append((False, self.move_line_ids_without_package.filtered(lambda x: (not x.move_id.sale_line_id) or (not x.move_id.sale_line_id.order_id.client_order_ref))))

        return lines_layouted
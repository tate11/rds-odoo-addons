from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class StockPickingGoodsDescription(models.Model):
    _name = 'stock.picking.goods_description'
    _description = "Description of Goods"

    name = fields.Char('Description of Goods', required=True, readonly=False)
    note = fields.Text('Notes')

class TransportDocument(models.Model):
    _name = 'stock.ddt'
    _description = 'Transport Document'

    _inherit = ['mail.thread']

    partner_id = fields.Many2one('res.partner', "Partner", required=True, states={'draft': [('readonly', False)]})
    partner_invoice_id = fields.Many2one('res.partner', "Invoice Address", readonly=True, states={'draft': [('readonly', False)]})

    name = fields.Char(string="DDT No.", copy=False)
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
        readonly=True, store=True, index=True)

    transport_partner_id = fields.Many2one('res.partner', "Carrier Address", readonly=True, related="carrier_id.transport_partner_id")
    carrier_id = fields.Many2one("delivery.carrier", string="Carrier", readonly=False, states={'draft': [('readonly', False)], 'waiting': [('readonly', False)]})

    goods_description_id = fields.Many2one('stock.picking.goods_description', 'Description of goods', readonly=True, states={'draft': [('readonly', False)], 'waiting': [('readonly', False)]})

    incoterm = fields.Many2one(
        'account.incoterms', 'Incoterms',
        help="International Commercial Terms are a series of predefined commercial terms used in international transactions.", readonly=True, states={'draft': [('readonly', False)], 'waiting': [('readonly', False)]})

    picking_ids = fields.Many2many(comodel_name='stock.picking', relation='picking_ddt_rel', string='Transfers', copy=False, readonly=True, states={'draft': [('readonly', False)], 'waiting': [('readonly', False)]})

    def _get_moves(self):
        for i in self:
            i.move_ids_without_package = i.picking_ids.mapped(lambda x: x.move_ids_without_package)

    move_ids_without_package = fields.Many2many('stock.move', compute=_get_moves)

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

    #Auto Bill
    auto_complete = fields.Many2one(
        'stock.picking',
        'Auto Bill'
    )

    @api.onchange('auto_complete')
    def onchange_auto_bill(self):
        if self.auto_complete:
            self.update({
                'picking_ids': (self.picking_ids + self.auto_complete).ids,
                'picking_type_id': self.auto_complete.picking_type_id.id,
                'carrier_id': self.auto_complete.carrier_id.id,
                'partner_id': self.auto_complete.partner_id.id,
                'partner_invoice_id': (self.auto_complete.sale_id and self.auto_complete.sale_id.partner_invoice_id.id) or False,
                'auto_complete': False
            })


    @api.model
    def create(self, vals):
        if not vals.get('name', False):
            vals['name'] = self.env['stock.picking.type'].browse(vals.get('picking_type_id')).sequence_ddt_id.next_by_id()
        
        return super(TransportDocument, self).create(vals)

    @api.multi
    def unlink(self):
        for i in self:
            if i.state == 'done':
                raise UserError(_("You cannot delete a confirmed DDT."))

        return super(TransportDocument, self).unlink()

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

    def do_layouted(self):
        self.ensure_one()
        if self.move_ids_without_package.filtered(lambda x: x.sale_line_id and bool(x.sale_line_id.order_id.client_order_ref)):
          return True
        return False  

    def get_lines_layouted(self):
        self.ensure_one()
        references = self.env['sale.order']
        for i in self.move_ids_without_package:
            if i.sale_line_id and (i.sale_line_id.order_id not in references):
                references += (i.sale_line_id.order_id)

        lines_layouted = list()

        for ref in references:
            if type(ref) != bool:
                lines_layouted.append((ref, self.move_ids_without_package.filtered(lambda x: x.sale_line_id and (x.sale_line_id.order_id == ref))))
            else:
                lines_layouted.append((False, self.move_ids_without_package.filtered(lambda x: (not x.sale_line_id) or (not x.sale_line_id.order_id.client_order_ref))))
        return lines_layouted

    def get_first_sale(self):
        self.ensure_one()
        sales = self.move_ids_without_package.mapped(lambda x: x.sale_line_id)

        if sales:
            return sales[0].order_id
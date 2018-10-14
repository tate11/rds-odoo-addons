from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging, base64

def s(string):
    return string.strip()
def _s(string):
    return string.strip().replace(" ", "")

class BomImporterRow(models.TransientModel):
    _name = "bomimporter.row"
    _order = "position ASC"
    
    bomimporter_id = fields.Many2one("bomimporter.loader", "BOM Loader")

    action = fields.Selection([('use', 'Usa:'),
                               ('make', 'Crea da:')], "Action")

    position = fields.Integer('Pos')
    child_of = fields.Integer('Upper Pos')

    name = fields.Char("Name")
    product_id = fields.Many2one("product.template", "Product")
    qty = fields.Integer("Qty")
    comment = fields.Text("Notes")

    def make(self, father, master_product):
        PROD = self.sudo().env['product.template']
        BOM = self.sudo().env['mrp.bom']
        BOML = self.sudo().env['mrp.bom.line']

        for i in self:
            if i.action == 'use':
                logging.warning("Use")
                BOML.create({'bom_id': father.id, 'product_tmpl_id': i.product_id.id, 'product_id': i.product_id.id, 'sequence': i.position, 'product_qty': i.qty, 'notes': i.comment.split("\n")[-1]})
                
            elif i.action == 'make':
                data = i.product_id.copy_data()[0]
                data['default_code'] = master_product.default_code + "-{}".format(i.position)
                data['name'] = i.name

                new = PROD.create(data)
                
                bom = self.env['mrp.bom'].create({'product_tmpl_id': new.id})
                BOML.create({'bom_id': bom.id, 'product_tmpl_id': i.product_id.id, 'product_id': i.product_id.id, 'product_qty': 1})
                BOML.create({'bom_id': father.id, 'sequence': i.position, 'product_tmpl_id': new.id, 'product_id': new.id, 'notes': i.comment.split("\n")[-1]})

                i.bomimporter_id.proposed_rows.filtered(lambda x: x.child_of == i.position).make(father=bom, master_product=master_product)

        


class BomImporterLoader(models.TransientModel):
    _name = 'bomimporter.loader'

    file_dis = fields.Binary("CSV File")
    filename = fields.Char("Filename")

    name = fields.Many2one("product.template", "Product")

    state = fields.Selection([('draft', 'Waiting'), ('loaded', 'Loaded')], "State")

    proposed_rows = fields.One2many("bomimporter.row", 'bomimporter_id', "Proposed Lines")

    @api.multi
    def name_get(self):
        return [(x.id, x.name and x.name.name_get() or _("New")) for x in self]

    def load_bom(self):
        lines = base64.b64decode(self.file_dis).decode("utf-8").split("\n")
        proposed_rows = list()
        for line in lines:
            try:
                line = line.split(",")
                product = line[4] and self.env['product.template'].search([('default_code', 'ilike', "%{}%".format(line[4]))], limit=1).id
                proposed_rows.append((0, 0, {'position': int(line[0]), 'name': s(line[2]), 'qty': int(line[1]), 
                                             'product_id': product, 'action': 'use' if product else 'make',
                                             'comment': (_s(line[3]) and "{}\n".format(_s(line[3]))) + ((line[4] and (not product)) and "{}\n".format(_s(line[4])) or "") + s(line[8])}))

            except Exception:
                continue

        new_id = self.create({'state': 'loaded', 'proposed_rows': proposed_rows})

        view_id = self.env.ref('bom_importer.bom_loader_wizard_form').id
        return {'type': 'ir.actions.act_window',
                'name': _('Loaded BOM'),
                'res_model': 'bomimporter.loader',
                'target': 'self',
                'context': {'form_view_initial_mode': 'edit','force_detailed_view': True},
                'view_mode': 'form',
                'res_id': new_id.id,
                'views': [[view_id, 'form']],
        }

    def build_bom(self):
        if not self.name:
            raise UserError(_("You must set or create a destination product!"))

        bom = self.env['mrp.bom'].create({'product_tmpl_id': self.name.id})
        self.proposed_rows.filtered(lambda x: x.child_of == 0).make(father=bom, master_product=self.name)



class BomImporter(models.TransientModel):
    _name = 'bomimporter.importer'
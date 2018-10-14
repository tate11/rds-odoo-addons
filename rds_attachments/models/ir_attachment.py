# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
import odoo.tools as tools
import logging, os, base64, hashlib, shutil, subprocess
from datetime import datetime as dt
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.modules.module import get_module_resource


def getattr_(obj, attr, fallback):
    a = getattr(obj, attr, False)
    if a == False:
        if fallback:
            return fallback
        else:
            return False
    else:
        return a



class IrAttachment(models.Model):

    _name = 'ir.attachment'
    _inherit = ['ir.attachment']

    def _save_to_tmp(self):
        try:
            fname = self.datas_fname
            ext = fname[fname.rfind("."):]
            tmp_path = "/tmp/" + hashlib.md5((str(dt.now()) + self.datas_fname).encode('utf-8')).hexdigest() + ext
            shutil.copyfile(self._full_path(self.store_fname), tmp_path)
            return tmp_path
        except Exception as e:
            return False

    def _compute_mimetype(self, values):
        
        mimetype = super(IrAttachment, self)._compute_mimetype(values)
        """ compute the mimetype of the given values
            :param values : dict of values to create or write an ir_attachment
            :return mime : string indicating the mimetype, or application/octet-stream by default
        """
        if not (mimetype in ['application/octet-stream', 'text/plain']):
            return mimetype
        
        filename = values.get('datas_fname', self.datas_fname)
        if filename:
            EXTENSIONS = {'dwg': 'application/acad', 'dxf':'application/dxf', 'iges':'application/iges', 'igs': 'application/iges',
                       'part': 'application/pro_eng', 'prt': 'application/pro_eng', 'st': 'application/STEP', 
                       'step': 'application/STEP', 'stp': 'application/application/STEP', 
                       'xlsx': 'application/openxmlformats-officedocument.spreadsheetml.sheet', 'xlsm':  "application/openxmlformats-officedocument.spreadsheetml.sheet",
                       'docx': 'application/officedocument.wordprocessingml.document',
                       'pptx': 'application/openxmlformats-officedocument.presentationml.presentation'
                      }

            extension = filename.split(".")[-1].lower()
            return EXTENSIONS.get(extension, mimetype)

        return mimetype or 'application/octet-stream'

    def _compute_preview(self, vals):
        def pdfable(mimetype):
            PDFABLE_MIMETYPES = ["msword", "officedocument.wordprocessingml.document",
                                 "ms-excel", "openxmlformats-officedocument.spreadsheetml.sheet",
                                 "ms-powerpoint", "openxmlformats-officedocument.presentationml.presentation", "openxmlformats-officedocument.presentationml.slideshow"
                                ]
            
            for i in PDFABLE_MIMETYPES:
                if i in mimetype:
                    return True

        def stlable(mimetype):
            STLABLE_MIMETYPES = ["STEP", "iges"]
            for i in STLABLE_MIMETYPES:
                if i in mimetype:
                    return True
            return False

        vals_ = dict(vals)
        if 'datas' not in vals_:
            vals_['datas'] = self.datas

        mimetype = self._compute_mimetype(vals_)
        vals['mimetype'] = mimetype
        
        if mimetype == False:
            return {'preview_file': False, 'preview_text': False, 'preview_fname': False, 'preview_type': 'none'}

        vals['preview_type'] = 'none'
        if "application/pdf" == mimetype:
            vals['preview_file'] = False
            vals['preview_fname'] = self.datas_fname
            vals['preview_type'] = 'pdf-d'

        elif "application/sla" == mimetype:
            vals['preview_file'] = False
            vals['preview_fname'] = self.datas_fname
            vals['preview_type'] = '3d-d'
        
        elif "image/" in mimetype:
            vals['preview_file'] = False
            vals['preview_fname'] = self.datas_fname
            vals['preview_type'] = 'image'

        elif mimetype in ["video/mp4", "video/webm", "video/obj"]:
            vals['preview_file'] = False
            vals['preview_fname'] = self.datas_fname
            vals['preview_type'] = 'video-d'           

        elif pdfable(mimetype) or stlable(mimetype):
            full_path = False
            if self.store_fname:
                full_path = self._full_path(self.store_fname)
            if full_path:
                tmpfile = self._save_to_tmp()
                if not tmpfile:
                    vals['preview_file'] = False
                    vals['preview_fname'] = False
                
                elif stlable(mimetype):
                    p = subprocess.Popen(['freecad', '-c', '/opt/convert.py', tmpfile])
                    try:
                        p.wait(30)
                        tmp_path = '%s.stl' % tmpfile
                        vals['preview_file']  = base64.b64encode(open(tmp_path,'rb').read())
                        vals['preview_fname'] = self.datas_fname + '.stl'
                        vals['preview_type']  = '3d'
                    except subprocess.TimeoutExpired:
                        p.kill()


                elif pdfable(mimetype):
                    p = subprocess.Popen(['libreoffice', '--headless', '-convert-to', 'pdf', '--outdir', '/tmp', tmpfile])
                    try:
                        p.wait(30)
                        tmp_path = '%s.pdf' % tmpfile[:tmpfile.rfind(".")]
                        vals['preview_file']  = base64.b64encode(open(tmp_path,'rb').read())
                        vals['preview_fname'] = self.datas_fname + '.pdf'
                        vals['preview_type']  = 'pdf'
                    except subprocess.TimeoutExpired:
                        p.kill()
                try:
                    os.remove(tmpfile)
                    os.remove(tmp_path)
                except Exception:
                    pass

        elif 'text/' in mimetype:
            try:
                full_path = False
                if self.store_fname:
                    full_path = self._full_path(self.store_fname)
                if full_path:
                    vals['preview_text'] = open(full_path, 'r').read()
                    vals['preview_type'] = 'text'
            except:
                vals['preview_file']  = False
                vals['preview_fname'] = False
                vals['preview_text']  = False
                vals['preview_type']  = 'none'           
        else:
            vals['preview_file']  = False
            vals['preview_fname'] = False

        return vals

    preview_type = fields.Selection([
        ('none', 'Non Disponibile'),
        ('text', 'Testo'),
        ('pdf', 'Documento PDF'),
        ('pdf-d', 'Documento PDF (Diretto)'),
        ('3d', 'WebGL'),
        ('3d-d', 'WebGL (Diretto)'),
        ('image', 'Immagine (Diretto)'),
        ('video', 'Video'),
        ('video-d', 'Video (Diretto)')
        ], string='Preview', readonly=True, default=False, copy=False)

    document_id = fields.Integer(string="Document ID")

    preview_text = fields.Text(string="Anteprima (Testo)", readonly=True, store=True, default=False, copy=False)
    preview_file = fields.Binary(string="Anteprima", readonly=True, store=True, default=False, copy=False)
    preview_fname = fields.Char(string="Nome File", readonly=True, store=True, default=False, copy=False)

    description = fields.Text(string="Descrizione")

    def write(self, values):
        a = super(IrAttachment, self).write(values)
        if ('datas' in values):
            values = self._compute_preview(values)
            return super(IrAttachment, self).write(values) 
        else:
            return a

    @api.multi
    def refr_pw(self):
        for i in self:
            values = i._compute_preview({})
            i.write(values)

    def to_document(self):
        values = {'name': self.datas_fname,'ir_attachment_id': self.ids[0], 'ref_doc_id': "%s,%s" % (self.res_model, self.res_id) }
        a = self.env['rds.ir.document'].create(values)
        self.document_id = a.id
        
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'rds.ir.document',
            'target': 'this',
            'res_id': a.id
        }
        
    @api.constrains('date_from', 'date_to')
    def _check_date(self):
        for i in self:
            if (i.public_w == True) & (i.public_r == False):
                raise ValidationError("Un documento in pubblica scrittura non può essere privato in lettura!")

class IrDocumendFolder(models.Model):

    _name = "rds.ir.document.folder"
    _description = "Document Folder"

    name = fields.Char(string="Cartella")

    description = fields.Text(string="Descrizione")

    @api.model
    def _default_image(self):
        image_path = get_module_resource('rds_attachments', 'static/src/img', 'default_folder.png')
        return tools.image_resize_image_big(base64.b64encode(open(image_path, 'rb').read()))

    icon = fields.Binary(
        "Icona", default=_default_image, attachment=True,
        help="Icona della Cartella.")

    restricted_r = fields.Boolean(string="Lettura Riservata")
    restricted_w = fields.Boolean(string="Scrittura Riservata")
    users_r = fields.Many2many('res.users', relation="folder_users_r", string="Utenti in Lettura", store=True)
    users_w = fields.Many2many('res.users', relation="folder_users_w", string="Utenti in Scrittura", store=True)

    document_ids = fields.One2many('rds.ir.document', inverse_name="folder_id", string='Documents')
    doc_count = fields.Integer(compute="_compute_docs_count")

    @api.multi
    def folder_view_docs(self):
        self.ensure_one()
        domain = [('id', 'in', self.document_ids.ids)]
        return {
            'name': 'Documenti',
            'domain': domain,
            'res_model': 'rds.ir.document',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'help': '''<p class="oe_view_nocontent_create">
                        Documents are attached to the tasks and issues of your project.</p><p>
                        Send messages or log internal notes with attachments to link
                        documents to your project.
                    </p>''',
            'context': {'default_folder_id': self.id},
            'limit': 80
        }

    def _compute_docs_count(self):
        for i in self:
            i.doc_count = len(i.document_ids)


class IrDocumentTag(models.Model):
    _description = 'Document Tags'
    _name = 'rds.ir.document.tag'
    _order = 'parent_left, name'
    _parent_store = True
    _parent_order = 'name'

    name = fields.Char(string='Tag Name', required=True, translate=True)
    complete_name = fields.Char(string='Complete Tag Name', compute="get_complete_tag_name")
    color = fields.Integer(string='Color Index')
    parent_id = fields.Many2one('rds.ir.document.tag', string='Parent Category', index=True, ondelete='cascade')
    child_ids = fields.One2many('rds.ir.document.tag', 'parent_id', string='Child Tags')
    active = fields.Boolean(default=True, help="The active field allows you to hide the category without removing it.")
    parent_left = fields.Integer(string='Left parent', index=True)
    parent_right = fields.Integer(string='Right parent', index=True)
    document_ids = fields.Many2many('rds.ir.document', 'rds_ir_document_tag_rel', 'tag_ids', 'document_ids', string='Documents')

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_('Error ! You can not create recursive tags.'))

    @api.multi
    def get_complete_tag_name(self):
        for tag in self:
            names = []
            current = tag
            while current:
                names.append(current.name)
                current = current.parent_id
            tag.complete_name = ' / '.join(reversed(names))

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            # Be sure name_search is symetric to name_get
            name = name.split(' / ')[-1]
            args = [('name', operator, name)] + args
        return self.search(args, limit=limit).name_get()


class ResRequestLink(models.Model):
    _name = 'res.request.link'
    _inherit = 'res.request.link'
    
    color = fields.Integer(string='Color Index')

class IrDocumentLink(models.Model):

    _name = "rds.ir.document.link"
    _description = "Document Links"

    _rec_name = 'complete_name'

    @api.model 
    def _referencable_models(self): 
        models = self.env['res.request.link'].search([]) 
        return [(x.object, x.name) for x in models] 

    @api.model 
    def _referencable_models_dict(self): 
        models = self.env['res.request.link'].search([])
        dictionary = {}
        for x in models:
            dictionary[x.object] = [x.name, x.color]
        return dictionary

    complete_name = fields.Char('Complete Name', compute='_compute_complete_name', store=True)

    @api.depends('name')
    def _compute_complete_name(self):
        for i in self:
            refs = i._referencable_models_dict()[i.name._name]
            if getattr(i.name, 'name', False):
                i.complete_name = "[%s] %s" % (refs[0], i.name.name)
                i.color = refs[1]
            else:
                i.complete_name = "%s" % (i.name)
                i.color = refs[1]

    name = fields.Reference(
        selection='_referencable_models',
        string='Oggetto di Riferimento',
        required=True)

    color = fields.Integer(string='Color Index', compute='_compute_complete_name', store=True)
    document_ids = fields.Many2many('rds.ir.document', 'rds_ir_document_link_rel', 'links_ids', 'document_ids', string='Documents')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]


class IrDocument(models.Model):

    _name = 'rds.ir.document'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _inherits = {
        'ir.attachment': 'ir_attachment_id',
    }
    ir_attachment_id = fields.Many2one('ir.attachment', string='Related attachment', required='True', ondelete='cascade')
    _description = 'Documento'


    name = fields.Char(default="Senza Titolo")

    links_ids = fields.Many2many(
        'rds.ir.document.link', 'rds_ir_document_link_rel',
        'document_ids', 'links_ids',
        string='Documenti Collegati')

    tag_ids = fields.Many2many(
        'rds.ir.document.tag', 'rds_ir_document_tag_rel',
        'document_ids', 'tag_ids',
        string='Tags')

    state = fields.Selection([
        ('draft', 'Bozza'),
        ('valid', 'Documento Valido'),
        ('changing', 'In Revisione'),
        ('cancel', 'Cancellato'),
        ('surpassed', 'Sorpassato'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    
    folder_id = fields.Many2one('rds.ir.document.folder', string='Cartella')

    working_user = fields.Many2one('res.users', "Utente Bloccante", readonly=True, copy=False)
    working_path = fields.Char("File di Lavoro", copy=False)

    restricted_r = fields.Boolean(string="Lettura Riservata", related="folder_id.restricted_r", readonly=True)
    restricted_w = fields.Boolean(string="Scrittura Riservata", related="folder_id.restricted_w", readonly=True)
    users_r = fields.Many2many('res.users', string="Utenti in Lettura", related="folder_id.users_r", readonly=True)
    users_w = fields.Many2many('res.users', string="Utenti in Scrittura", related="folder_id.users_w", readonly=True)

    ##COPIA FISICA
    building = fields.Char(size=4, string="Edificio", default="PD01")
    section = fields.Char(size=2, string="Stanza")
    place = fields.Char(size=2, string="Armadio/Scaffalatura")
    subplace = fields.Char(size=2, string="Scaffale/Mensola")
    collector = fields.Char(size=3, string="Faldone")


#########################################################################################################
############                          SISTEMA GESTIONE DELLE REVISIONI                       ############
#########################################################################################################
                                                                                                        #
    @api.multi                                                                                          #
    def _compute_revs(self):                                                                            #
        for i in self:                                                                                  #
            if i.original:                                                                              #
                i.next_rev = i.env[i._name].search([('original','=',i.original.id),                     #
                                                   ('rev_no', '=', (i.rev_no+1))])                      #
            if bool(i.original) & (i.rev_no > 0):                                                       #
                i.prev_rev = i.env[i._name].search([('original','=',i.original.id),                     #
                                                   ('rev_no', '=', (i.rev_no-1))])                      #
                                                                                                        #
                                                                                                        #
                                                                                                        #
    rev_no = fields.Integer(string="Rev No.", readonly=True, default=0)                                 #
    original = fields.Many2one(_name, string="Originale", readonly=True)                                #
    next_rev = fields.Many2one(_name, string="Rev. Successiva",                                         #
                               store=False, compute="_compute_revs")                                    #
    prev_rev = fields.Many2one(_name, string="Rev. Precedente",                                         #
                               store=False, compute="_compute_revs")                                    #
                                                                                                        #
    @api.multi                                                                                          #
    def action_view_revisions(self):                                                                    #
        if self.original:                                                                               #
            domain = ['|', ('id', 'in', [self.original.id, self.ids[0]]),                               #
                           ('original', 'in', [self.original.id, self.ids[0]])]                         #
        else:                                                                                           #
            domain = ['|', ('id', 'in', [self.original.id, self.ids[0]]),                               #
                           ('original', 'in', self.ids[0])]                                             #
                                                                                                        #
        return {                                                                                        #
            'name': 'Revisioni',                                                                        #
            'create': False,                                                                            #
            'domain': domain,                                                                           #
            'res_model':  self._name,                                                                   #
            'type': 'ir.actions.act_window',                                                            #
            'view_id': False,                                                                           #
            'view_mode': 'kanban,tree,form',                                                            #
            'view_type': 'form',                                                                        #
            'help': '''<p class="oe_view_nocontent_create">                                             
                        Puoi visualizzare qui tutte le revisioni dei documenti.                         
                    </p>''',                                                                            #
            'limit': 80,                                                                                #
        }                                                                                               #
                                                                                                        #
    @api.multi                                                                                          #
    def action_revise(self):                                                                            #
            new = self.copy({'name': self.name,                                                         #
                             'original': self.original.ids[0] if self.original else self.ids[0],        #
                             'rev_no': (self.rev_no+1)})                                                #
            self.write({                                                                                #
                'state': 'surpassed',
                'original': self.original.ids[0] if self.original else self.ids[0],                                                                 #
            })                                                                                          #
            return {'view_type': 'form',                                                                #
                    'res_model': self._name,                                                            #
                    'type': 'ir.actions.act_window',                                                    #
                    'view_mode': 'form',                                                                #
                    'res_id': new.id,                                                                   #
                    }                                                                                   #
                                                                                                        #
#########################################################################################################


#Bottoni

    @api.multi
    def action_approve(self):
        for i in self:
            i.write({'state': 'valid'})

    @api.multi
    def action_lock(self):
        for i in self:
            i.write({'state': 'changing'})
            i.working_user = self.env.user

    @api.multi
    def action_unlock(self):
        for i in self:
            i.write({'state': 'valid'})

    @api.multi    
    def save_to_wk_dir(self):
        root = self.env['ir.config_parameter'].sudo().get_param('working.directories.root')
        wkdir = root + self.env.user.wk_dir + hashlib.md5(( str(dt.now()) ).encode('utf-8')).hexdigest()[:5] + "_File_da_Odoo/"
        
        if not os.path.exists(wkdir):
            os.makedirs(wkdir)

        os.chmod(wkdir, 0o777)
        self._save_to_wk_dir(wkdir)

    @api.multi    
    def load_from_wk_dir(self):
        for i in self:
            if i.working_user != self.env.user:
                continue

                try:
                    i.write({
                        'state': 'valid',
                        'original': i.original.ids[0] if i.original else i.ids[0],
                        'datas': base64.b64encode(open(i.working_path,'rb').read()),
                        'working_path': False,
                        'working_user': False
                    })
                except Exception:
                    continue

    @api.multi    
    def load_from_wk_dir_nr(self):
        new = self.copy({'name': self.name,
                        'original': self.original.ids[0] if self.original else self.ids[0],
                        'rev_no': (self.rev_no+1),
                        'datas': base64.b64encode(open(self.working_path,'rb').read()),
                        'mimetype': self.mimetype
                        })
        self.write({
            'state': 'surpassed',
            'original': self.original.ids[0] if self.original else self.ids[0],
            'working_path': False,
            'working_user': False
        })

        return {'view_type': 'form',
                'res_model': self._name,
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_id': new.id,
                }
        
    def _save_to_wk_dir(self, wdir):
        for i in self:
            try:
                tmp_path = wdir + i.datas_fname
                shutil.copyfile(i.ir_attachment_id._full_path(i.store_fname), tmp_path)
                os.chmod(tmp_path, 0o777)

                if i.state == 'changing':
                    i.working_path = tmp_path

            except Exception:
                continue

    @api.model
    def create(self, values):
        if not ('ir_attachment_id' in values):
            att = self.env['ir.attachment'].create({'name': values['name']})
            values['ir_attachment_id'] = att.ids[0]

        ####REVISIONI
        return super(IrDocument, self).create(values)


    @api.multi
    def copy(self, default={}):
        new_attachment_id = self.ir_attachment_id.copy()
        # website.page's ir.ui.view should have a different key than the one it
        # is copied from.
        # (eg: website_version: an ir.ui.view record with the same key is
        # expected to be the same ir.ui.view but from another version)
        default['name'] = default.get('name', self.name + ' (copia)')
        default['ir_attachment_id'] = new_attachment_id.ids[0]

        return super(IrDocument, self).copy(default=default)

    @api.multi
    def refr_pw(self):
        for i in self:
            values = i.ir_attachment_id._compute_preview({})
            i.ir_attachment_id.write(values)

class RdsDocumentMixin(models.AbstractModel):
    _name = 'rds.document.mixin'

    def get_link(self):
        domain = [('name', '=', '%s' % ((str(self._name) + ',' + str(self.ids[0])) ))]
        link = self.env['rds.ir.document.link'].search(domain)
        if link:
            return link
        else:
            try:
                link = self.env['rds.ir.document.link'].create({'name':  '%s' % (str(self._name) + ',' + str(self.ids[0])) })
                return link
            except Exception:
                return False

    @api.multi
    def rds_view_attachments(self):
        self.ensure_one()
        link = self.get_link()

        domain = [('links_ids', 'in', link.ids[0])]
        return {
            'name': 'Documenti',
            'domain': domain,
            'res_model': 'rds.ir.document',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'help': '''<p class="oe_view_nocontent_create">
                        Documents are attached to the tasks and issues of your project.</p><p>
                        Send messages or log internal notes with attachments to link
                        documents to your project.
                    </p>''',
            'context': {'default_links_ids': (4, link.id)},
            'limit': 80
        }

    doc_count = fields.Integer(compute='_compute_attached_docs_count', string="Number of documents attached")

    def _compute_attached_docs_count(self):
        documents = self.env['rds.ir.document']
        for i in self:
            link = i.get_link()
            if link == False:
                i.doc_count = 0
            else:
                domain = [('links_ids', 'in', link.ids[0])]
                i.doc_count = documents.search_count(domain)


class Users(models.Model):
    """ User class. A res.users record models an OpenERP user and is different
        from an employee.

        res.users class now inherits from res.partner. The partner model is
        used to store the data related to the partner: lang, name, address,
        avatar, ... The user model is now dedicated to technical data.
    """
    _inherit = "res.users"

    wk_dir = fields.Char("Castella di Lavoro")


class Lead(models.Model):
    _inherit = ['crm.lead', 'rds.document.mixin']
    _name = 'crm.lead'

class Employee(models.Model):
    _inherit = ['hr.employee', 'rds.document.mixin']
    _name = 'hr.employee'

class Partner(models.Model):
    _inherit = ['res.partner', 'rds.document.mixin']
    _name = 'res.partner'

class ProductTemplate(models.Model):
    _inherit = ['product.template', 'rds.document.mixin']
    _name = 'product.template'

class HrJob(models.Model):
    _inherit = ['hr.job', 'rds.document.mixin']
    _name = 'hr.job'

class Project(models.Model):
    _inherit = ['project.project', 'rds.document.mixin']
    _name = 'project.project'

class ProjectTask(models.Model):
    _inherit = ['project.task', 'rds.document.mixin']
    _name = 'project.task'
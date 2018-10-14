import base64
import datetime
import dateutil
import email
import hashlib
import hmac
import lxml
import logging
import pytz
import re
import socket
import time
try:
    from xmlrpc import client as xmlrpclib
except ImportError:
    import xmlrpclib

from collections import namedtuple
from email.utils import formataddr
from lxml import etree
from werkzeug import url_encode

from odoo.osv import expression
from odoo import _, api, exceptions, fields, models, tools
from odoo.tools import pycompat, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.safe_eval import safe_eval
import html2text

try:
    from email_validator import validate_email, EmailNotValidError
except Exception as ex:
    logging.error("Unable to load python library email_validator")

_logger = logging.getLogger(__name__)


def get_fully_featured_emails(emails):
    _emails = list(set(emails.split(",")))
    validated_emails = []

    for i in _emails:
        try:
            validated_emails += [validate_email(i.strip())['email']]
        except EmailNotValidError:
            try:
                validated_emails += [validate_email(i[i.index('<') + 1:i.index('>')].strip())['email']]
            except Exception:
                continue

    return list(set(validated_emails))

class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def send_mail(self, auto_commit=False):
        if self.env.context.get('create_new_topic'):
            a = self.env['rds.mail.topic'].create({'name': self.subject})
            self.model = 'rds.mail.topic'
            self.res_id = a.id

            obj = super(MailComposeMessage, self).send_mail(auto_commit=auto_commit)
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'rds.mail.topic',
                'res_id': a.id,
                'views': [(False, 'form')],
                'target': 'main',
            }
        else:
            return super(MailComposeMessage, self).send_mail(auto_commit=auto_commit)


class Topic(models.Model):
    _name = 'rds.mail.topic'
    _description = "Topic"
    _inherit = ['mail.thread']
    _order = 'message_last_post desc'

    name = fields.Char('Oggetto:')

    @api.multi
    def convert(self):
        wizard = self.env['channel.tothread']
        new = wizard.create({'topic_id': self.ids[0]})
        return {'name': _('Crea o converti thread'),
                'view_type': 'form',
                'res_model': 'channel.tothread',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_id': new.id,
                'target': 'new',
                }


class Message(models.Model):
    _inherit = 'mail.message'

    @api.model
    def create(self, vals):
        a = super(Message, self).create(vals)

        if a.author_id:
            usr = self.env['res.users'].search([('partner_id', '=', a.author_id.id)], limit=1)
            if usr:
                a.mail_server_id = usr[0].mail_server_id
            else:
                a.mail_server_id = False
        else:
            a.mail_server_id = False

        if a.model and a.res_id:
            query = ""
            ids = a.partner_ids.filtered(lambda x: x.parent_id.id == 1).ids

            try:
                ids += a.email_cc_ids.filtered(lambda x: x.parent_id.id == 1).ids
                ids +=  a.email_bcc_ids.filtered(lambda x: x.parent_id.id == 1).ids
            except Exception:
                pass

            now = fields.datetime.now()
            for idx in ids:
                query += """update mail_followers set follow_state='follow', last_message_date='%s' where res_model='%s' and res_id=%d and partner_id=%d and follow_state='silenced';""" % (now, a.model, a.res_id, idx)
                query += (("""insert into mail_followers (res_model, res_id, partner_id, last_message_date,follow_state) 
                              select '%s', %d, %d, '%s', 'follow' """ % (a.model, a.res_id, idx, now) ) +
                          ("""where not exists (select 1 from mail_followers where res_model='%s' and res_id=%d and partner_id=%d);""" % (a.model, a.res_id, idx)))
            if query:
                result = self.env.cr.execute(query)
                logging.warning( "Updated follower records: %s" % result)

        return a

    @api.multi
    def write(self, vals):
        super(Message, self).write(vals)
        for a in self:
            if a.model and a.res_id:
                query = ""
                ids = a.partner_ids.filtered(lambda x: x.parent_id.id == 1).ids

                try:
                    ids += a.email_cc_ids.filtered(lambda x: x.parent_id.id == 1).ids
                    ids +=  a.email_bcc_ids.filtered(lambda x: x.parent_id.id == 1).ids
                except Exception:
                    pass

                now = fields.datetime.now()
                for idx in ids:
                    query += """update mail_followers set follow_state='follow', last_message_date='%s' where res_model='%s' and res_id=%d and partner_id=%d and follow_state='silenced';""" % (now, a.model, a.res_id, idx)
                    query += (("""insert into mail_followers (res_model, res_id, partner_id, last_message_date,follow_state) 
                                select '%s', %d, %d, '%s', 'follow' """ % (a.model, a.res_id, idx, now) ) +
                            ("""where not exists (select 1 from mail_followers where res_model='%s' and res_id=%d and partner_id=%d);""" % (a.model, a.res_id, idx)))
                if query:
                    result = self.env.cr.execute(query)
                    logging.warning( "Updated follower records: %s" % result)

    @api.model
    def threads_mark_read(self, recs):
        domain = []
        for i in recs:
            domain = expression.OR([domain, ['&', ['model', '=', i[0]], ['res_id', '=', i[1]] ]])
        query = """delete from mail_message_res_partner_needaction_rel where mail_message_id = any(array%s) and res_partner_id = %s;""" % (self.search(domain, limit=None).ids, self.env.user.partner_id.id)
        self.env.cr.execute(query)

    @api.model
    def threads_silence(self, recs):
        domain = [('partner_id', '=', self.env.user.partner_id.id)]
        dom = []
        for i in recs:
            dom = expression.OR([dom, ['&', ['res_model', '=', i[0]], ['res_id', '=', i[1]] ]])
        domain = expression.AND([domain, dom])

        self.env['mail.followers'].search(domain).silence()

    @api.model
    def threads_unfollow(self, recs):
        domain = [('partner_id', '=', self.env.user.partner_id.id)]
        dom = []
        for i in recs:
            dom = expression.OR([dom, ['&', ['res_model', '=', i[0]], ['res_id', '=', i[1]] ]])
        domain = expression.AND([domain, dom])

        self.env['mail.followers'].search(domain).unlink()

    @api.model
    def thread_fetch(self, domain, cached=[], fwstate=[]):

        LIMIT = 20
        partner_id = self.env.user.partner_id.id

        threads = []
        parser_tuples = [tuple(x) for x in cached]

        nomore = False

        while len(threads) < LIMIT:
            pt_dom = [('partner_id', '=', partner_id), ('follow_state', 'in', fwstate)]

            for i in parser_tuples:
                pt_dom = expression.AND([pt_dom, ['&', ['res_model', '!=', i[0]], ['res_id', '!=', i[1]]]])

            following = self.sudo().env['mail.followers'].search(pt_dom, order="last_message_date DESC", limit=LIMIT)

            if not following:
                nomore = True
                break

            parser_tuples += [(i.res_model, i.res_id) for i in following]

            following = following.filtered(lambda x: x.filter_by_msg(domain))

            for i in following:
                if len(threads) == LIMIT:
                    break
                threads += [(self.env[i.res_model].browse(i.res_id), i.get_last_msg(), i.follow_state)]
        
        del(parser_tuples)
        
        return self.format_threads(threads, nomore)

    @api.multi
    def format_threads(self, threads, nomore=False):
        recs = []

        for t in threads:
            i = t[0]
            m = t[1]

            preview = html2text.html2text(m.body if m.body else "")
            try:
                _date = pytz.utc.localize(datetime.datetime.strptime(m.date, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(pytz.timezone("Europe/Rome"))
                if _date.date() == datetime.date.today():
                    date = _date.strftime("%H:%M")
                else:
                    date = _date.strftime("%h %d")
            except Exception:
                date = "--:--"


            recs += [{'model': i._name,  'model_desc': i._description,'id': i.id, 'name': i.name if i.name else "<Nessun Oggetto>", 'followstate': t[2],
                      'last_post_date': date, 'effective_timestamp': m.date, 'author_id': m.author_id.id if m.author_id else False, 'author_name': (("%s <%s>") % (m.author_id.name, m.author_id.email)) if m.author_id else m.email_from,
                      'unread': int(self.env.user.partner_id in m.needaction_partner_ids), 'unread_n': i.message_unread_counter, 'preview': preview[:min(len(preview), 100)]}]

        return [sorted(recs, key=lambda x: x['effective_timestamp'], reverse=True), nomore]


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    @api.multi
    @api.returns('self', lambda value: value.id)
    def message_post(self, *vargs, **kwargs):
        for fw in self.sudo().message_follower_ids:
            fw.last_message_date = fields.Datetime.now()
            fw.follow_state = 'follow'
        return super(MailThread, self).message_post(*vargs, **kwargs)

    @api.multi
    @api.depends('message_follower_ids')
    def _compute_follow_state(self):
        followers = self.env['mail.followers'].sudo().search([
            ('res_model', '=', self._name),
            ('res_id', 'in', self.ids),
            ('partner_id', '=', self.env.user.partner_id.id)])

        for record in self:
            try:
                record.follow_state = followers.filtered(lambda x: x.res_id == record.id)[0].follow_state
            except IndexError:
                record.follow_state = False

    @api.model
    def _search_follow_state(self, operator, operand):
        followers = self.env['mail.followers'].sudo().search([
            ('res_model', '=', self._name),
            ('partner_id', '=', self.env.user.partner_id.id),
            ('follow_state', operator, operand)])

        return [('id', 'in', followers.mapped('res_id'))]

    @api.model
    def toggle_fav(self, rid):
        rec = self.env[self._name].browse(rid)
        fw = rec.message_follower_ids.filtered(lambda x: x.partner_id == self.env.user.partner_id)[0]
        if fw.follow_state == 'follow':
            fw.follow_state = 'starred'
            return 'starred'
        if fw.follow_state == 'starred':
            fw.follow_state = 'follow'
            return 'follow'

    def _message_find_partners(self, message, header_fields=['From']):
        """ Find partners related to some header fields of the message.

            :param string message: an email.message instance """
        s = ', '.join([tools.decode_smtp_header(message.get(h)).replace("rdssubfornitura.com", "rdsmoulding.com") for h in header_fields if message.get(h)])
        result = [x for x in self._find_partner_from_emails(tools.email_split(s)) if x]
        return result


class Followers(models.Model):
    """ mail_followers holds the data related to the follow mechanism inside
    Odoo. Partners can choose to follow documents (records) of any kind
    that inherits from mail.thread. Following documents allow to receive
    notifications for new messages. A subscription is characterized by:

    :param: res_model: model of the followed objects
    :param: res_id: ID of resource (may be 0 for every objects)
    """
    _inherit = 'mail.followers'

    last_message_date = fields.Datetime('Data Ultimo Messaggio')
    follow_state = fields.Selection(selection=[('follow', 'Sta Seguendo'),
                                               ('starred', 'Preferito'),
                                               ('silenced', 'Nascosto')
                                               ], string='Stato', default="follow")

    @api.model
    def create(self, vals):
        vals['follow_state'] = 'follow'
        if ('res_model' in vals) and ('res_id' in vals):
            rec = self.sudo().env[vals['res_model']].browse(vals['res_id'])
            date_lp = rec.message_last_post 
            vals['last_message_date'] = date_lp if date_lp else rec.create_date

        return super(Followers, self).create(vals)

    @api.model
    def MASS_UPDATE_CREATE_DATE(self):
        ok = 0
        not_ok = 0
        for i in self.env['mail.followers'].search([], limit=20000):
            try:
                rec = self.sudo().env[i.res_model].browse(i.res_id)
                date_lp = rec.message_last_post
                i.last_message_date = date_lp if date_lp else rec.create_date
                ok += 1
            except Exception:
                not_ok += 1
                continue

        logging.warning("Riparati %d records, falliti %d" % (ok, not_ok))


    @api.model
    def silence(self):
        for i in self:
            i.follow_state = 'silenced'

    def filter_by_msg(self, domain):
        return True if self.env['mail.message'].search(expression.AND([domain, ['&', ['model', '=', self.res_model], ['res_id', '=', self.res_id]]])) else False

    def get_last_msg(self):
        return self.env['mail.message'].search(['&', ['model', '=', self.res_model], ['res_id', '=', self.res_id]], limit=1)


class Users(models.Model):
    """ User class. A res.users record models an OpenERP user and is different
        from an employee.

        res.users class now inherits from res.partner. The partner model is
        used to store the data related to the partner: lang, name, address,
        avatar, ... The user model is now dedicated to technical data.
    """
    _inherit = "res.users"

    mail_server_id = fields.Many2one("ir.mail_server", string="Server Mail")


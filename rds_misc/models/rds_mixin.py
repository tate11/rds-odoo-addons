from odoo import api, fields, models

class RdsMixin(models.AbstractModel): 
    _name = 'rds.mixin'
    _description = 'RDS Mixin'

    @api.multi
    def notify_managers(self, title, message_body, add_groups_xmlids=[], warn=True):
        groups_xmlids = ['rds_misc.group_rds_ad'] + add_groups_xmlids

        if (warn):
            for g in groups_xmlids:
                gr = self.env.ref(g)
                recipients = []
                for usr in gr.users:
                    recipients.append(usr.partner_id.id)
        else:
            recipients = ['']

        self.message_post(
                subject=title,
                body=message_body,
                partner_ids= recipients,
                type='notification',
                subtype=False,)
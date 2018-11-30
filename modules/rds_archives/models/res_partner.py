# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import os
import logging
from odoo import api
from odoo import fields
from odoo import models
from odoo import _
from odoo.exceptions import UserError, ValidationError
import csv

logger = logging.getLogger()

try:
    import cx_Oracle
except Exception as ex:
    logging.warning("Unable to import cx_oracle module some functionality may not work %s" % ex)



class PaymentTerm(models.Model):
    _inherit = ['account.payment.term']

    def get_or_make(self, code, desc):
        if (not code) or not code.strip():
            return False
        res = self.search([('dia_code', '=', code.strip())])
        if not res:
            res = self.create({'name': desc, 'dia_code': code.strip()})
        return res and res.id or False

class ResPartner(models.Model):

    _inherit = ['res.partner']

    @api.model
    def dia2vals(self, code, mode="cli"):

        con = cx_Oracle.connect('asal', 'ace0896AC21', '10.15.0.103/EUR3')
        cur = con.cursor()

        if mode == "cli":
            t = cur.execute("""
                SELECT d.CONTO, d.P_IVA, d.PAGAMENTO, p.DES_PAG, tl.ID_FISC_COD_DF, tl.CFIS_DF
                FROM XLDB01.AN_CLI d
                LEFT JOIN XLDB01.AN_CLIFOR_FISC tl ON tl.CONTO = d.CONTO
                LEFT JOIN XLDB01.PAGAMENTI p ON p.PAGAMENTO = d.PAGAMENTO 
                WHERE d.CONTO LIKE '1 {}%'
                """.format(str(code))).fetchone()
            pcode = 'property_payment_term_id'

        elif mode == "for":
            t = cur.execute("""
                SELECT d.CONTO, d.P_IVA, d.PAGAMENTO, p.DES_PAG, tl.ID_FISC_COD_DF, tl.CFIS_DF
                FROM XLDB01.AN_FOR d
                LEFT JOIN XLDB01.AN_CLIFOR_FISC tl ON tl.CONTO = d.CONTO
                LEFT JOIN XLDB01.PAGAMENTI p ON p.PAGAMENTO = d.PAGAMENTO
                WHERE d.CONTO LIKE '1 {}%'
                """.format(str(code))).fetchone()
            pcode = 'property_supplier_payment_term_id'

        if not t:
            return False


        vals = {
            'vat': t[1].strip(),
            'fiscalcode': (t[5] and t[5].strip()) or (t[4] and t[4].strip()) or "",
            pcode: self.env['account.payment.term'].get_or_make(t[2], t[3])
        }

        return vals

    @api.multi
    def customer_fix_vat_fc(self):
        for i in self:
            vals = False
            ref_customer, ref_vendor = getattr(i, 'dia_ref_customer'), getattr(i, 'dia_ref_vendor')


            if ref_vendor:
                vals = self.dia2vals(ref_vendor, mode="for")

            if ref_customer:
                f_vals = self.dia2vals(ref_customer)
                if vals:
                    for key in f_vals.keys():
                        vals[key] = f_vals[key]
                else:
                    vals = f_vals

            if not vals:
                logger.error("Cliente ({}) {} saltato perché non rintracciabile nel DB dia.".format(i.id, i.name))
                continue
            try:
                i.write(vals)
            except ValidationError:
                continue

    @api.model
    def load_from_csv(self, mode='dry_run'):
        PARTNER = self

        log_stream = list()
        failed_vats = list()

        def get_partner(ref, name, vat):
            result = False
            if ref:
                result = PARTNER.search(['|', ('dia_ref_vendor', '=', ref), ('dia_ref_customer', '=', ref)], limit=1)
            if vat and (not result):
                result = PARTNER.search([('vat', 'like', '%{}%'.format(vat))], limit=1)

            if not result:
                log_stream.append("Missing partner {} ({})".format(name, vat) + (ref and ", Dia Ref. {}, creating from scratch!".format(ref) or "creating from scratch!"))
            return result

        def bank_getormake(abi, cab, name=False):
            if (not bool(abi.strip())) or (not bool(cab.strip())):
                return False

            bank = self.env['res.bank'].search([('abi', '=', abi), ('cab', '=', cab)], limit=1)
            
            if bank:
                return bank
            else:
                bnk = self.env['res.bank'].create({'abi': abi, 'cab': cab, 'name': name.strip() if bool(name.strip()) else abi+cab})
                log_stream.append("Creating Bank {} ({})".format(abi, cab))
                return bnk

        def to_dict(line):
            bank_riba = bank_getormake(line[17], line[18], line[19])

            if (line[20] == line[17]) and (line[22] == line[18]):
                bank_bnf = bank_riba
            else:
                bank_bnf = bank_getormake(line[20], line[22], line[21])

            banks = []
            if getattr(bank_riba, 'id', False):
                banks.append((0, 0, {'bank_id': bank_riba.id, 'acc_number': 'RiBa-' + line[12].strip()}))
            if getattr(bank_bnf, 'id', False) and bool(line[24].strip()):
                banks.append((0, 0, {'bank_id': bank_bnf.id, 'acc_number': line[24]}))

            if line[9] == 'I':
                posiz = 1 if line[12].strip() == "" else 4
            else:
                posiz = 3 if line[13].strip() == 'N' else 2

            vals = {
                'dia_ref': line[0].strip() or False,
                'name': line[1].strip() + line[2].strip(),
                'street': line[3].strip(),
                'zip': line[4],
                'city': line[5],
                'state_id': getattr(self.env['res.country.state'].search([('code', 'ilike', line[6].strip())], limit=1), 'id', False),
                'country_id': getattr(self.env['res.country'].search([('code', 'ilike', line[7].strip() or 'IT')], limit=1), 'id', False),
                'is_company': True, 'is_individual': True if line[8] == 'S' else False,
                'fiscalcode': line[11].strip(), 'vat': line[12].strip(),
                'phone': line[14],
                'payment_term_id': getattr(self.env['account.payment.term'].search([('dia_code', 'ilike', line[15].strip())], limit=1), 'id', False),
                'bank_ids': banks,
                'property_account_position_id': posiz
            }

            return vals

        with open("/tmp/partners.csv", 'r') as file:
            raw_data = list(csv.reader(file))[1:]
        
        
        """
 'CODICE', 'RAGIONE SOCIALE 1', 'RAGIONE SOCIALE 2',
 'INDIRIZZO (VIA)', 'CAP', "LOCALITA'", 'PROV.', 'NAZ.',
 'pers.Fisica', 'It/Estero', 'CEE', 'CODICE FISCALE', 'PARTITA IVA',
 'ES.IVA', 'TELEFONO', 'PAGAMENTO', 'descr.pagamento', 'BANCA APP.', 'CAB B.APP.', 'AGENZIA BANCA APPOGGIO',
 'BANCA BNF.', 'AGENZIA BANCA BONIFICI', 'CAB B.BNF.', 'C/CORRENTE', 'IBAN', 'ANNOTAZIONI (1)', 'ANNOTAZIONI (2)'

 '08002724', '4P SRL', ' ',
 'Via Germania, 15', '35127', 'PADOVA', 'PD', ' ', 
 'N', 'I', 'N', '02168560288', '02168560288',
 ' ', '0498069811', 'R6F', 'RIBA 60 GG D.F.F.M.', '06225', '62690', ' ',
 ' ', ' ', ' ', ' ', ' ', 'SENTIRE GIULIANO x INSOLUTO W1245/11', ' '
        """

        created_partners = PARTNER

        for i in raw_data:
            i = to_dict(i)

            if not i or not i['dia_ref']:
                log_stream.append("[GRAVE] Bad line data for partner. Skipping ({}) {} - {}.".format(i['dia_red'], i['name'], i['vat']))
                continue

            vendor = i['dia_ref'][0] == '2'

            name = i['name']
            vat = i['vat']
            ref = i['dia_ref']

            if i['bank_ids'] == []:
                i.pop('bank_ids', False)

            if vendor:
                i['dia_ref_vendor'] = i.pop('dia_ref')
                i['supplier'] = True
                i['customer'] = False
                i['property_supplier_payment_term_id'] = i.pop('payment_term_id')
                i.pop('bank_ids', False)

                part = get_partner(i['dia_ref_vendor'], i['name'], i['vat'])

            else:
                i['dia_ref_customer'] = i.pop('dia_ref')
                i['customer'] = True
                i['supplier'] = False
                i['property_payment_term_id'] = i.pop('payment_term_id')

                part = get_partner(i['dia_ref_customer'], i['name'], i['vat'])

            if part:
                i.pop('name')
                i.pop('street')
                i.pop('zip')
                i.pop('city')
                i.pop('state_id')
                i.pop('country_id')
                i.pop('phone')
            
            new = False

            try:
                if part:
                    part.write(i)
                else:
                    new = PARTNER.new(i)

            except ValidationError as e:
                log_stream.append("ValidationError with partner {}: {}. Popping VAT and Banks, and trying again.".format(ref, e))
                i.pop('vat')
                i.pop('bank_ids', False)

                try:
                    failed_vats.append('"mild","{}","{}","{}","{}"'.format(ref, vat, name, e))
                    if part:
                        part.write(i)
                    else:
                        new = PARTNER.new(i)

                except Exception as e:
                    log_stream.append("[ERR] Exception with partner {}: {}.".format(ref, e))
                    failed_vats.append('"grave","{}","{}","{}","{}"'.format(ref, vat, name, e))
                    self.env.cr.rollback()
                    continue
                    
            except Exception as e:
                log_stream.append("[ERR] Exception with partner {}: {}.".format(ref, e))
                failed_vats.append('"grave","{}","{}","{}","{}"'.format(ref, vat, name, e))
                self.env.cr.rollback()
                continue
            
            if new:
                del(new)
                new = PARTNER.create(i)
                created_partners |= new

            self.env.cr.commit()

        log_stream.append("Created {} partners.".format(len(created_partners)))


        with open("/tmp/log.log", 'w') as file:
            file.write("\n".join(log_stream)) 
        with open("/tmp/vatfailed.csv", 'w') as file:
            file.write("\n".join(failed_vats)) 

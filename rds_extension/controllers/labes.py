# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import json
import base64
import codecs
from odoo import _
from odoo import SUPERUSER_ID
from odoo.addons.portal.controllers.portal import _build_url_w_params
from odoo import modules
from odoo import http
from odoo.http import request
from odoo.http import route
from odoo.tools.mimetypes import guess_mimetype

import werkzeug
from odoo.addons.web.controllers.main import binary_content


class LabelsController(http.Controller):

    @http.route('/labels/', type='http', auth='public')
    def print_labels(self, **kw):
        return http.request.render("rds_extension.lables_main", {})

    @http.route('/labels/print/', type='http', auth='public')
    def do_print(self, **kw):
        for product_product_id in request.env['product.product'].search([("default_code", "=", kw.get('product', ''))]):
            if product_product_id.image_small:
                kw["image_src"] = "data:image/png;base64," + base64.encode(product_product_id.image_small)
                break
        report = http.request.env.ref('rds_extension.ui_report_standard_lables')
        pdf = report.render_qweb_pdf([], data=[kw])[0]
        pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
        return request.make_response(pdf, headers=pdfhttpheaders)

    @http.route('/labels/production/', type='http', auth='public')
    def get_order_search(self, **kw):
        name_search = kw.get('name')
        name_out = []
        for mrp_production in request.env['mrp.production'].sudo().search([('name', 'like', name_search)], limit=50):
            products = []
            products_ids = mrp_production.mold_product_ids.ids
            if mrp_production.product_id.id:
                products_ids.append(mrp_production.product_id.id)
                products_ids = list(set(products_ids))
            products = self.get_products_search(ids=json.dumps(products_ids)).data
            products = json.loads(products.decode('utf-8'))
            name_out.append({'id': mrp_production.id,
                             'value': mrp_production.display_name,
                             'products': products,
                             'customer': mrp_production.customer_id.id})

        return json.dumps(name_out)

    @http.route('/labels/customers/', type='http', auth='public')
    def get_customer_search(self, **kw):
        name_search = kw.get('name')
        name_out = []
        for res_partner in request.env['res.partner'].sudo().search([('name', 'like', name_search)], limit=50):
            name_out.append({'id': res_partner.id,
                             'value': res_partner.display_name})

        return json.dumps(name_out)

    @http.route('/labels/products/', type='http', auth='public')
    def get_products_search(self, **kw):
        name_search = kw.get('name', False)
        if name_search:
            loop_product = request.env['product.product'].sudo().search([('default_code', 'like', name_search)], limit=50)
        ids_search = kw.get('ids', False)
        if ids_search:
            ids_search = json.loads(ids_search)
            loop_product = request.env['product.product'].sudo().search([('id', 'in', ids_search)])
        name_out = []
        for product_product_id in loop_product:
            out_package = []
            for package in product_product_id.packaging_ids:
                out_package.append((package.name, package.qty))
            name_out.append({'id': product_product_id.id,
                             'value': product_product_id.default_code,
                             'name': product_product_id.name,
                             'display_name': product_product_id.display_name,
                             'customer_code': product_product_id.get_customer_ref(),    # FIXME: Fissare passando id cliente
                             'image_url': "/labels/products/image?id=%d" % product_product_id.id,
                             'pakage_qty': out_package,
                             })

        return json.dumps(name_out)

    @http.route('/labels/products/image', type='http', auth='public')
    def get_products_image(self, **kw):
        product_id = kw.get('id', 0)
        status, headers, content = binary_content(model='product.product',
                                                  id=product_id,
                                                  field='image_medium',
                                                  default_mimetype='image/png',
                                                  env=request.env(user=SUPERUSER_ID))
        if not content:
            img_path = modules.get_module_resource('web', 'static/src/img', 'placeholder.png')
            with open(img_path, 'rb') as f:
                image = f.read()
            content = base64.b64encode(image)
        if status == 304:
            return werkzeug.wrappers.Response(status=304)
        image_base64 = base64.b64decode(content)
        headers.append(('Content-Length', len(image_base64)))
        response = request.make_response(image_base64, headers)
        response.status = str(status)
        return response

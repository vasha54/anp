import odoo
import re
import logging
import json

from datetime import datetime, timedelta
from user_agents import parse

from odoo import _, http
from odoo.http import Response, request
from odoo.exceptions import AccessDenied
from odoo.modules.registry import Registry

from ..base_api_controller import BaseAPIController

_logger = logging.getLogger(__name__)


class CatalogAccesorieProductAPIController(BaseAPIController):

    def _get_template_products_format(self,template_products_db):
        #TODO Falta implementar
        pass

    def _get_products_format(self, products_db):
        # --- Obtención correcta del mapeo de selección del campo 'type' ---
        model = request.env['product.product']  # el modelo, no solo el entorno
        field_type = model._fields['type']
        selection = field_type.selection
        if callable(selection):
            # Pasar el modelo (self) a la función de selección
            type_selection = dict(selection(model))
        else:
            type_selection = dict(selection)

        base_url = (
            request.env["ir.config_parameter"].sudo().get_param("web.base.url")
        )
        #
        #  "priority", "points_cost",
        # "points_awarded",
        #
        # "vote_average", "vote_count",
        # Formatear respuesta
        product_data = [{
            'id': p.id,
            'name': p.name,
            'display_name': p.display_name,
            'default_code': p.default_code,
            'list_price': p.list_price,
            'lst_price': p.lst_price,
            'description': p.description or '',
            'sale_ok': p.sale_ok,
            'purchase_ok': p.purchase_ok,
            'type': p.type,
            'type_str': type_selection.get(p.type),
            'uom_id': p.uom_id.id if p.uom_id else None,
            'uom_name': p.uom_id.name if p.uom_id else '',
            'image_1920': True if p.image_1920 else False,
            'image_1920_url': f"{base_url}/public/image/product_accesorie/{p.id}" if p.image_1920 else None,
            'is_favorite': p.is_favorite,
            'product_tags': p.product_tags,
            'tax_string': p.tax_string,
            'standard_price': p.standard_price,
            'taxes': p.taxes,
            'categ': p.categ,
            'barcode': p.barcode,
            'companies': p.companies,
            'attribute_lines': p.attribute_lines,
            'product_tmpl': p.product_tmpl,
            'description_sale': p.description_sale,
            'qty_available': p.qty_available,
            'variant_values': p.variant_values,
            'vote_count': p.vote_count,
            'vote_average': p.vote_average,
        } for p in products_db]

        return product_data

    @http.route('/api_pilates/v1/template_accesories/', type='json', auth='public', methods=['POST'], csrf=False)
    def get_template_accesories_general(self, **kwargs):
        # TODO Falta implementar
        pass

    @http.route('/api_pilates/v1/accesories/', type='json', auth='public', methods=['POST'], csrf=False)
    def get_accesories_general(self, **kwargs):
        try:
            # Obtener datos JSON del cuerpo de la petición
            data = json.loads(request.httprequest.data)
            page = 1
            limit = 80
            if data:
                page = data.get('page', 1)
                limit = data.get('limit', 80)

            # Validar y convertir a enteros
            try:
                page = int(page) if page else 1
                limit = int(limit) if limit else 80
            except ValueError:
                page = 1
                limit = 80

            if page < 1:
                page = 1
            if limit < 1:
                limit = 1

            offset = (page - 1) * limit

            category = request.env.ref('apn_product.cat_accessories', raise_if_not_found=False)
            if not category:
                raise Exception("Accessories category not found")

            domain = [('categ_id', '=', category.id), ('active', '=', True)]
            total_count = request.env['product.product'].sudo().search_count(domain)
            products = request.env['product.product'].sudo().search(domain, limit=limit, offset=offset)

            product_data = self._get_products_format(products)
            total_pages = (total_count + limit - 1) // limit if limit > 0 else 0

            answer = {
                "status": "success",
                "message": _('Data obtained correctly'),
                "data": product_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total_items": total_count,
                    "total_pages": total_pages,
                    "offset": offset,
                }
            }
            return answer

        except Exception as e:
            return self._handle_error(e)

    @http.route('/api_pilates/v1/template_accesories_branch', type='json', auth='public', methods=['POST'], csrf=False)
    def get_template_accesories_branch(self, **kwargs):
        # TODO Falta implementar
        pass

    @http.route('/api_pilates/v1/accesories_branch', type='json', auth='public', methods=['POST'], csrf=False)
    def get_accesories_branch(self, **kwargs):
        try:
            # Obtener datos JSON del cuerpo de la petición
            data = self._get_json_data(request.httprequest.data)
            self._check_existence_parameters(['branch_id'],data)
            page = data.get('page', 1)
            limit = data.get('limit', 80)
            branch_id = data['branch_id']

            # Validar y convertir a enteros
            try:
                page = int(page) if page else 1
                limit = int(limit) if limit else 80
            except ValueError:
                page = 1
                limit = 80

            if page < 1:
                page = 1
            if limit < 1:
                limit = 1

            offset = (page - 1) * limit

            category = request.env.ref('apn_product.cat_accessories', raise_if_not_found=False)
            if not category:
                raise Exception(_("Accessories category not found"))

            branch = request.env['res.company'].search(domain=[('is_branch','=',True),('id','=',branch_id)],limit=1)
            if not branch:
                raise Exception(_("Branch not found or invalid"))

            domain = [('categ_id', '=', category.id), ('active', '=', True),('company_ids', 'in', [branch_id])]
            total_count = request.env['product.product'].sudo().search_count(domain)
            products = request.env['product.product'].sudo().search(domain, limit=limit, offset=offset)

            product_data = self._get_products_format(products)
            total_pages = (total_count + limit - 1) // limit if limit > 0 else 0

            answer = {
                "status": "success",
                "message": _('Data obtained correctly'),
                "data": product_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total_items": total_count,
                    "total_pages": total_pages,
                    "offset": offset,
                }
            }
            return answer

        except Exception as e:
            return self._handle_error(e)
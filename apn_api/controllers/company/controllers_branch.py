import json
import jwt
import logging
import odoo
import re

from datetime import datetime, timedelta
from user_agents import parse

from odoo import _, http
from odoo.http import Response, request
from odoo.exceptions import AccessDenied
from odoo.modules.registry import Registry

from ..base_api_controller import BaseAPIController

_logger = logging.getLogger(__name__)

class BranchAPIController(BaseAPIController):

    @http.route('/api_pilates/v1/nearby_branches', type='json', auth='public', methods=['POST'], csrf=False)
    def get_nearby_branches(self, **kwargs):
        """
        Endpoint público JSON que devuelve las sucursales cercanas a una coordenada.
        Espera un cuerpo JSON con:
            - latitude (float, obligatorio)
            - longitude (float, obligatorio)
            - max_distance (float, opcional)   – distancia máxima en metros
            - page (int, opcional)             – número de página (por defecto la 1)
            - limit (int, opcional)            – elementos por página (por defecto 80)
        Si no se envían page/limit, se devuelven todas las sucursales sin paginar.
        """
        try:
            data = self._get_json_data(request.httprequest.data)
            self._check_existence_parameters(['latitude','longitude'],data)
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            max_distance = data.get('max_distance',None)
            page = data.get('page',1)
            limit = data.get('limit',80)

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
            company_model = request.env['res.company'].sudo()
            all_nearby = company_model.get_nearby_branches( latitude, longitude, max_distance=max_distance)

            total_count = len(all_nearby)

            # Calcular páginas totales
            total_pages = (total_count // limit) + (1 if total_count % limit else 0)

            # Ajustar page si excede el total (devolver la última página posible)
            if page > total_pages and total_pages > 0:
                page = total_pages
                offset = (page - 1) * limit

            # Aplicar paginación a la lista
            paginated_data = all_nearby[offset:offset + limit]

            return {
                "status": "success",
                "message": _('Data obtained successfully.'),
                "data": paginated_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total_items": total_count,
                    "total_pages": total_pages,
                    "offset": offset,
                }
            }
        except Exception as e:
            return self._handle_error(e)

    @http.route('/api_pilates/v1/branches', type='json', auth='public', methods=['POST'], csrf=False)
    def get_branches(self, **kwargs):
        try:
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
            domain = [('active', '=', True), ('is_branch', '=', True)]
            fields = [ "id", "name", "latitude", "longitude", "map_url", "city", "phone", "email", "website", "street",
                        "street2", "state", "zip", "country", "parent_company", "reference", "room_count", "rooms",
                       "schedules", "logo"]

            total_count = request.env["res.company"].sudo().search_count(domain)
            branchs = request.env["res.company"].sudo().search_read( domain, fields=fields, limit=limit, offset=offset)
            total_pages = (total_count + limit - 1) // limit if limit > 0 else 0

            base_url = (
                request.env["ir.config_parameter"].sudo().get_param("web.base.url")
            )
            for branch in branchs:
                if branch.get('logo',False):
                    branch['logo'] = True
                    branch['logo_url'] = f"{base_url}/public/image/branch/{branch['id']}"
                else:
                    branch['logo'] = False
                    branch['logo_url'] = None

            answer = {
                "status": "success",
                "message": _('Data obtained successfully.'),
                "data": branchs,
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

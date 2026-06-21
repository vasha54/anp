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


class UserAPIController(BaseAPIController):

    @http.route('/api_pilates/v1/profile_user', type='json', auth='public', methods=['POST'], csrf=False)
    def get_profile_user(self, **kwargs):
        try:
            token = self._get_token()
            user = self._validate_token(token)  # esto ya verifica expiración, activo, etc.

            data = self._get_json_data(request.httprequest.data)
            self._check_existence_parameters([], data)  # sin parámetros obligatorios

            current_db = request.env.cr.dbname
            registry = Registry(current_db)
            with registry.cursor() as cr:
                env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
                # Leemos los campos necesarios con el id del usuario validado
                user_data = env['res.users'].sudo().search_read(
                    domain=[("id", "=", user.id)],
                    fields=["id", "name", "login", "active", "apn_groups", "email", "mobile", "partner"],
                    limit=1,
                )
                if not user_data:
                    raise AccessDenied(_("User not found."))

            answer = {
                "status": "success",
                "message": "Perfil obtenido exitosamente",
                "data": user_data[0]
            }
            _logger.info(f"Response: {answer}")
            return answer
        except Exception as e:
            return self._handle_error(e)
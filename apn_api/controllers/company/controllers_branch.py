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

    @http.route('/api_pilates/v1/branches', type='http', auth='public', methods=['GET'], csrf=False)
    def get_branches(self, **kwargs):
        try:
            data = (
                request.env["res.company"].sudo().search_read(
                    [('active', '=', True), ('is_branch', '=', True)],
                    [
                        "id",
                        "name",
                        "latitude",
                        "longitude",
                        "map_url",
                        "city",
                        "phone",
                        "email",
                        "website",
                        "street",
                        "street2",
                        "state",
                        "zip",
                        "country",
                        "parent_company",
                        "reference",
                        "room_count",
                        "rooms",
                        "schedules",
                        "logo",
                    ],
                )
            )
            base_url = (
                request.env["ir.config_parameter"].sudo().get_param("web.base.url")
            )
            for branch in data:
                if branch.get('logo',False):
                    branch['logo'] = True
                    branch['logo_url'] = f"{base_url}/public/image/branch/{branch['id']}"
                else:
                    branch['logo'] = False
                    branch['logo_url'] = None

            answer = {
                "status": "success",
                "message": "Datos obtenidos correctamente",
                "data": data,
            }
            return Response(
                json.dumps(answer), headers={"Content-Type": "application/json"}
            )
        except Exception as e:
            return self._handle_error_get(e)

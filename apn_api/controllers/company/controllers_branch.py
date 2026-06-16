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
    def get_branches(self):
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
                    ],
                )
            )
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

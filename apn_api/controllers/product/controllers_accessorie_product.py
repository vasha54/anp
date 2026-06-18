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


class CatalogAccesorieProductAPIController(BaseAPIController):

    @http.route('/api_pilates/v1/accesories', type='http', auth='public', methods=['POST'], csrf=False)
    def get_accesories_general(self, **kwargs):
        pass

    @http.route('/api_pilates/v1/accesories_branch', type='http', auth='public', methods=['POST'], csrf=False)
    def get_accesories_branch(self, **kwargs):
        pass
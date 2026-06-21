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


class CatalogAPIController(BaseAPIController):

    @http.route('/api_pilates/v1/catalog', type='http', auth='public', methods=['POST'], csrf=False)
    def get_catalog_general(self, **kwargs):
        pass

    @http.route('/api_pilates/v1/catalog_branch', type='http', auth='public', methods=['POST'], csrf=False)
    def get_catalog_branch(self, **kwargs):
        pass



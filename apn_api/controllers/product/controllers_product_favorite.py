import odoo
import re
import logging
import json

from datetime import datetime, timedelta
from user_agents import parse

from odoo import _, http
from odoo.http import Response, request
from odoo.exceptions import AccessDenied, ValidationError
from odoo.modules.registry import Registry

from ..base_api_controller import BaseAPIController

_logger = logging.getLogger(__name__)


class ProductFavoriteAPIController(BaseAPIController):

    @http.route('/api_pilates/v1/toggle_favorite_product_template', type='json', auth='public', methods=['POST'],
                csrf=False)
    def toggle_favorite_product_template(self, **kwargs):
        try:
            token = self._get_token()
            user = self._validate_token(token)
            data = self._get_json_data(request.httprequest.data)
            self._check_existence_parameters(['product_template_id'], data)
            product_template_id = int(data['product_template_id'])

            partner = user.partner_id.sudo()
            product = request.env['product.template'].sudo().browse(product_template_id)
            if not product.exists():
                raise ValidationError("Product template not found.")

            if product_template_id in partner.favorite_product_tmpl_ids.ids:
                partner.write({'favorite_product_tmpl_ids': [(3, product_template_id)]})
                is_favorite = False
            else:
                partner.write({'favorite_product_tmpl_ids': [(4, product_template_id)]})
                is_favorite = True

            return {
                "status": "success",
                "message": _("Favorite toggled successfully"),
                "data": {
                    "product_template_id": product_template_id,
                    "is_favorite": is_favorite
                }
            }
        except Exception as e:
            return self._handle_error(e)

    @http.route('/api_pilates/v1/toggle_favorite_product_product', type='json', auth='public', methods=['POST'],
                csrf=False)
    def toggle_favorite_product_product(self, **kwargs):
        try:
            token = self._get_token()
            user = self._validate_token(token)
            data = self._get_json_data(request.httprequest.data)
            self._check_existence_parameters(['product_product_id'], data)
            product_product_id = int(data['product_product_id'])

            partner = user.partner_id.sudo()
            variant = request.env['product.product'].sudo().browse(product_product_id)
            if not variant.exists():
                raise ValidationError("Product variant not found.")

            if product_product_id in partner.favorite_product_ids.ids:
                partner.write({'favorite_product_ids': [(3, product_product_id)]})
                is_favorite = False
            else:
                partner.write({'favorite_product_ids': [(4, product_product_id)]})
                is_favorite = True

            return {
                "status": "success",
                "message": _("Favorite toggled successfully"),
                "data": {
                    "product_product_id": product_product_id,
                    "is_favorite": is_favorite
                }
            }
        except Exception as e:
            return self._handle_error(e)
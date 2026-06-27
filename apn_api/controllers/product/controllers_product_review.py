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


class ReviewProductAPIController(BaseAPIController):

    @http.route('/api_pilates/v1/register_review_product_template', type='json', auth='public', methods=['POST'], csrf=False)
    def register_review_product_template(self, **kwargs):
        try:
            token = self._get_token()
            user = self._validate_token(token)  # esto ya verifica expiración, activo, etc.

            data = self._get_json_data(request.httprequest.data)
            self._check_existence_parameters(['product_template_id','rating'], data)
            product_template_id = int(data['product_template_id'])
            rating_value = float(data['rating'])
            comment = data.get('comment', '')
            if not (0 <= rating_value <= 5):
                raise ValidationError("Rating must be between 0 and 5.")

            ProductTemplate = request.env['product.template'].sudo()
            product = ProductTemplate.browse(product_template_id)

            if not product.exists():
                raise ValidationError(f"Product template with ID {product_template_id} not found.")

            # evitar duplicados del mismo usuario
            existing_rating = request.env['rating.rating'].sudo().search([
                    ('res_model', '=', 'product.template'),
                    ('res_id', '=', product.id),
                    ('partner_id', '=', user.partner_id.id),
                ], limit=1)
            if existing_rating:
                raise ValidationError("You have already submitted a review for this product.")

            Rating = request.env['rating.rating'].sudo()
            rating = Rating.create({
                'res_model': 'product.template',
                'res_id': product.id,
                'rating': rating_value,
                'feedback': comment,
                'consumed': True,
                'partner_id': user.partner_id.id,
            })
            # Asegurar que el res_model se persista
            rating.sudo().write({'res_model': 'product.template'})

            answer = {
                "status": "success",
                "message": _('Data obtained correctly'),
                "data": {
                    'rating_id': rating.id,
                    'rating': rating.rating,
                    'user': {
                        'id': user.id,
                        'name': user.name,
                        'partner_id': user.partner_id.id,  # Mejor enviar solo el ID del partner
                    }
                }
            }
            return answer
        except Exception as e:
            return self._handle_error(e)

    @http.route('/api_pilates/v1/register_review_product_product', type='json', auth='public', methods=['POST'],
                csrf=False)
    def register_review_product_product(self, **kwargs):
        try:
            token = self._get_token()
            user = self._validate_token(token)

            data = self._get_json_data(request.httprequest.data)
            self._check_existence_parameters(['product_product_id', 'rating'], data)

            product_product_id = int(data['product_product_id'])
            rating_value = float(data['rating'])
            comment = data.get('comment', '')

            if not (0 <= rating_value <= 5):
                raise ValidationError("Rating must be between 0 and 5.")

            ProductProduct = request.env['product.product'].sudo()
            product_variant = ProductProduct.browse(product_product_id)

            if not product_variant.exists():
                raise ValidationError(f"Product variant with ID {product_product_id} not found.")

            # evitar duplicados del mismo usuario
            existing_rating = request.env['rating.rating'].sudo().search([
                ('res_model', '=', 'product.product'),
                ('res_id', '=', product.id),
                ('partner_id', '=', user.partner_id.id),
            ], limit=1)
            if existing_rating:
                raise ValidationError("You have already submitted a review for this product.")

            Rating = request.env['rating.rating'].sudo()
            rating = Rating.create({
                'res_model': 'product.product',
                'res_id': product_variant.id,
                'rating': rating_value,
                'feedback': comment,
                'consumed': True,
                'partner_id': user.partner_id.id,
            })
            # Asegurar que el res_model se persista
            rating.sudo().write({'res_model': 'product.product'})

            answer = {
                "status": "success",
                "message": _('Data obtained correctly'),
                "data": {
                    'rating_id': rating.id,
                    'rating': rating.rating,
                    'user': {
                        'id': user.id,
                        'name': user.name,
                        'partner_id': user.partner_id.id,  # Mejor enviar solo el ID del partner
                    }
                }
            }
            return answer
        except Exception as e:
            return self._handle_error(e)


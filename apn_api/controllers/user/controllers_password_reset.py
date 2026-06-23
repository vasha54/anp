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


class PasswordResetAPIController(BaseAPIController):

    @http.route('/api_pilates/v1/change_password', type='json', auth='public', methods=['POST'], csrf=False)
    def change_passwod(self, **kwargs):
        try:
            token = self._get_token()
            user = self._validate_token(token)  # esto ya verifica expiración, activo, etc.

            data = self._get_json_data(request.httprequest.data)
            self._check_existence_parameters(['password','confirmed_password'], data)
            password = data['password']
            confirmed_password = data['confirmed_password']

            if password != confirmed_password:
                raise Exception(_('Passwords do not match'))

            user._validate_password_security(password)
            user.sudo().write({
                'password': password,
                'confirmed_password': confirmed_password,
            })
            return {
                'success': True,
                'message': _('Password has been changed successfully.'),
                'data': {
                    'user': {
                        'id': user.id,
                        'name': user.name,
                        'login': user.login,
                    }
                }
            }

        except Exception as e:
            return self._handle_error(e)

    @http.route('/api_pilates/v1/password_reset_request', type='json', auth='public', methods=['POST'], csrf=False)
    def request_password_reset(self, **kwargs):
        """Service 1: Request a password reset code."""
        try:
            data = self._get_json_data(request.httprequest.data)
            # Validar parámetros requeridos
            self._check_existence_parameters(['email'], data)
            email = data['email'].strip().lower()
            user = request.env['res.users'].sudo().search([('email', '=', email)], limit=1)
            if not user:
                raise Exception(_('No user was found with that email address'))
            token, code = user.generate_password_reset_token()
            user.write({
                'password_reset_ip': request.httprequest.remote_addr,
                'password_reset_user_agent': request.httprequest.headers.get('User-Agent', ''),
            })
            user._send_reset_code_email()
            return {
                'success': True,
                'message': _('If the email is registered, a reset code has been sent.'),
                'data':{
                    'user':{
                        'email': user.email,
                        'id': user.id,
                        'name': user.name,
                    }
                }
            }
        except Exception as e:
            return self._handle_error(e)

    @http.route('/api_pilates/v1/password_reset_confirm', type='json', auth='public', methods=['POST'], csrf=False)
    def confirm_password_reset(self, **kwargs):
        """Service 2: Confirm password reset with code and new password."""
        try:
            data = self._get_json_data(request.httprequest.data)
            # Validar parámetros requeridos
            self._check_existence_parameters(['email','code','new_password'], data)
            email = data['email']
            code = data['code']
            new_password = data['new_password']
            email = email.strip().lower()
            user = request.env['res.users'].sudo().search([('email', '=', email)], limit=1)
            if not user:
                raise Exception(_('No user was found with that email address'))
            user.verify_reset_code(code)
            user.reset_password(new_password, code=code)
            return {
                'success': True,
                'message': 'Password has been changed successfully.',
                'data': {
                    'user': {
                        'email': user.email,
                        'id': user.id,
                        'name': user.name,
                    }
                }
            }
        except Exception as e:
            return self._handle_error(e)
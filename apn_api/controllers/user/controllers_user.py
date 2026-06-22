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

    def _is_valid_email(self, email):
        """Valida formato de email"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def _is_strong_password(self, password):
        """Valida que la contraseña sea segura"""
        import re
        if len(password) < 8:
            return False
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'[a-z]', password):
            return False
        if not re.search(r'\d', password):
            return False
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False
        return True

    

    @http.route("/api_pilates/v1/account_activate_email", type='json', auth="none", methods=['POST'], csrf=False)
    def activate_account(self, **post):
        """
        Activa la cuenta del usuario mediante token

        Parámetros requeridos:
        - email: Correo electrónico del usuario
        - token: Token de activación recibido por email
        """
        try:
            data = self._get_json_data(request.httprequest.data)

            # Validar parámetros requeridos
            self._check_existence_parameters(['email', 'token'], data)

            email = data['email'].strip().lower()
            token = data['token'].strip()
            # Buscar usuario por email
            user = request.env['res.users'].sudo().with_context(active_test=False).search([('email', '=', email)], limit=1)
            if not user:
                raise Exception(_('No account found with this email.'))
            user.action_activate_account(token)
            return {
                'status': 'success',
                'message': _('Account activated successfully. You can now log in.'),
                'data': {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'is_activated': True
                }
            }
        except Exception as e:
            return self._handle_error(e)

    @http.route("/api_pilates/v1/register_client_by_email", type='json', auth="none", methods=['POST'], csrf=False)
    def register_client_by_email(self, **post):
        """
            Registro público de usuarios (clientes) con envío de email de activación

            Parámetros requeridos:
            - email: Correo electrónico del usuario
            - password: Contraseña del usuario
            - confirmed_password: Contraseña de confirmación del usuario
            - name: Nombre completo del usuario

            Parámetros opcionales:
            - login: Nombre de usuario (si no se proporciona, se usa el email)
            - mobile: Teléfono móvil del usuario
        """
        try:
            # Asegurar un usuario válido en el entorno (para evitar errores en sudo(False))
            if not request.env.user:
                request.env = request.env(user=1)  # Superusuario

            # Obtener datos del JSON
            data = self._get_json_data(request.httprequest.data)

            # Validar parámetros requeridos
            self._check_existence_parameters(['email', 'password', 'confirmed_password', 'name'], data)

            email = data['email'].strip().lower()
            password = data['password']
            confirmed_password = data['confirmed_password']
            name = data['name'].strip()
            login = data.get('login', email)  # Si no se proporciona login, usar email
            mobile = data.get('mobile')

            if not self._is_valid_email(email):
                raise Exception(_('Invalid email format.'))

            if not self._is_strong_password(password):
                raise Exception(_('Password must be at least 8 characters long and contain '
                        'uppercase, lowercase, numbers and special characters.'))

            # Verificar si el email ya está registrado
            existing_user = request.env['res.users'].sudo().with_context(active_test=False).search([
                ('login', '=', login)
            ], limit=1)
            if existing_user:
                if existing_user.is_account_activated:
                    raise Exception(_('A user with this email already exists.'))
                else:
                    # Reenviar email de activación para usuario existente no activado
                    existing_user.action_resend_activation_email()
                    return {
                        'status': 'success',
                        'message': _(
                            'An account with this email already exists but is not activated. '
                            'A new activation email has been sent.'
                        ),
                        'data':{
                            'id': existing_user.id,
                            'name': existing_user.name,
                            'login': existing_user.login,
                        }
                    }
            else:
                default_group = request.env.ref('apn_group.group_client', raise_if_not_found=False)
                if not default_group:
                    raise Exception(_('The client group is not configured. Contact the administrator.'))

                company = request.env['res.company'].sudo().search([], limit=1)
                branchs = request.env['res.company'].sudo().search(domain=[('is_branch','=',True)])

                id_branchs = [company.id]
                id_branch = company.id

                if branchs:
                    id_branchs = branchs.mapped('id')
                    id_branch = id_branchs[0]

                if not company:
                    raise Exception(_("No company was found in the system."))

                user_vals = {
                    'name': name,
                    'login': login,
                    'email': email,
                    'password': password,
                    'confirmed_password': confirmed_password,
                    'is_user_apn':True,
                    'apn_group_ids':[(6, 0, [default_group.id])] if default_group else [(6, 0, [])],
                    'company_id': id_branch,
                    'company_ids': [(6, 0, id_branchs)],
                    'mobile': mobile if mobile else False,

                }
                context_data = {
                    'email_registration': True,
                }
                users = request.env['res.users'].with_context(**context_data).sudo().create(user_vals)

                for user in users:
                    user.action_send_activation_email()

                response = {
                    'status': 'success',
                    'message': _(
                        'Registration successful. Please check your email to activate your account.'
                    ),
                    'data': {
                        'id': user.id,
                        'name': user.name,
                        'email': user.email,
                        'is_activated': user.is_account_activated,
                        'activation_email_sent': True
                    },
                }
                return response

        except Exception as e:
            return self._handle_error(e)

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
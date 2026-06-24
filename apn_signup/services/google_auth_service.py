import logging
import requests
import secrets
import string
from datetime import datetime, timedelta
from odoo import _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class GoogleAuthService:
    """Servicio para manejar autenticación Google OAuth2"""
    GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
    GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v3/userinfo'
    GOOGLE_TOKENINFO_URL = 'https://oauth2.googleapis.com/tokeninfo'

    def __init__(self, env):
        self.env = env
        self.config = env['google.oauth2.config'].get_config()

    def verify_google_token(self, id_token=None, access_token=None):
        """
        Verifica un token de Google y obtiene información del usuario
        Args:
            id_token: ID Token de Google (para autenticación móvil)
            access_token: Access Token de Google
        Returns:
            dict: Información del usuario de Google
        """
        google_data = None

        if id_token:
            google_data = self._verify_id_token(id_token)
        elif access_token:
            google_data = self._verify_access_token(access_token)
        else:
            raise ValidationError(_('No token provided. Provide id_token or access_token.'))

        if not google_data:
            raise ValidationError(_('Invalid Google token.'))

        # Verificar dominio si está configurado
        if not self.config.is_domain_allowed(google_data.get('email')):
            raise ValidationError(
                _('Email domain not allowed: %s') % google_data.get('email')
            )

        return google_data

    def _verify_id_token(self, id_token):
        """
        Verifica un ID Token de Google
        Args:
            id_token: ID Token JWT de Google
        Returns:
            dict: Información del usuario
        """
        try:
            # Verificar token con Google
            response = requests.get(
                self.GOOGLE_TOKENINFO_URL,
                params={'id_token': id_token}
            )

            if response.status_code != 200:
                _logger.error(f"Invalid ID token: {response.text}")
                return None

            token_info = response.json()

            # Verificar audiencia
            if token_info.get('aud') != self.config.client_id:
                _logger.error("Token audience mismatch")
                return None

            # Verificar expiración
            if token_info.get('exp', 0) < datetime.now().timestamp():
                _logger.error("Token expired")
                return None

            # Obtener información del usuario
            user_info = self._get_user_info(access_token=None, id_token=id_token)

            return {
                'google_id': token_info.get('sub'),
                'email': token_info.get('email'),
                'name': user_info.get('name', ''),
                'picture': user_info.get('picture', ''),
                'verified_email': token_info.get('email_verified', False),
            }

        except Exception as e:
            _logger.error(f"Error verifying ID token: {str(e)}")
            return None

    def _verify_access_token(self, access_token):
        """
        Verifica un Access Token de Google
        Args:
            access_token: Access Token de Google
        Returns:
            dict: Información del usuario
        """
        try:
            user_info = self._get_user_info(access_token=access_token)

            if not user_info:
                return None

            # Verificar token info
            response = requests.get(
                self.GOOGLE_TOKENINFO_URL,
                params={'access_token': access_token}
            )

            token_info = response.json() if response.status_code == 200 else {}

            return {
                'google_id': user_info.get('sub') or token_info.get('sub'),
                'email': user_info.get('email'),
                'name': user_info.get('name', ''),
                'picture': user_info.get('picture', ''),
                'verified_email': user_info.get('email_verified', False),
            }

        except Exception as e:
            _logger.error(f"Error verifying access token: {str(e)}")
            return None

    def _get_user_info(self, access_token=None, id_token=None):
        """
        Obtiene información del usuario de Google
        Args:
            access_token: Access Token
            id_token: ID Token
        Returns:
            dict: Información del usuario
        """
        try:
            headers = {}

            if access_token:
                headers['Authorization'] = f'Bearer {access_token}'
            elif id_token:
                params = {'id_token': id_token}
                response = requests.get(
                    self.GOOGLE_USERINFO_URL,
                    params=params
                )
                return response.json() if response.status_code == 200 else None

            response = requests.get(
                self.GOOGLE_USERINFO_URL,
                headers=headers
            )

            return response.json() if response.status_code == 200 else None

        except Exception as e:
            _logger.error(f"Error getting user info: {str(e)}")
            return None

    def exchange_authorization_code(self, code, redirect_uri=None):
        """
        Intercambia un código de autorización por tokens
        Args:
            code: Código de autorización
            redirect_uri: URI de redirección
        Returns:
            dict: Tokens de acceso y refresh
        """
        try:
            response = requests.post(
                self.GOOGLE_TOKEN_URL,
                data={
                    'code': code,
                    'client_id': self.config.client_id,
                    'client_secret': self.config.client_secret,
                    'redirect_uri': redirect_uri or self.config.redirect_uri,
                    'grant_type': 'authorization_code',
                }
            )

            if response.status_code == 200:
                return response.json()
            else:
                _logger.error(f"Failed to exchange code: {response.text}")
                return None

        except Exception as e:
            _logger.error(f"Error exchanging code: {str(e)}")
            return None

    def create_user(self, google_data):
        """
        Crea un usuario basado en datos de Google
        Args:
            google_data: Datos del usuario de Google
        Returns:
            res.users: Usuario creado
        """
        User = self.env['res.users'].sudo()

        # Buscar usuario por Google ID
        user = User.search([('google_id', '=', google_data.get('google_id'))], limit=1)

        if user:
            # Actualizar tokens
            user.write({
                'google_access_token': google_data.get('access_token'),
                'google_refresh_token': google_data.get('refresh_token'),
                'google_token_expiration': google_data.get('token_expiration'),
                'google_profile_picture': google_data.get('picture'),
            })
            return user

        # Buscar usuario por email
        email = google_data.get('email')
        user = User.search([('login', '=', email)], limit=1)

        if user:
            # Vincular Google account
            user.link_google_account(google_data)
            return user

        # Crear nuevo usuario
        user = self._create_user_from_google(google_data)
        return user


    def _create_user_from_google(self, google_data):
        """
        Crea un nuevo usuario desde datos de Google
        Args:
            google_data: Datos del usuario de Google
        Returns:
            res.users: Nuevo usuario creado
        """
        User = self.env['res.users'].sudo()

        default_group = self.env.ref('apn_group.group_client', raise_if_not_found=False)
        if not default_group:
            raise Exception(_('The client group is not configured. Contact the administrator.'))

        company = self.env['res.company'].sudo().search([], limit=1)
        branchs = self.env['res.company'].sudo().search(domain=[('is_branch', '=', True)])

        id_branchs = [company.id]
        id_branch = company.id

        if branchs:
            id_branchs = branchs.mapped('id')
            id_branch = id_branchs[0]

        if not company:
            raise Exception(_("No company was found in the system."))

        password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))

        # Preparar valores del usuario
        user_vals = {
            'name': google_data.get('name', 'Google User'),
            'login': google_data.get('email'),
            'email': google_data.get('email'),
            'google_id': google_data.get('google_id'),
            'google_email': google_data.get('email'),
            'google_profile_picture': google_data.get('picture'),
            'google_access_token': google_data.get('access_token'),
            'google_refresh_token': google_data.get('refresh_token'),
            'google_token_expiration': google_data.get('token_expiration'),
            'auth_provider': 'google',
            'is_account_activated': True,  # Google accounts are pre-verified
            'active': True,
            'is_user_apn': True,
            'apn_group_ids': [(6, 0, [default_group.id])] if default_group else [(6, 0, [])],
            'company_id': id_branch,
            'company_ids': [(6, 0, id_branchs)],
            'password': password,
            'confirmed_password': confirmed_password,
        }

        # Crear usuario
        user = User.create(user_vals)
        _logger.info(f"User created from Google: {user.email}")
        return user
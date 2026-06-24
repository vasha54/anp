from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import uuid
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    google_id = fields.Char(
        string='Google ID',
        copy=False,
        help='Google account ID for OAuth2 authentication'
    )
    google_email = fields.Char(
        string='Google Email',
        copy=False,
        help='Email associated with Google account'
    )
    google_profile_picture = fields.Char(
        string='Google Profile Picture',
        copy=False,
        help='URL of Google profile picture'
    )
    google_access_token = fields.Char(
        string='Google Access Token',
        copy=False,
        help='Google OAuth2 access token'
    )
    google_refresh_token = fields.Char(
        string='Google Refresh Token',
        copy=False,
        help='Google OAuth2 refresh token'
    )
    google_token_expiration = fields.Datetime(
        string='Google Token Expiration',
        copy=False,
        help='Expiration date of Google access token'
    )
    auth_provider = fields.Selection([
        ('local', 'Local'),
        ('google', 'Google'),
        ('apple', 'Apple'),
        ('facebook', 'Facebook'),
    ], string='Authentication Provider', default='local')
    is_google_linked = fields.Boolean(
        string='Google Account Linked',
        compute='_compute_is_google_linked',
        store=True
    )

    @api.depends('google_id')
    def _compute_is_google_linked(self):
        for user in self:
            user.is_google_linked = bool(user.google_id)

    def link_google_account(self, google_data):
        """
        Vincula una cuenta de Google al usuario existente
        Args:
            google_data: Diccionario con datos de Google
        """
        self.ensure_one()
        # Verificar que el Google ID no esté vinculado a otro usuario
        existing_user = self.search([
            ('google_id', '=', google_data.get('google_id')),
            ('id', '!=', self.id)
        ], limit=1)

        if existing_user:
            raise ValidationError(
                _('This Google account is already linked to another user.')
            )

        self.write({
            'google_id': google_data.get('google_id'),
            'google_email': google_data.get('email'),
            'google_profile_picture': google_data.get('picture'),
            'google_access_token': google_data.get('access_token'),
            'google_refresh_token': google_data.get('refresh_token'),
            'google_token_expiration': google_data.get('token_expiration'),
            'auth_provider': 'google',
        })
        _logger.info(f"Google account linked to user {self.email}")
        return True

    def unlink_google_account(self):
        """Desvincula la cuenta de Google del usuario"""
        self.ensure_one()
        # No permitir desvincular si es el único método de autenticación
        if self.auth_provider == 'google' and not self.password:
            raise ValidationError(
                _('Cannot unlink Google account. Set a password first.')
            )
        self.write({
            'google_id': False,
            'google_email': False,
            'google_profile_picture': False,
            'google_access_token': False,
            'google_refresh_token': False,
            'google_token_expiration': False,
            'auth_provider': 'local' if self.auth_provider == 'google' else self.auth_provider,
        })
        _logger.info(f"Google account unlinked from user {self.email}")
        return True

    def refresh_google_token(self):
        """
        Refresca el token de acceso de Google

        Returns:
            str: Nuevo token de acceso
        """
        self.ensure_one()

        if not self.google_refresh_token:
            raise ValidationError(_('No refresh token available.'))

        config = self.env['google.oauth2.config'].get_config()

        try:
            response = requests.post(
                'https://oauth2.googleapis.com/token',
                data={
                    'client_id': config.client_id,
                    'client_secret': config.client_secret,
                    'refresh_token': self.google_refresh_token,
                    'grant_type': 'refresh_token',
                }
            )

            if response.status_code == 200:
                token_data = response.json()
                self.write({
                    'google_access_token': token_data.get('access_token'),
                    'google_token_expiration': datetime.now() + timedelta(
                        seconds=token_data.get('expires_in', 3600)
                    ),
                })
                return token_data.get('access_token')
            else:
                _logger.error(f"Failed to refresh Google token: {response.text}")
                raise ValidationError(_('Failed to refresh Google token.'))

        except Exception as e:
            _logger.error(f"Error refreshing Google token: {str(e)}")
            raise ValidationError(_('Error refreshing Google token.'))
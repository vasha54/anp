import logging
import secrets
import re
import uuid

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError, AccessDenied
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class GoogleOAuth2Config(models.Model):
    _name = 'google.oauth2.config'
    _description = 'Google OAuth2 Configuration'

    name = fields.Char(string='Name', default='Google OAuth2 Config')
    client_id = fields.Char(string='Client ID', required=True)
    client_secret = fields.Char(string='Client Secret', required=True)
    redirect_uri = fields.Char(string='Redirect URI')
    active = fields.Boolean(string='Active', default=True)

    # Configuración adicional
    allowed_domains = fields.Text(
        string='Allowed Domains',
        help='Lista de dominios permitidos (uno por línea). Dejar vacío para permitir todos.'
    )
    auto_create_user = fields.Boolean(
        string='Auto Create User',
        default=True,
        help='Automatically create user if not exists'
    )
    default_group_id = fields.Many2one(
        'res.groups',
        string='Default Group for New Users',
        help='Group assigned to users created via Google login'
    )

    @api.model
    def get_config(self):
        """Obtiene la configuración activa"""
        config = self.search([('active', '=', True)], limit=1)
        if not config:
            raise ValidationError(_('Google OAuth2 is not configured.'))
        return config

    def is_domain_allowed(self, email):
        """
        Verifica si el dominio del email está permitido

        Args:
            email: Email a verificar

        Returns:
            bool: True si el dominio está permitido
        """
        self.ensure_one()

        if not self.allowed_domains:
            return True

        domain = email.split('@')[1].lower()
        allowed_domains = [d.strip().lower() for d in self.allowed_domains.split('\n') if d.strip()]

        return domain in allowed_domains
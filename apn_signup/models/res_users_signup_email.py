from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import uuid
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    activation_token = fields.Char(
        string='Activation Token',
        copy=False,
        help='Token sent by email for account activation'
    )
    activation_token_expiration = fields.Datetime(
        string='Activation Token Expiration',
        copy=False,
        help='Expiration date for the activation token'
    )
    is_account_activated = fields.Boolean(
        string='Account Activated',
        default=False,
        help='Indicates if the user has activated their account via email'
    )
    email_activation_sent = fields.Boolean(
        string='Activation Email Sent',
        default=False,
        help='Indicates if the activation email has been sent'
    )
    registration_date = fields.Datetime(
        string='Registration Date',
        default=fields.Datetime.now,
        readonly=True
    )
    last_activation_attempt = fields.Datetime(
        string='Last Activation Attempt',
        readonly=True
    )
    activation_attempts = fields.Integer(
        string='Activation Attempts',
        default=0,
        readonly=True
    )

    @api.model
    def create(self, vals):
        """Override create to handle user registration"""
        # # Leer la bandera desde el contexto, NO desde vals
        if self.env.context.get('email_registration'):
            # vals['active'] = False
            vals['is_account_activated'] = False
            vals['activation_token'] = self._generate_activation_token()
            vals['activation_token_expiration'] = self._get_activation_expiration()
        records = super().create(vals)
        if self.env.context.get('email_registration'):
            for rec in records:
                rec.write({'active': False})
        return records

    def _generate_activation_token(self):
        """Genera un token único para activación de cuenta"""
        return str(uuid.uuid4())

    def _get_activation_expiration(self):
        """Obtiene la fecha de expiración del token de activación"""
        hours = int(self.env['ir.config_parameter'].sudo().get_param(
            'auth.activation_token_expiration_hours', 48
        ))
        return datetime.now() + timedelta(hours=hours)

    def _is_token_expired(self):
        """Verifica si el token de activación ha expirado"""
        self.ensure_one()
        if not self.activation_token_expiration:
            return True
        return fields.Datetime.now() > self.activation_token_expiration

    def action_send_activation_email(self):
        """Envía el correo de activación al usuario"""
        self.ensure_one()

        if self.is_account_activated:
            raise UserError(_('Account is already activated.'))

        # Generar nuevo token si no existe o expiró
        if not self.activation_token or self._is_token_expired():
            self.write({
                'activation_token': self._generate_activation_token(),
                'activation_token_expiration': self._get_activation_expiration()
            })

        # Enviar email
        template = self.env.ref('apn_signup.email_template_user_activation', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)
            self.write({
                'email_activation_sent': True
            })
            _logger.info(f"Activation email sent to user {self.email}")
        else:
            raise UserError(_('Activation email template not found.'))

    def _is_token_expired(self):
        """Verifica si el token de activación ha expirado"""
        self.ensure_one()
        if not self.activation_token_expiration:
            return True
        return fields.Datetime.now() > self.activation_token_expiration

    def action_activate_account(self, token):
        """
        Activa la cuenta del usuario mediante token
        Args:
            token: Token de activación recibido por email
        Returns:
            bool: True si la activación fue exitosa
        Raises:
            ValidationError: Si el token es inválido o expiró
        """
        self.ensure_one()
        # Incrementar contador de intentos
        self.write({
            'activation_attempts': self.activation_attempts + 1,
            'last_activation_attempt': fields.Datetime.now()
        })
        # Validaciones
        if self.is_account_activated:
            raise ValidationError(_('Account is already activated.'))
        if not self.activation_token:
            raise ValidationError(_('No activation token found. Please request a new activation email.'))
        if self._is_token_expired():
            raise ValidationError(_('Activation token has expired. Please request a new activation email.'))
        if self.activation_token != token:
            raise ValidationError(_('Invalid activation token.'))
        # Activar cuenta
        self.write({
            'active': True,
            'is_account_activated': True,
            'activation_token': False,  # Limpiar token usado
            'activation_token_expiration': False
        })
        _logger.info(f"Account activated for user {self.email}")
        return True

    def action_resend_activation_email(self):
        """Reenvía el correo de activación"""
        self.ensure_one()

        if self.is_account_activated:
            raise UserError(_('Account is already activated.'))
        # Limpiar token anterior y generar uno nuevo
        self.write({
            'activation_token': self._generate_activation_token(),
            'activation_token_expiration': self._get_activation_expiration(),
            'activation_attempts': 0
        })
        # Enviar email
        template = self.env.ref('apn_signup.email_template_user_activation', raise_if_not_found=False)
        if not template:
            raise UserError(_('Activation email template not found.'))

            # Obtener URL base y construir el enlace
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        activation_url = f"{base_url}/api_pilates/v1/account_activate_email?email={self.email}&token={self.activation_token}"

        # Enviar el correo pasando el enlace como contexto adicional
        template.with_context(activation_url=activation_url).send_mail(
            self.id,
            force_send=True,
        )
        self.write({'email_activation_sent': True})
        _logger.info("Activation email resent to user %s", self.email)

    @api.model
    def _clean_expired_email_activations(self):
        """
        Limpia usuarios que no activaron su cuenta en el tiempo establecido
        Puede ser ejecutado por un cron job
        """
        expiration_date = fields.Datetime.now() - timedelta(days=7)
        expired_users = self.search([
            ('is_account_activated', '=', False),
            ('create_date', '<', expiration_date),
            ('activation_token', '!=', False)
        ])

        count = len(expired_users)
        if count > 0:
            _logger.info(f"Cleaning {count} expired unactivated accounts")
            expired_users.unlink()

        return count
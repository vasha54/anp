import logging
import secrets
import re
import uuid

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import AccessDenied

from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'

    # Campos para recuperación de contraseña
    password_reset_token = fields.Char(
        string='Password Reset Token',
        copy=False,
        help='Token for password reset'
    )
    password_reset_token_expiration = fields.Datetime(
        string='Token Expiration',
        copy=False,
        help='Expiration date for password reset token'
    )
    password_reset_code = fields.Char(
        string='Reset Code (6 digits)',
        copy=False,
        help='6-digit code for password reset'
    )
    password_reset_code_expiration = fields.Datetime(
        string='Code Expiration',
        copy=False,
        help='Expiration date for reset code'
    )
    password_reset_attempts = fields.Integer(
        string='Reset Attempts',
        default=0,
        help='Number of password reset attempts'
    )
    last_password_reset = fields.Datetime(
        string='Last Password Reset',
        readonly=True,
        help='Date of last successful password reset'
    )
    password_reset_ip = fields.Char(
        string='Reset Request IP',
        readonly=True,
        help='IP address from which reset was requested'
    )
    password_reset_user_agent = fields.Char(
        string='Reset Request User Agent',
        readonly=True,
        help='User agent from which reset was requested'
    )
    # Campos para bloqueo de cuenta por fuerza bruta
    failed_reset_attempts = fields.Integer(
        string='Failed Reset Attempts',
        default=0,
        help='Number of failed password reset attempts'
    )
    locked_until = fields.Datetime(
        string='Locked Until',
        help='Account locked until this date due to multiple failed attempts'
    )
    is_reset_locked = fields.Boolean(
        string='Reset Locked',
        compute='_compute_is_reset_locked',
        store=True
    )

    @api.depends('locked_until')
    def _compute_is_reset_locked(self):
        for user in self:
            if user.locked_until and user.locked_until > fields.Datetime.now():
                user.is_reset_locked = True
            else:
                user.is_reset_locked = False
                if user.locked_until:
                    user.locked_until = False

    def generate_password_reset_token(self):
        """
        Genera un token seguro para reseteo de contraseña

        Returns:
            str: Token generado
        """
        self.ensure_one()

        # Verificar bloqueo
        if self.is_reset_locked:
            remaining = self.locked_until - fields.Datetime.now()
            minutes = int(remaining.total_seconds() / 60)
            raise ValidationError(
                _('Account is temporarily locked. Try again in %(minutes)d minutes.',
                  minutes=minutes)
            )

        # Generar token seguro (32 bytes = 64 caracteres hex)
        token = secrets.token_hex(32)

        # Generar código de 6 dígitos
        code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])

        # Configurar expiración
        expiration_minutes = int(self.env['ir.config_parameter'].sudo().get_param(
            'auth.password_reset_expiration_minutes', 30
        ))
        expiration = fields.Datetime.now() + timedelta(minutes=expiration_minutes)

        # Guardar token y código
        self.write({
            'password_reset_token': token,
            'password_reset_token_expiration': expiration,
            'password_reset_code': code,
            'password_reset_code_expiration': expiration,
            'password_reset_attempts': 0,
            'failed_reset_attempts': 0,
            'locked_until': False,
        })

        return token, code

    def verify_reset_token(self, token):
        """
        Verifica el token de reseteo de contraseña
        Args:
            token: Token a verificar
        Returns:
            bool: True si el token es válido
        """
        self.ensure_one()

        # Verificar bloqueo
        if self.is_reset_locked:
            remaining = self.locked_until - fields.Datetime.now()
            minutes = int(remaining.total_seconds() / 60)
            raise AccessDenied(
                _('Account is temporarily locked. Try again in %(minutes)d minutes.',
                  minutes=minutes)
            )
        # Verificar token
        if not self.password_reset_token:
            self._increment_failed_attempts()
            raise ValidationError(_('No password reset has been requested.'))

        if self._is_reset_token_expired():
            self._increment_failed_attempts()
            raise ValidationError(_('Reset token has expired. Please request a new one.'))

        # Usar comparación segura para prevenir timing attacks
        if not secrets.compare_digest(self.password_reset_token, token):
            self._increment_failed_attempts()
            raise ValidationError(_('Invalid reset token.'))

        return True

    def verify_reset_code(self, code):
        """
        Verifica el código de 6 dígitos para reseteo
        Args:
            code: Código de 6 dígitos
        Returns:
            bool: True si el código es válido
        """
        self.ensure_one()
        if self.is_reset_locked:
            raise AccessDenied(_('Account is temporarily locked.'))

        if not self.password_reset_code:
            self._increment_failed_attempts()
            raise ValidationError(_('No password reset has been requested.'))

        if self._is_reset_code_expired():
            self._increment_failed_attempts()
            raise ValidationError(_('Reset code has expired. Please request a new one.'))

        if self.password_reset_attempts >= 3:
            self._lock_account()
            raise AccessDenied(_('Too many attempts. Account locked for 30 minutes.'))

        if code != self.password_reset_code:
            self.write({
                'password_reset_attempts': self.password_reset_attempts + 1
            })
            remaining = 3 - (self.password_reset_attempts + 1)
            raise ValidationError(
                _('Invalid code. %(remaining)d attempts remaining.', remaining=remaining)
            )

        return True

    def reset_password(self, new_password, token=None, code=None):
        """
        Resetea la contraseña del usuario
        Args:
            new_password: Nueva contraseña
            token: Token de reseteo (opcional)
            code: Código de reseteo (opcional)
        Returns:
            bool: True si el reseteo fue exitoso
        """
        self.ensure_one()

        # Verificar token o código
        if token:
            self.verify_reset_token(token)
        elif code:
            self.verify_reset_code(code)
        else:
            raise ValidationError(_('Reset token or code is required.'))

        # Validar nueva contraseña
        self._validate_password_strength(new_password)

        # Verificar que no sea igual a contraseñas anteriores
        if self._is_password_previously_used(new_password):
            raise ValidationError(
                _('This password has been used recently. Please choose a different password.')
            )

        # Capturar hash actual antes de cambiar
        old_hash = self.password

        # Cambiar contraseña
        self.sudo().write({
            'password': new_password,
            'password_reset_token': False,
            'password_reset_token_expiration': False,
            'password_reset_code': False,
            'password_reset_code_expiration': False,
            'password_reset_attempts': 0,
            'failed_reset_attempts': 0,
            'locked_until': False,
            'last_password_reset': fields.Datetime.now(),
        })
        # Registrar en historial
        self.env['password.reset.history'].sudo().create({
            'user_id': self.id,
            'reset_date': fields.Datetime.now(),
            'ip_address': self.password_reset_ip,
            'user_agent': self.password_reset_user_agent,
            'successful': True,
            'old_password_hash': old_hash,
        })

        # Enviar notificación de cambio de contraseña
        self._send_password_changed_notification()
        _logger.info(f"Password reset successful for user {self.email}")
        return True

    def _is_reset_token_expired(self):
        """Verifica si el token de reseteo ha expirado"""
        self.ensure_one()
        if not self.password_reset_token_expiration:
            return True
        return fields.Datetime.now() > self.password_reset_token_expiration

    def _is_reset_code_expired(self):
        """Verifica si el código de reseteo ha expirado"""
        self.ensure_one()
        if not self.password_reset_code_expiration:
            return True
        return fields.Datetime.now() > self.password_reset_code_expiration

    def _increment_failed_attempts(self):
        """Incrementa el contador de intentos fallidos"""
        self.ensure_one()
        max_attempts = int(self.env['ir.config_parameter'].sudo().get_param(
            'auth.max_reset_attempts', 5
        ))

        self.write({
            'failed_reset_attempts': self.failed_reset_attempts + 1
        })

        if self.failed_reset_attempts >= max_attempts:
            self._lock_account()

    def _lock_account(self):
        """Bloquea la cuenta temporalmente"""
        self.ensure_one()
        lock_minutes = int(self.env['ir.config_parameter'].sudo().get_param(
            'auth.reset_lock_minutes', 30
        ))

        self.write({
            'locked_until': fields.Datetime.now() + timedelta(minutes=lock_minutes),
            'failed_reset_attempts': 0,
        })

        _logger.warning(f"Account locked for password reset: {self.email}")

    def _validate_password_strength(self, password):
        """Valida la fortaleza de la contraseña"""
        min_length = int(self.env['ir.config_parameter'].sudo().get_param(
            'auth.min_password_length', 8
        ))

        if len(password) < min_length:
            raise ValidationError(
                _('Password must be at least %(length)d characters long.', length=min_length)
            )

        if not re.search(r'[A-Z]', password):
            raise ValidationError(_('Password must contain at least one uppercase letter.'))

        if not re.search(r'[a-z]', password):
            raise ValidationError(_('Password must contain at least one lowercase letter.'))

        if not re.search(r'\d', password):
            raise ValidationError(_('Password must contain at least one number.'))

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(_('Password must contain at least one special character.'))

    def _is_password_previously_used(self, new_password):
        """
        Verifica si la contraseña ha sido usada anteriormente
        Returns:
            bool: True si la contraseña ya fue usada
        """
        self.ensure_one()

        # Obtener historial de contraseñas
        history_count = int(self.env['ir.config_parameter'].sudo().get_param('auth.password_history_count', 5))

        recent_passwords = self.env['password.reset.history'].sudo().search([
            ('user_id', '=', self.id),
            ('successful', '=', True),
        ], limit=history_count, order='reset_date desc')

        for record in recent_passwords:
            if record.old_password_hash and self._verify_password_hash(new_password, record.old_password_hash):
                return True
        return False

    def _send_password_changed_notification(self):
        """Envía notificación de cambio de contraseña exitoso"""
        self.ensure_one()

        template = self.env.ref('apn_signup.email_template_password_changed', raise_if_not_found=False)
        if template:
            try:
                template.send_mail(self.id, force_send=True)
                _logger.info(f"Password change notification sent to {self.email}")
            except Exception as e:
                _logger.error(f"Failed to send password change notification: {str(e)}")

    def _verify_password_hash(self, password, pwd_hash):
        """Verifica si la contraseña corresponde al hash dado."""
        self.ensure_one()
        return self.env['res.users']._crypt_context().verify(password, pwd_hash)


class PasswordResetHistory(models.Model):
    _name = 'password.reset.history'
    _description = 'Password Reset History'
    _order = 'reset_date desc'

    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        ondelete='cascade'
    )
    reset_date = fields.Datetime(
        string='Reset Date',
        default=fields.Datetime.now
    )
    ip_address = fields.Char(string='IP Address')
    user_agent = fields.Char(string='User Agent')
    old_password_hash = fields.Char(string='Old Password Hash')
    successful = fields.Boolean(string='Successful', default=True)
    reset_type = fields.Selection([
        ('email_link', 'Email Link'),
        ('sms_code', 'SMS Code'),
        ('admin', 'Admin Reset'),
        ('api', 'API'),
    ], string='Reset Type', default='api')
import json
import logging
from datetime import timedelta
import firebase_admin
from firebase_admin import credentials, messaging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class FCMDevice(models.Model):
    _name = 'fcm.device'
    _description = 'FCM Device Token'
    name = fields.Char(string='Device User')
    token = fields.Char(string='FCM Token', required=True)
    user_id = fields.Many2one('res.users', string='User', required=True, ondelete='cascade')
    active = fields.Boolean(default=True)
    last_seen = fields.Datetime(default=fields.Datetime.now)
    # Campo platform existente - LO MANTENEMOS PERO NO LO USAREMOS PARA LA NUEVA INFO
    platform = fields.Selection([
        ('android', 'Android'),
        ('ios', 'iOS'),
    ], string='Platform')

    # NUEVOS CAMPOS para información detallada del dispositivo
    device_platform = fields.Char(string='Plataforma Detallada', help="Ej: Mobile, Tablet, Desktop")
    device_os = fields.Char(string='Sistema Operativo', help="Ej: Android 13, iOS 16.1, Windows 10")
    device_browser = fields.Char(string='Navegador', help="Ej: Chrome 120, Safari 16")
    device_type = fields.Char(string='Tipo de Dispositivo', help="Ej: iPhone, Samsung Galaxy, PC")
    user_agent = fields.Text(string='User Agent Completo')
    ip_address = fields.Char(string='Dirección IP')
    is_mobile = fields.Boolean(string='Es Móvil')
    is_tablet = fields.Boolean(string='Es Tablet')
    is_pc = fields.Boolean(string='Es PC')

    # Campo computado para mostrar nombre descriptivo
    device_name = fields.Char(
        string='Device Name',
        compute='_compute_device_name',
        store=True
    )
    first_login = fields.Datetime(
        string='First login',
        default=fields.Datetime.now
    )
    login_count = fields.Integer(
        string='Count login',
        default=1
    )

    @api.depends('device_platform', 'device_os', 'device_browser', 'device_type')
    def _compute_device_name(self):
        for record in self:
            parts = []
            if record.device_platform:
                parts.append(record.device_platform)
            if record.device_os:
                parts.append(record.device_os)
            if record.device_browser:
                parts.append(f"({record.device_browser})")
            if record.device_type:
                parts.append(f"- {record.device_type}")

            record.device_name = ' '.join(parts) if parts else record.name

    @api.model
    def register_device_token(self, token, _user=None, platform=None, device_info=None):
        """
        API method mejorado para registrar device token con información detallada

        Args:
            token: FCM device token
            _user: User object (opcional)
            platform: 'android' o 'ios' (campo legacy)
            device_info: Diccionario con información detallada del dispositivo
        """
        _logger.info(_("Registering device token: %s with device info"), token)

        if not token:
            return {'success': False, 'error': _('Token is required')}

        user = _user if _user else self.env.user

        # Buscar dispositivo existente por token y usuario
        device = self.search([
            ('token', '=', token),
            ('user_id', '=', user.id)
        ], limit=1)

        values = {
            'user_id': user.id,
            'last_seen': fields.Datetime.now(),
            'active': True,
        }

        # Solo actualizar platform si se proporciona (campo legacy)
        if platform:
            values['platform'] = platform

        # Si hay información detallada del dispositivo
        if device_info:
            values.update({
                'device_platform': device_info.get('platform'),
                'device_os': device_info.get('os'),
                'device_browser': device_info.get('browser'),
                'device_type': device_info.get('device'),
                'user_agent': device_info.get('user_agent_raw'),
                'ip_address': device_info.get('ip_address'),
                'is_mobile': device_info.get('is_mobile', False),
                'is_tablet': device_info.get('is_tablet', False),
                'is_pc': device_info.get('is_pc', False),
            })

        if device:
            # Actualizar dispositivo existente
            device.write(values)
            # Incrementar contador de login
            device.login_count += 1
            device_id = device.id
            _logger.info(_("Updated existing device for user %s"), user.name)
        else:
            # Crear nuevo dispositivo
            values.update({
                'name': _("%s's device") % user.name,
                'token': token,
            })
            new_device = self.create(values)
            device_id = new_device.id
            _logger.info(_("Created new device with detailed info for user %s"), user.name)

        return {
            'success': True,
            'message': _('Device token registered successfully'),
            'device_id': device_id
        }

    @api.model
    def clean_invalid_tokens(self, *args, **kwargs):
        """
        Clean up invalid and inactive tokens.
        (Mantiene la funcionalidad original)
        """
        result = {
            'success': True,
            'message': _('Invalid and old tokens have been cleaned up.'),
            'details': []
        }

        inactive_devices = self.search([('active', '=', False)])
        if inactive_devices:
            count = len(inactive_devices)
            inactive_devices.unlink()
            _logger.info(_("Cleaned up %d inactive device tokens"), count)
            result['details'].append(_("Removed %d inactive device tokens") % count)

        date_threshold = fields.Datetime.now() - timedelta(days=90)
        old_devices = self.search([
            ('last_seen', '<', date_threshold),
            ('active', '=', True)
        ])

        if old_devices:
            count = len(old_devices)
            old_devices.write({'active': False})
            _logger.info(_("Marked %d old device tokens as inactive"), count)
            result['details'].append(
                _("Marked %d old tokens as inactive (not seen in 90+ days)") % count
            )

        if not result['details']:
            result['details'].append(_("No tokens needed cleanup"))

        return self._prepare_notification_action(result)

    @api.model
    def test_firebase_configuration(self, *args, **kwargs):
        """
        Test Firebase configuration and connection.

        This method validates the Firebase setup by:
        1. Checking if credentials are configured
        2. Validating the JSON format of credentials
        3. Initializing or verifying Firebase app initialization
        4. Testing the connection with a dry-run message

        This is useful for administrators to verify that the Firebase
        integration is properly configured before relying on it for
        production notifications.

        Returns:
            Client action dictionary for UI notification display
        """
        result = {
            'success': False,
            'message': '',
            'details': []
        }

        # Check Firebase credentials
        cred_json = self.env['ir.config_parameter'].sudo().get_param(
            'apn_notifications.firebase_credentials'
        )
        if not cred_json:
            result['message'] = _("Firebase credentials not configured")
            result['details'].append(
                _("Add credentials in System Parameters with key 'apn_notifications.firebase_credentials'")
            )
            return self._prepare_notification_action(result)

        try:
            # Try to parse the credentials
            cred_dict = json.loads(cred_json)

            # Check if Firebase app is already initialized
            firebase_initialized = False
            try:
                app = firebase_admin.get_app()
                result['details'].append(_("Firebase app was already initialized"))
                firebase_initialized = True
            except ValueError:
                # Initialize Firebase app
                try:
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
                    result['details'].append(_("Firebase app initialized successfully"))
                    firebase_initialized = True
                except Exception as e:
                    result['message'] = _("Failed to initialize Firebase app")
                    result['details'].append(str(e))
                    return self._prepare_notification_action(result)

            # Test connection with a dry-run message to an invalid token
            if firebase_initialized:
                try:
                    # Usar un token con formato válido pero que no existe
                    message = messaging.Message(
                        notification=messaging.Notification(
                            title='Test',
                            body='Testing Firebase connection',
                        ),
                        data={'test': 'true'},
                        token='fcm_token_test_validation_only'
                    )
                    messaging.send(message, dry_run=True)
                    result['details'].append(
                        _("Connection to Firebase messaging service is working correctly")
                    )
                    result['success'] = True
                    result['message'] = _("Firebase configuration is valid and connection test passed")
                except Exception as e:
                    error_str = str(e).lower()
                    # Lista de errores que indican que la conexión funciona pero el token no es válido
                    valid_connection_errors = [
                        'invalid-argument',
                        'invalid-registration',
                        'registration-token-not-registered',
                        'invalid-registration-token',
                        'registration token is not a valid fcm registration token',
                        'not_found',
                        'unregistered'
                    ]

                    if any(err in error_str for err in valid_connection_errors):
                        result['details'].append(
                            _("Connection to Firebase messaging service is working (received expected validation error)")
                        )
                        result['success'] = True
                        result['message'] = _("Firebase configuration is valid and connection test passed")
                    else:
                        # Error inesperado - probablemente error de autenticación o permisos
                        result['message'] = _("Firebase connection failed")
                        result['details'].append(_("Error: %s") % str(e))
                        _logger.error("Firebase connection test failed: %s", str(e))
            else:
                result['message'] = _("Firebase app could not be initialized")

        except json.JSONDecodeError:
            result['message'] = _("Invalid Firebase credentials format")
            result['details'].append(_("Credentials must be a valid JSON"))
        except Exception as e:
            result['message'] = _("Error testing Firebase configuration")
            result['details'].append(str(e))
            _logger.exception(_("Firebase test failed"))

        return self._prepare_notification_action(result)

    def _prepare_notification_action(self, result):
        """
        Helper method to prepare notification action for UI display.

        This internal method converts the operation results into a proper
        Odoo client action that can be displayed as a notification in the
        user interface. It handles different result types and formats them
        appropriately for the notification system.

        Args:
            result: Dictionary with success status, message, and details
                   or None/boolean for legacy support

        Returns:
            Client action dictionary formatted for Odoo's notification system
        """
        if result is None or isinstance(result, bool):
            # Ensure we never return a boolean value - legacy support
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Operation Result'),
                    'message': _('Operation completed'),
                    'type': 'success' if result else 'warning',
                    'sticky': False,
                }
            }

        action = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Testing Firebase Configuration') if 'firebase' in str(
                    result.get('message', '')).lower() else _('Tokens Cleanup'),
                'sticky': False,
            }
        }

        if result['success']:
            action['params']['type'] = 'success'
            action['params']['message'] = result['message']
        else:
            action['params']['type'] = 'danger'
            action['params']['message'] = result['message']

        if result.get('details'):
            action['params']['message'] += "\n" + "\n".join(result['details'])

        return action

    @api.model
    def deactivate_device_token(self, token, user_id=None):
        """
        Deactivate a specific device token for a user.

        This method is useful when:
        - A user logs out from the mobile app
        - A device token is no longer valid
        - Manual cleanup of specific tokens is needed

        Args:
            token: FCM device token to deactivate
            user_id: User ID (optional, defaults to current user)

        Returns:
            Dictionary with success status and message
        """
        _logger.info(_("Deactivating device token: %s"), token)

        if not token:
            return {
                'success': False,
                'error': _('Token is required')
            }

        # Get current user if not specified
        user = self.env['res.users'].browse(user_id) if user_id else self.env.user

        if not user.exists():
            return {
                'success': False,
                'error': _('User not found')
            }

        # Find the device
        domain = [
            ('token', '=', token),
            ('user_id', '=', user.id),
            ('active', '=', True)
        ]

        device = self.search(domain, limit=1)

        if not device:
            return {
                'success': False,
                'error': _('No active device found with the specified token for this user')
            }

        try:
            # Deactivate the device
            device.write({
                'active': False
            })
            _logger.info(
                _("Device token deactivated successfully for user %s"),
                user.name
            )

            return {
                'success': True,
                'message': _('Device token deactivated successfully'),
                'device_id': device.id
            }

        except Exception as e:
            _logger.error(
                _("Error deactivating device token: %s"),
                str(e)
            )
            return {
                'success': False,
                'error': _('Error deactivating device token: %s') % str(e)
            }

    @api.model
    def deactivate_user_devices(self, user_id=None):
        """
        Deactivate all active devices for a specific user.

        This is useful when:
        - A user account is deactivated
        - All user sessions need to be terminated
        - Cleanup all devices for a specific user

        Args:
            user_id: User ID (optional, defaults to current user)

        Returns:
            Dictionary with success status, message, and count of deactivated devices
        """
        user = self.env['res.users'].browse(user_id) if user_id else self.env.user

        if not user.exists():
            return {
                'success': False,
                'error': _('User not found')
            }

        _logger.info(_("Deactivating all devices for user: %s"), user.name)

        # Find all active devices for this user
        devices = self.search([
            ('user_id', '=', user.id),
            ('active', '=', True)
        ])

        if not devices:
            return {
                'success': True,
                'message': _('No active devices found for user %s') % user.name,
                'count': 0
            }

        try:
            count = len(devices)
            devices.write({'active': False})

            _logger.info(
                _("Deactivated %d device tokens for user %s"),
                count,
                user.name
            )

            return {
                'success': True,
                'message': _('Successfully deactivated %d device(s) for user %s') % (count, user.name),
                'count': count
            }

        except Exception as e:
            _logger.error(
                _("Error deactivating devices for user %s: %s"),
                user.name,
                str(e)
            )
            return {
                'success': False,
                'error': _('Error deactivating devices: %s') % str(e)
            }

    @api.model
    def deactivate_device_by_id(self, device_id):
        """
        Deactivate a specific device by its ID.

        Args:
            device_id: ID of the FCM device to deactivate

        Returns:
            Dictionary with success status and message
        """
        device = self.browse(device_id)

        if not device.exists():
            return {
                'success': False,
                'error': _('Device not found')
            }

        if not device.active:
            return {
                'success': True,
                'message': _('Device is already inactive'),
                'device_id': device.id
            }

        try:
            device.write({'active': False})
            _logger.info(
                _("Device deactivated: %s (ID: %d)"),
                device.name,
                device.id
            )

            return {
                'success': True,
                'message': _('Device "%s" deactivated successfully') % device.name,
                'device_id': device.id
            }

        except Exception as e:
            _logger.error(
                _("Error deactivating device %s: %s"),
                device.name,
                str(e)
            )
            return {
                'success': False,
                'error': _('Error deactivating device: %s') % str(e)
            }
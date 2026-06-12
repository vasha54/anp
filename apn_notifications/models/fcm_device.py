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

    name = fields.Char(string='Device Name', required=True)
    token = fields.Char(string='FCM Token', required=True)
    user_id = fields.Many2one('res.users', string='User', required=True, ondelete='cascade')
    active = fields.Boolean(default=True)
    last_seen = fields.Datetime(default=fields.Datetime.now)
    platform = fields.Selection([
        ('android', 'Android'),
        ('ios', 'iOS'),
    ], string='Platform')

    @api.model
    def register_device_token(self, token, _user=None, platform=None):
        """
        API method to register device token from mobile app.

        This method is called from the mobile application to register or update
        a device token for push notifications. It handles both new device
        registration and existing device updates.

        Args:
            token: FCM device token from the mobile app
            _user: User object (optional, defaults to current user)
            platform: Device platform ('android' or 'ios')

        Returns:
            Dictionary with success status, message, and device_id
        """
        _logger.info(_("Registering device token: %s"), token)

        if not token:
            return {'success': False, 'error': _('Token is required')}

        # Get current user
        user = _user if _user else self.env.user

        # Check if token already exists for the same user
        device = self.search([
            ('token', '=', token),
            ('user_id', '=', user.id)
        ], limit=1)

        values = {
            'user_id': user.id,
            'last_seen': fields.Datetime.now(),
            'active': True
        }

        if platform:
            values['platform'] = platform

        if device:
            # Update existing device for the same user
            device.write(values)
            device_id = device.id
            _logger.info(_("Updated existing device token for user %s"), user.name)
        else:
            # Create new device
            values.update({
                'name': _("%s's device") % user.name,
                'token': token,
            })
            new_device = self.create(values)
            device_id = new_device.id
            _logger.info(_("Created new device token for user %s"), user.name)

        return {
            'success': True,
            'message': _('Device token registered successfully'),
            'device_id': device_id
        }

    @api.model
    def clean_invalid_tokens(self):
        """
        Clean up invalid and inactive tokens.

        This method performs two cleanup operations:
        1. Removes inactive device tokens from the database
        2. Marks old tokens (not seen in 90+ days) as inactive

        This helps maintain database cleanliness and ensures that push
        notifications are only sent to active, recently used devices.

        Returns:
            Client action dictionary for UI notification display
        """
        result = {
            'success': True,
            'message': _('Invalid and old tokens have been cleaned up.'),
            'details': []
        }

        # Find and delete inactive tokens
        inactive_devices = self.search([('active', '=', False)])
        if inactive_devices:
            count = len(inactive_devices)
            inactive_devices.unlink()
            _logger.info(_("Cleaned up %d inactive device tokens"), count)
            result['details'].append(_("Removed %d inactive device tokens") % count)

        # Find old tokens (not seen in more than 90 days)
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
    def test_firebase_configuration(self):
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
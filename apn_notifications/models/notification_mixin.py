import json
import logging
import firebase_admin
from firebase_admin import credentials, messaging
from odoo import models, _

_logger = logging.getLogger(__name__)

class NotificationMixin(models.AbstractModel):
    _name = 'apn.notifications.mixin'
    _description = 'Mixin for FCM notification sending'
    _abstract = True

    def send_notification(self, title, body, data=None, partner=None, user=None):
        """
        Generic method to send FCM notifications.
        Args:
            title: Notification title
            body: Notification body
            data: Additional data dictionary
            partner: partner (optional) to notify
            user: user (optional) to notify
        Returns:
            Number of successfully sent notifications
        """
        self.ensure_one()
        _logger.info(_("Preparing notification '%s'"), title)

        # Determine target user
        target_user = user
        if not target_user and partner:
            target_user = self.env['res.users'].search([('partner_id', '=', partner.id)], limit=1)
        if not target_user:
            _logger.warning(_("No user found for the specified partner"))
            return 0

        # Search for active devices
        devices = self.env['fcm.device'].search([
            ('user_id', '=', target_user.id),
            ('active', '=', True)
        ])
        if not devices:
            _logger.warning(_("No active devices for user %s"), target_user.name)
            return 0

        # Get Firebase credentials
        cred_json = self.env['ir.config_parameter'].sudo().get_param('apn_notifications.firebase_credentials')
        if not cred_json:
            msg = _("Firebase credentials not configured")
            _logger.error(msg)
            if hasattr(self, 'message_post'):
                self.message_post(body=msg)
            return 0
        try:
            if not firebase_admin._apps:
                try:
                    cred_dict = json.loads(cred_json)
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
                except json.JSONDecodeError:
                    msg = _("Invalid Firebase credentials format (must be valid JSON)")
                    _logger.error(msg)
                    if hasattr(self, 'message_post'):
                        self.message_post(body=msg)
                    return 0
            notification_data = data or {}
            # Add default click_action if not present
            if 'click_action' not in notification_data:
                notification_data['click_action'] = 'FLUTTER_NOTIFICATION_CLICK'
            # Convert all values to string to avoid ValueError
            notification_data = {k: str(v) for k, v in notification_data.items()}
            success_count = 0
            for device in devices:
                try:
                    _logger.info(_("Sending notification to device %s"), device.name)
                    message = messaging.Message(
                        notification=messaging.Notification(
                            title=title,
                            body=body,
                        ),
                        data=notification_data,
                        token=device.token,
                    )
                    response = messaging.send(message)
                    _logger.info(_("Notification sent: %s"), response)
                    success_count += 1
                except firebase_admin.exceptions.FirebaseError as e:
                    error_code = getattr(e, 'code', 'unknown_error')
                    if error_code in ['invalid-argument', 'registration-token-not-registered',
                                      'NOT_FOUND', 'UNREGISTERED', 'not-found', 'unregistered']:
                        device.active = False
                        _logger.warning(_("Deactivating device due to error: %s - Token: %s"), error_code, device.token)
                    _logger.error(_("Error sending notification: %s"), str(e))
                    if hasattr(self, 'message_post'):
                        self.message_post(body=_("Error sending notification: %s") % str(e))
            if success_count > 0 and hasattr(self, 'message_post'):
                self.message_post(body=_("Notification '%s' sent to %d devices") % (title, success_count))
            return success_count
        except Exception as e:
            _logger.exception(_("Exception sending notification"))
            if hasattr(self, 'message_post'):
                self.message_post(body=_("Exception sending notification: %s") % str(e))
            return 0
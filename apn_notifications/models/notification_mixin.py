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

    def send_notification(self, title, body, data=None, partner=None, user=None, topic=None):
        """
        Generic method to send FCM notifications.
        Can send to individual devices (via partner/user) OR to a topic.

        Args:
            title: Notification title
            body: Notification body
            data: Additional data dictionary
            partner: partner (optional) to notify (for device-specific sending)
            user: user (optional) to notify (for device-specific sending)
            topic: topic name (optional) to send notification to all subscribed devices
        Returns:
            Number of successfully sent notifications (1 for topic, count for devices)
        """
        self.ensure_one()
        _logger.info(_("Preparing notification '%s'"), title)

        # Get Firebase credentials (needed for both modes)
        cred_json = self.env['ir.config_parameter'].sudo().get_param('apn_notifications.firebase_credentials')
        if not cred_json:
            msg = _("Firebase credentials not configured")
            _logger.error(msg)
            if hasattr(self, 'message_post'):
                self.message_post(body=msg)
            return 0

        try:
            # Initialize Firebase if not already done
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

            # Prepare notification data
            notification_data = data or {}
            if 'click_action' not in notification_data:
                notification_data['click_action'] = 'FLUTTER_NOTIFICATION_CLICK'
            notification_data = {k: str(v) for k, v in notification_data.items()}

            # --- MODE 1: Send to TOPIC (if topic parameter is provided) ---
            if topic:
                return self._send_to_topic(title, body, notification_data, topic)
            # --- MODE 2: Send to individual DEVICES (original behavior) ---
            else:
                return self._send_to_devices(title, body, notification_data, partner, user)

        except Exception as e:
            _logger.exception(_("Exception sending notification"))
            if hasattr(self, 'message_post'):
                self.message_post(body=_("Exception sending notification: %s") % str(e))
            return 0

    def _send_to_topic(self, title, body, notification_data, topic):
        """
        Send notification to all devices subscribed to a topic.
        Returns 1 if successful, 0 otherwise.
        """
        try:
            _logger.info(_("Sending notification to topic '%s'"), topic)

            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=notification_data,
                topic=topic,  # <-- Esto es lo nuevo: enviamos al topic en vez de a un token
            )

            response = messaging.send(message)
            _logger.info(_("Notification sent to topic '%s': %s"), topic, response)

            if hasattr(self, 'message_post'):
                self.message_post(
                    body=_("Notification '%s' sent to topic '%s'") % (title, topic)
                )

            return 1  # En topic, consideramos 1 envío exitoso

        except firebase_admin.exceptions.FirebaseError as e:
            error_msg = str(e)
            _logger.error(_("Error sending notification to topic '%s': %s"), topic, error_msg)

            if hasattr(self, 'message_post'):
                self.message_post(
                    body=_("Error sending to topic '%s': %s") % (topic, error_msg)
                )

            return 0

    def _send_to_devices(self, title, body, notification_data, partner, user):
        """
        Send notification to individual devices (original behavior).
        Returns the number of successfully sent notifications.
        """
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
                    _logger.warning(
                        _("Deactivating device due to error: %s - Token: %s"),
                        error_code,
                        device.token
                    )
                _logger.error(_("Error sending notification: %s"), str(e))
                if hasattr(self, 'message_post'):
                    self.message_post(body=_("Error sending notification: %s") % str(e))

        if success_count > 0 and hasattr(self, 'message_post'):
            self.message_post(
                body=_("Notification '%s' sent to %d devices") % (title, success_count)
            )

        return success_count
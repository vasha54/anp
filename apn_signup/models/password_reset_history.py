import logging
import secrets
import re
import uuid

from odoo import models, fields, api, _
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

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
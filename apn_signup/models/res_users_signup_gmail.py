from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import uuid
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'
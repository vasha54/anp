# -*- coding: utf-8 -*-

import json
from odoo.exceptions import ValidationError
from odoo import _, models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    firebase_credentials = fields.Char(
        string="Firebase Credentials",
        config_parameter='apn_notifications.firebase_credentials',
        default=lambda self: self.env['ir.config_parameter'].sudo().get_param(
            'apn_notifications.firebase_credentials', ''
        )
    )

    firebase_is_configured = fields.Boolean(
        string="Firebase Configured",
        compute='_compute_firebase_configured'
    )

    firebase_project_id = fields.Char(
        string="Project ID",
        compute='_compute_firebase_info'
    )

    @api.depends('firebase_credentials')
    def _compute_firebase_configured(self):
        for record in self:
            valid = bool(record.firebase_credentials)
            if valid:
                try:
                    json.loads(record.firebase_credentials)
                except json.JSONDecodeError:
                    valid = False
            record.firebase_is_configured = valid

    @api.depends('firebase_credentials')
    def _compute_firebase_info(self):
        for record in self:
            project_id = ''
            if record.firebase_credentials:
                try:
                    creds = json.loads(record.firebase_credentials)
                    project_id = creds.get('project_id', '')
                except json.JSONDecodeError:
                    project_id = 'Invalid JSON'
            record.firebase_project_id = project_id

    @api.constrains('firebase_credentials')
    def _check_firebase_credentials(self):
        for record in self:
            if record.firebase_credentials:
                try:
                    json.loads(record.firebase_credentials)
                except json.JSONDecodeError:
                    raise ValidationError(
                        _("Firebase credentials must be valid JSON format")
                    )

    def action_test_firebase_connection(self):
        """Test Firebase connection from settings"""
        self.ensure_one()
        return self.env['fcm.device'].test_firebase_configuration()
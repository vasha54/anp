from odoo import _, api, models
from odoo.exceptions import ValidationError

class IrConfigParameter(models.Model):
    _inherit = "ir.config_parameter"

    PARAMETERS = {
        "apn_company.nearby_branches_default_distance_meters": {
            "min": 5,
            "max": 2**29,
            "type": int,
            "message_error_type": "Parameter %s must be an integer. Received value: %s",
            "message_error_range": "Parameter %s must be between %s and %s. Received value: %s",
        }
    }

    def _validate_parameter_value(self, key, value):
        if key not in self.PARAMETERS:
            return True

        param_def = self.PARAMETERS[key]

        try:
            if param_def["type"] is int:
                converted_value = int(value)
        except (ValueError, TypeError) as err:
            raise ValidationError(_(param_def["message_error_type"]) % (key, value)) from err

        if param_def["type"] is int and not param_def["min"] <= converted_value <= param_def["max"]:
            raise ValidationError(
                _(param_def["message_error_range"])
                % (key, param_def["min"], param_def["max"], value)
            )

        return True

    @api.model
    def set_param(self, key, value):
        self._validate_parameter_value(key, value)
        return super().set_param(key, value)

    def write(self, vals):
        if "value" in vals:
            for record in self:
                if record.key in self.PARAMETERS:
                    self._validate_parameter_value(record.key, vals["value"])
        return super().write(vals)
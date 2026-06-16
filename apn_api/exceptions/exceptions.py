from odoo import _


class MissingParameterError(Exception):
    """Custom exception to indicate that a required parameter is missing."""

    def __init__(self, parameter):
        text = _("The parameter '%(parameter)s' is required.", parameter=parameter)
        super().__init__(text)


class MissingMultipleParameterError(Exception):
    """Custom exception to indicate that multiple required parameters are missing."""

    def __init__(self, list_parameters):
        parameters = ", ".join([f"{x}" for x in list_parameters])
        text = _(
            "At least one of the following parameters is required: %(parameters)s. "
            "None were provided.",
            parameters=parameters
        )
        super().__init__(text)


class AuthenticateFailed(Exception):
    """Custom exception for authentication failures."""

    def __init__(self):
        text = _("Authentication failed")
        super().__init__(text)


class DatabaseNotAvailable(Exception):
    """Custom exception for database unavailability."""

    def __init__(self):
        text = _("Database not available")
        super().__init__(text)


class EmptyBodyInRequest(Exception):
    """Custom exception for empty request body."""

    def __init__(self):
        text = _("Empty body in request")
        super().__init__(text)


class UserNotFound(Exception):
    """Custom exception for user not found."""

    def __init__(self):
        text = _("User not found")
        super().__init__(text)


class TokenExpiredError(Exception):
    """Custom exception for expired tokens."""

    def __init__(self):
        text = _("Token has expired")
        super().__init__(text)


class InvalidTokenError(Exception):
    """Custom exception for invalid tokens."""

    def __init__(self):
        text = _("Invalid token")
        super().__init__(text)


class AccessDeniedError(Exception):
    """Custom exception for access denied."""

    def __init__(self, message=None):
        text = message or _("Access denied")
        super().__init__(text)


class UserInactiveError(Exception):
    """Custom exception for inactive users."""

    def __init__(self):
        text = _("User account is inactive")
        super().__init__(text)


class DeviceLimitExceededError(Exception):
    """Custom exception for exceeding device limit."""

    def __init__(self, max_devices):
        text = _(
            "Maximum number of devices (%(max_devices)s) exceeded. "
            "Please contact your administrator.",
            max_devices=max_devices
        )
        super().__init__(text)
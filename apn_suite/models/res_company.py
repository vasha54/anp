import logging
import base64
import os

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessDenied
from odoo import SUPERUSER_ID

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    @api.model
    def _set_default_company(self):
        company = self.env.ref("base.main_company", raise_if_not_found=False)
        _logger.info("Search company")
        if company:
            # Ruta a la imagen estática
            _logger.info(f"Find company: {company.name}")
            module_path = os.path.dirname(os.path.dirname(__file__))
            image_path = os.path.join(module_path, "static", "src", "img", "logo_pilates.png")
            favicon_path = os.path.join(module_path, "static", "src", "img", "favicon.ico")

            if os.path.exists(image_path):
                with open(image_path, "rb") as image_file:
                    encoded_image = base64.b64encode(image_file.read())
                    company.write(
                        {
                            "name": "Pilates",
                            "logo": encoded_image,
                        }
                    )
                    _logger.info(f"Update company: {company.name}")

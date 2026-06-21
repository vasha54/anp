from odoo import http
from odoo.http import request
import base64
import logging

_logger = logging.getLogger(__name__)

class PublicImageController(http.Controller):

    @http.route(['/public/image/branch/<int:branch_id>'],
                type='http', auth='public', website=True, methods=['GET'], csrf=False)
    def serve_public_branch_image(self, branch_id, **kwargs):
        """
        Public controller to serve res.company images without authentication
        Access via: /public/image/branch/123
        """
        try:
            # Find the partner record using superuser privileges
            partner = request.env['res.company'].sudo().browse(branch_id)

            if not partner.exists() or not partner.logo:
                # Return default image or 404 if no partner or image found
                return request.not_found()

            # Extract image data and format
            image_data = base64.b64decode(partner.logo)
            image_content_type = self._get_image_content_type(partner.logo)

            # Serve the image with caching headers
            return request.make_response(
                image_data,
                headers=[
                    ('Content-Type', image_content_type),
                    ('Cache-Control', 'public, max-age=86400'),  # Cache for 24 hours
                ]
            )

        except Exception as e:
            # Log error and return 404
            _logger.error("Error serving public partner image: %s", str(e))
            return request.not_found()

    @http.route(['/public/image/product_accesorie/<int:accesorie_id>'],
                type='http', auth='public', website=True, methods=['GET'], csrf=False)
    def serve_public_accesorie_image(self, accesorie_id, **kwargs):
        """
        Public controller to serve res.company images without authentication
        Access via: /public/image/branch/123
        """
        try:
            # Find the partner record using superuser privileges
            product = request.env['product.product'].sudo().browse(accesorie_id)

            if not product.exists() or not product.image_1920:
                # Return default image or 404 if no partner or image found
                return request.not_found()

            # Extract image data and format
            image_data = base64.b64decode(product.image_1920)
            image_content_type = self._get_image_content_type(product.image_1920)

            # Serve the image with caching headers
            return request.make_response(
                image_data,
                headers=[
                    ('Content-Type', image_content_type),
                    ('Cache-Control', 'public, max-age=86400'),  # Cache for 24 hours
                ]
            )

        except Exception as e:
            # Log error and return 404
            _logger.error("Error serving public product image: %s", str(e))
            return request.not_found()

    def _get_image_content_type(self, image_data):
        """
        Detect image content type from base64 data
        Simple detection - in production you might want more robust detection
        """
        if image_data.startswith(b'/9j/'):
            return 'image/jpeg'
        elif image_data.startswith(b'iVBORw0KGgo'):
            return 'image/png'
        elif image_data.startswith(b'R0lGODdh'):
            return 'image/gif'
        else:
            return 'image/jpeg'  # Default fallback
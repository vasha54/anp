import json
import logging
import os

from odoo import http
from odoo.http import request, Response
from datetime import datetime

_logger = logging.getLogger(__name__)


class SwaggerController(http.Controller):

    @http.route('/apn_swagger/swagger.yaml', type='http', auth='public', csrf=False)
    def swagger_yaml(self):
        """Sirve el archivo swagger.yaml"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            addon_path = os.path.dirname(current_dir)
            yaml_path = os.path.join(addon_path, 'swagger', 'swagger.yaml')

            _logger.info(f"Buscando swagger.yaml en: {yaml_path}")

            if not os.path.exists(yaml_path):
                _logger.error(f"Archivo swagger.yaml no encontrado en: {yaml_path}")
                return Response(
                    "Archivo swagger.yaml no encontrado",
                    status=404,
                    mimetype='text/plain'
                )

            with open(yaml_path, 'r') as file:
                yaml_content = file.read()

            return Response(
                yaml_content,
                mimetype='text/yaml',
                headers={
                    'Content-Type': 'text/yaml; charset=utf-8',
                    'Access-Control-Allow-Origin': '*'
                }
            )
        except Exception as e:
            _logger.error(f"Error al servir swagger.yaml: {str(e)}")
            return Response(
                f"Error interno: {str(e)}",
                status=500,
                mimetype='text/plain'
            )

    @http.route('/api_pilates/docs', type='http', auth='public', csrf=False)
    def swagger_ui(self):
        """Vista de Swagger UI con archivos locales"""
        # Obtener la URL base del módulo para archivos estáticos
        base_url = '/apn_api/static/src/swagger'

        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="utf-8"/>
            <meta name="viewport" content="width=device-width, initial-scale=1"/>
            <title>APN Pilates API - Documentación</title>
            <link rel="icon" type="image/png" href="{base_url}/favicon-32x32.png"/>
            <link rel="stylesheet" href="{base_url}/swagger-ui.css"/>
            <style>
                html {{
                    box-sizing: border-box;
                    overflow: -moz-scrollbars-vertical;
                    overflow-y: scroll;
                }}
                *,
                *:before,
                *:after {{
                    box-sizing: inherit;
                }}
                body {{
                    margin: 0;
                    background: #fafafa;
                }}
                .topbar {{
                    background: linear-gradient(135deg, #4154f1 0%, #2c3cd4 100%);
                    padding: 15px 30px;
                    color: white;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                }}
                .topbar h1 {{
                    margin: 0;
                    font-size: 1.5em;
                    font-weight: 600;
                }}
                .topbar .version {{
                    background: rgba(255,255,255,0.2);
                    padding: 5px 15px;
                    border-radius: 20px;
                    font-size: 0.9em;
                }}
                .swagger-ui .topbar {{
                    display: none;
                }}
            </style>
        </head>
        <body>
            <div class="topbar">
                <div>
                    <h1>🚀 APN Pilates API v1.0</h1>
                    <small style="opacity: 0.8;">Documentación interactiva de la API REST</small>
                </div>
                <span class="version">Odoo 18</span>
            </div>
            <div id="swagger-ui"></div>

            <script src="{base_url}/swagger-ui-bundle.js"></script>
            <script src="{base_url}/swagger-ui-standalone-preset.js"></script>
            <script>
                window.onload = function() {{
                    const ui = SwaggerUIBundle({{
                        url: "/apn_swagger/swagger.yaml",
                        dom_id: '#swagger-ui',
                        deepLinking: true,
                        presets: [
                            SwaggerUIBundle.presets.apis,
                            SwaggerUIStandalonePreset
                        ],
                        plugins: [
                            SwaggerUIBundle.plugins.DownloadUrl
                        ],
                        layout: "StandaloneLayout",
                        defaultModelsExpandDepth: 1,
                        defaultModelExpandDepth: 1,
                        docExpansion: "list",
                        filter: true,
                        showExtensions: true,
                        showCommonExtensions: true,
                        tryItOutEnabled: true,
                        defaultModelRendering: 'model'
                    }});
                    window.ui = ui;
                }};
            </script>
        </body>
        </html>
        """
        return Response(html_content, mimetype='text/html')
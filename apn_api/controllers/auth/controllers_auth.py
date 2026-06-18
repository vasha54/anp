import json
import jwt
import logging
import odoo
import re

from datetime import datetime, timedelta
from user_agents import parse

from odoo import _, http
from odoo.http import Response, request
from odoo.exceptions import AccessDenied
from odoo.modules.registry import Registry

from ..base_api_controller import BaseAPIController

_logger = logging.getLogger(__name__)

class AuthAPIController(BaseAPIController):

    def _get_jwt_expiration_datetime(self, env):
        """Obtener la fecha de expiración para el token JWT"""
        expiration_value = int(env['ir.config_parameter'].sudo().get_param(
            'jwt_token.expiration_value',
            12
        ))
        expiration_unit = env['ir.config_parameter'].sudo().get_param(
            'jwt_token.expiration_unit',
            'hours'
        )

        now = datetime.now()
        if expiration_unit == 'minutes':
            expiration = now + timedelta(minutes=expiration_value)
        elif expiration_unit == 'hours':
            expiration = now + timedelta(hours=expiration_value)
        else:  # 'days'
            expiration = now + timedelta(days=expiration_value)

        return expiration

    def _parse_user_agent(self, user_agent_string):
        """
        Analiza el User-Agent para extraer información del dispositivo
        """
        try:
            # Usando la librería user-agents (recomendado)
            user_agent = parse(user_agent_string)

            device_info = {
                'browser': f"{user_agent.browser.family} {user_agent.browser.version_string}",
                'os': f"{user_agent.os.family} {user_agent.os.version_string}",
                'device': user_agent.device.family,
                'is_mobile': user_agent.is_mobile,
                'is_tablet': user_agent.is_tablet,
                'is_pc': user_agent.is_pc,
                'platform': self._get_platform(user_agent),
                'user_agent_raw': user_agent_string
            }

            return device_info

        except Exception as e:
            _logger.error(f"Error parsing user agent: {e}")
            # Fallback a análisis básico si no se puede usar la librería
            return self._parse_user_agent_basic(user_agent_string)

    def _parse_user_agent_basic(self, user_agent_string):
        """
        Análisis básico del User-Agent sin dependencias externas
        """
        device_info = {
            'browser': 'Unknown',
            'os': 'Unknown',
            'platform': 'Unknown',
            'is_mobile': False,
            'is_tablet': False,
            'user_agent_raw': user_agent_string
        }

        # Detectar sistema operativo
        if 'Windows' in user_agent_string:
            device_info['os'] = 'Windows'
        elif 'Mac OS' in user_agent_string or 'Macintosh' in user_agent_string:
            device_info['os'] = 'macOS'
        elif 'Linux' in user_agent_string and 'Android' not in user_agent_string:
            device_info['os'] = 'Linux'
        elif 'Android' in user_agent_string:
            device_info['os'] = 'Android'
            device_info['is_mobile'] = True
        elif 'iOS' in user_agent_string or 'iPhone' in user_agent_string:
            device_info['os'] = 'iOS'
            device_info['is_mobile'] = True
        elif 'iPad' in user_agent_string:
            device_info['os'] = 'iOS'
            device_info['is_tablet'] = True

        # Detectar navegador
        if 'Chrome' in user_agent_string and 'Edg' not in user_agent_string:
            device_info['browser'] = 'Chrome'
        elif 'Firefox' in user_agent_string:
            device_info['browser'] = 'Firefox'
        elif 'Safari' in user_agent_string and 'Chrome' not in user_agent_string:
            device_info['browser'] = 'Safari'
        elif 'Edg' in user_agent_string:
            device_info['browser'] = 'Edge'
        elif 'Opera' in user_agent_string or 'OPR' in user_agent_string:
            device_info['browser'] = 'Opera'

        # Determinar plataforma
        device_info['platform'] = 'Mobile' if device_info['is_mobile'] else 'Web'

        return device_info

    def _get_platform(self, user_agent):
        """
        Determina la plataforma basada en el análisis
        """
        if user_agent.is_mobile:
            return 'Mobile'
        elif user_agent.is_tablet:
            return 'Tablet'
        else:
            return 'Desktop'


    @http.route(
        "/api_pilates/v1/login",
        type='json',
        auth="none",
        methods=['POST'],
        csrf=False
    )
    def login(self, **post):
        """
        Login simple: siempre genera un nuevo token, reemplazando cualquier token anterior
        """
        try:
            # Obtener datos del JSON
            data = self._get_json_data(request.httprequest.data)
            self._check_existence_parameters(['login', 'password','token_fmc'], data)

            login = data['login']
            password = data['password']
            token_fmc = data['token_fmc']
            current_db = request.env.cr.dbname

            # Obtener información del dispositivo
            user_agent = request.httprequest.headers.get('User-Agent', '')
            client_ip = request.httprequest.remote_addr
            device_info = self._parse_user_agent(user_agent)
            device_info['ip_address'] = client_ip

            answer = {}
            # Usar Registry directamente
            registry = Registry(current_db)
            with registry.cursor() as cr:
                env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})

                # Crear el diccionario de credenciales
                credentials = {
                    'type': 'password',
                    'login': login,
                    'password': password
                }

                # Autenticar usuario
                uid = env['res.users'].authenticate(current_db, credentials, {})
                if not uid:
                    raise AccessDenied(_("Invalid credentials"))

                _logger.info(f"User authenticated with uid:{uid}")
                uid = uid.get('uid', 0)
                user = env['res.users'].sudo().browse(uid)

                if not user:
                    raise Exception("Usuario no encontrado")

                # Verificar acceso del usuario
                self._check_access_user_active(env, user.id)

                # Registrar o actualizar dispositivo FCM con información detallada
                if token_fmc:
                    # Determinar platform legacy basado en el device info
                    legacy_platform = None
                    if 'Android' in device_info.get('os', ''):
                        legacy_platform = 'android'
                    elif 'iOS' in device_info.get('os', ''):
                        legacy_platform = 'ios'

                    env['fcm.device'].sudo().register_device_token(
                        token=token_fmc,
                        _user=user,
                        platform=legacy_platform,  # Mantener compatibilidad
                        device_info=device_info  # Nueva información detallada
                    )

                # Siempre generar nuevo token JWT (reemplaza cualquier token anterior)
                expiration_dt = self._get_jwt_expiration_datetime(env)

                # Crear payload
                payload = {
                    "user_id": user.id,
                    "login": user.login,
                    "exp": expiration_dt,
                    "token_fmc": token_fmc,
                    "iat": datetime.now()
                }

                # Generar nuevo token
                token = jwt.encode(
                    payload,
                    BaseAPIController.SECRET_KEY,
                    algorithm=BaseAPIController.ALGORITHM
                )

                # Guardar el nuevo token (reemplaza cualquier token anterior)
                user.sudo().write({
                    "jwt_token": token,
                    "token_expiration": expiration_dt
                })

                _logger.info(f"Nuevo token generado para usuario {user.login}")

                # Preparar respuesta
                answer = {
                    "status": "success",
                    "user": {
                        "id": user.id,
                        "name": user.name,
                        "login": user.login,
                        "token": token,
                        "token_expiration": self._convert_timezone(user, expiration_dt),
                    },
                    "message": "Sesión iniciada exitosamente"
                }

            _logger.info(f"Response: {answer}")
            return answer

        except Exception as e:
            return self._handle_error(e)

    @http.route(
        "/api_pilates/v1/logout",
        type='json',
        auth="none",
        methods=['POST'],
        csrf=False
    )
    def logout(self, **post):
        """
        Logout simple: elimina el token del usuario sin verificar expiración
        """
        try:
            # Extraer token del encabezado Authorization
            auth_header = http.request.httprequest.headers.get('Authorization')
            if not auth_header or 'Bearer ' not in auth_header:
                raise Exception("Encabezado de autorización inválido")

            token = auth_header.split('Bearer ')[1].strip()
            current_db = request.env.cr.dbname

            answer = {}
            registry = Registry(current_db)
            with registry.cursor() as cr:
                env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})

                # Buscar usuario por token (sin verificar expiración)
                users = env['res.users'].sudo().search([("jwt_token", "=", token)])

                if users:
                    # Invalidar token en base de datos
                    users.sudo().write({
                        "jwt_token": False,
                        "token_expiration": False
                    })
                    answer = {
                        "status": "success",
                        "message": "Sesión cerrada correctamente",
                        "data": None,
                        "pagination": None,
                    }
                else:
                    # Si no se encuentra por token exacto, intentar decodificar para obtener user_id
                    try:
                        # Intentar decodificar incluso si está expirado
                        payload = jwt.decode(
                            token,
                            BaseAPIController.SECRET_KEY,
                            algorithms=[BaseAPIController.ALGORITHM],
                            options={"verify_exp": False}  # No verificar expiración
                        )
                        user_id = payload.get('user_id')

                        # Buscar usuario por ID y limpiar token
                        user = env['res.users'].sudo().browse(user_id)
                        if user:
                            user.sudo().write({
                                "jwt_token": False,
                                "token_expiration": False
                            })
                            answer = {
                                "status": "success",
                                "message": "Sesión cerrada correctamente (token expirado)",
                                "data": None,
                                "pagination": None,
                            }
                        else:
                            answer = {
                                "status": "error",
                                "message": "Usuario no encontrado en el sistema",
                                "data": None,
                                "pagination": None,
                            }
                    except:
                        # Token inválido o no se pudo decodificar
                        answer = {
                            "status": "error",
                            "message": "Token inválido",
                            "data": None,
                            "pagination": None,
                        }

            _logger.info(f"Response: {answer}")
            return answer

        except Exception as e:
            return self._handle_error(e)
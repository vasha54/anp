import json
import odoo
import logging
import jwt
import traceback
import yaml

from odoo import _, fields, http
from odoo.http import Response
from odoo.exceptions import AccessDenied, AccessError, UserError

from pytz import timezone
from datetime import datetime


class BaseAPIController(http.Controller):

    SECRET_KEY = "v#7P!x9A$gF2mZbR5kYq8tNs3Wu6cJdE1hT4oVlXp0yIjOeQrDaSzMfHnLwK_+CtB"
    ALGORITHM = "HS256"

    # Permisos individuales (bits individuales)
    CAN_NONE = 0  # 0000 - Sin permisos
    CAN_UNLINK = 1  # 0001 - Solo eliminar
    CAN_WRITE = 2  # 0010 - Solo modificar
    CAN_CREATE = 4  # 0100 - Solo crear
    CAN_READ = 8  # 1000 - Solo leer

    # Combinaciones de 2 permisos
    CAN_UNLINK_WRITE = 3  # 0011 - Eliminar + Modificar (1|2)
    CAN_UNLINK_CREATE = 5  # 0101 - Eliminar + Crear (1|4)
    CAN_UNLINK_READ = 9  # 1001 - Eliminar + Leer (1|8)
    CAN_WRITE_CREATE = 6  # 0110 - Modificar + Crear (2|4)
    CAN_WRITE_READ = 10  # 1010 - Modificar + Leer (2|8)
    CAN_CREATE_READ = 12  # 1100 - Crear + Leer (4|8)

    # Combinaciones de 3 permisos
    CAN_UNLINK_WRITE_CREATE = 7  # 0111 - Eliminar + Modificar + Crear (1|2|4)
    CAN_UNLINK_WRITE_READ = 11  # 1011 - Eliminar + Modificar + Leer (1|2|8)
    CAN_UNLINK_CREATE_READ = 13  # 1101 - Eliminar + Crear + Leer (1|4|8)
    CAN_WRITE_CREATE_READ = 14  # 1110 - Modificar + Crear + Leer (2|4|8)

    # Todos los permisos
    CAN_ALL = 15  # 1111 - Eliminar + Modificar + Crear + Leer (1|2|4|8)

    def _endpoint_not_yet_implemented(self):
        answer = {
            "status": "error",
            "message": "EndPoint de API aún no implementado",
            "data": None,
            "pagination": None,
        }
        return answer

    def _info_error(self, _exception):
        info_error = False
        type_exception = type(_exception).__name__
        message_exception = str(_exception)
        tb = traceback.extract_tb(_exception.__traceback__)
        if tb:
            file, line, function, text = tb[-1]
            info_error = {
                'type': type_exception,
                'message': message_exception,
                'file': file,
                'line': line,
                'function': function,
                'text': text,
            }
        else:
            info_error = {
                'type': type_exception,
                'message': message_exception,
                'file': None,
                'line': None,
                'function': None,
                'text': None,
            }
        return info_error

    def _response_error(self, code, message, detail=''):
        """Formatea una respuesta de error"""
        response_data = {
            'success': False,
            'error': {
                'code': code,
                'message': message,
                'detail': detail
            },
            'timestamp': http.request.env.cr.now()
        }
        return Response(
            json.dumps(response_data, default=str),
            status=code,
            mimetype='application/json',
            headers={
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        )

    def _response_success(self, data, message='OK', status=200):
        """Formatea una respuesta exitosa"""
        response_data = {
            'success': True,
            'message': message,
            'data': data,
            'timestamp': http.request.env.cr.now()
        }
        return Response(
            json.dumps(response_data, default=str),
            status=status,
            mimetype='application/json',
            headers={
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Authorization, Content-Type',
            }
        )

    @http.route('/api_pilates/v1/status', type='http', auth='public', methods=['GET'], csrf=False)
    def api_status(self):
        """Endpoint de estado de la API"""
        return self._response_success({
            'api_version': '1.0',
            'odoo_version': '18.0',
            'status': 'operational'
        })



# import json
# import functools
# from odoo import http
# from odoo.http import request, Response
# import logging
#
# _logger = logging.getLogger(__name__)
#
# def validate_token(func):
#     """Decorador para validar token en las peticiones"""
#     @functools.wraps(func)
#     def wrapper(self, *args, **kwargs):
#         # Obtener token del header
#         token = request.httprequest.headers.get('Authorization', '').replace('Bearer ', '')
#
#         if not token:
#             return self._response_error(401, 'Token no proporcionado', 'Se requiere un token de autorización')
#
#         # Verificar token
#         user = request.env['apn.api.token'].sudo().get_user_from_token(token)
#         if not user:
#             return self._response_error(403, 'Token inválido', 'El token proporcionado no es válido o ha expirado')
#
#         # Actualizar el usuario del entorno
#         request.env = request.env(user=user.id)
#
#         return func(self, *args, **kwargs)
#     return wrapper
#
# class APNRestController(http.Controller):
#
#     def _response_success(self, data, message='OK', status=200):
#         """Formatea una respuesta exitosa"""
#         response_data = {
#             'success': True,
#             'message': message,
#             'data': data,
#             'timestamp': http.request.env.cr.now()
#         }
#         return Response(
#             json.dumps(response_data, default=str),
#             status=status,
#             mimetype='application/json',
#             headers={
#                 'Content-Type': 'application/json',
#                 'Access-Control-Allow-Origin': '*',
#                 'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
#                 'Access-Control-Allow-Headers': 'Authorization, Content-Type',
#             }
#         )
#
#     def _response_error(self, code, message, detail=''):
#         """Formatea una respuesta de error"""
#         response_data = {
#             'success': False,
#             'error': {
#                 'code': code,
#                 'message': message,
#                 'detail': detail
#             },
#             'timestamp': http.request.env.cr.now()
#         }
#         return Response(
#             json.dumps(response_data, default=str),
#             status=code,
#             mimetype='application/json',
#             headers={
#                 'Content-Type': 'application/json',
#                 'Access-Control-Allow-Origin': '*'
#             }
#         )
#
#     @http.route('/api/v1/status', type='http', auth='public', methods=['GET'], csrf=False)
#     def api_status(self):
#         """Endpoint de estado de la API"""
#         return self._response_success({
#             'api_version': '1.0',
#             'odoo_version': '18.0',
#             'status': 'operational'
#         })
#
#     @http.route('/api/v1/auth/login', type='http', auth='public', methods=['POST'], csrf=False)
#     def api_login(self):
#         """Endpoint para login y obtener token"""
#         try:
#             data = json.loads(request.httprequest.data)
#             login = data.get('login')
#             password = data.get('password')
#
#             if not login or not password:
#                 return self._response_error(400, 'Datos incompletos', 'Se requiere login y password')
#
#             # Autenticar usuario
#             user_id = request.env['res.users'].sudo().authenticate(
#                 request.env.cr.dbname,
#                 login,
#                 password,
#                 {}
#             )
#
#             if not user_id:
#                 return self._response_error(401, 'Credenciales inválidas', 'Usuario o contraseña incorrectos')
#
#             # Buscar o crear token para el usuario
#             token_record = request.env['apn.api.token'].sudo().search([
#                 ('user_id', '=', user_id),
#                 ('active', '=', True),
#                 '|',
#                 ('expiration_date', '=', False),
#                 ('expiration_date', '>', datetime.now())
#             ], limit=1)
#
#             if not token_record:
#                 token_record = request.env['apn.api.token'].sudo().create({
#                     'name': f'Token for {login}',
#                     'user_id': user_id,
#                 })
#
#             user = request.env['res.users'].browse(user_id)
#
#             return self._response_success({
#                 'token': token_record.token,
#                 'expiration': token_record.expiration_date,
#                 'user': {
#                     'id': user.id,
#                     'name': user.name,
#                     'email': user.email or user.login
#                 }
#             })
#
#         except json.JSONDecodeError:
#             return self._response_error(400, 'JSON inválido', 'El cuerpo de la petición no es JSON válido')
#         except Exception as e:
#             _logger.error(f'Error en login: {str(e)}')
#             return self._response_error(500, 'Error interno', str(e))
#
#     @http.route('/api/v1/user/info', type='http', auth='public', methods=['GET'], csrf=False)
#     @validate_token
#     def api_user_info(self):
#         """Endpoint para obtener información del usuario autenticado"""
#         try:
#             user = request.env.user
#             return self._response_success({
#                 'id': user.id,
#                 'name': user.name,
#                 'email': user.email or user.login,
#                 'login': user.login,
#                 'company': {
#                     'id': user.company_id.id,
#                     'name': user.company_id.name
#                 } if user.company_id else None
#             })
#         except Exception as e:
#             _logger.error(f'Error obteniendo info de usuario: {str(e)}')
#             return self._response_error(500, 'Error interno', str(e))
#
#     @http.route('/api/v1/pilates/centers', type='http', auth='public', methods=['GET'], csrf=False)
#     @validate_token
#     def api_pilates_centers(self):
#         """Endpoint de ejemplo: Listar centros de pilates"""
#         try:
#             # Este es un ejemplo. Deberías ajustarlo a tus modelos reales
#             centers = [
#                 {'id': 1, 'name': 'Centro Pilates Norte', 'location': 'Zona Norte'},
#                 {'id': 2, 'name': 'Centro Pilates Sur', 'location': 'Zona Sur'},
#                 {'id': 3, 'name': 'Centro Pilates Centro', 'location': 'Centro'},
#             ]
#             return self._response_success(centers)
#         except Exception as e:
#             return self._response_error(500, 'Error interno', str(e))
#
#     @http.route('/api/v1/pilates/classes', type='http', auth='public', methods=['GET'], csrf=False)
#     @validate_token
#     def api_pilates_classes(self):
#         """Endpoint de ejemplo: Listar clases disponibles"""
#         try:
#             classes = [
#                 {'id': 1, 'name': 'Pilates Reformer', 'duration': '60 min', 'level': 'Intermedio'},
#                 {'id': 2, 'name': 'Pilates Mat', 'duration': '45 min', 'level': 'Básico'},
#                 {'id': 3, 'name': 'Pilates Avanzado', 'duration': '90 min', 'level': 'Avanzado'},
#             ]
#             return self._response_success(classes)
#         except Exception as e:
#             return self._response_error(500, 'Error interno', str(e))
#
#     @http.route('/api/v1/token/refresh', type='http', auth='public', methods=['POST'], csrf=False)
#     @validate_token
#     def api_refresh_token(self):
#         """Endpoint para refrescar token"""
#         try:
#             user = request.env.user
#             token_record = request.env['apn.api.token'].sudo().search([
#                 ('user_id', '=', user.id),
#                 ('active', '=', True)
#             ], limit=1)
#
#             if token_record:
#                 # Generar nuevo token
#                 new_token = request.env['apn.api.token'].sudo().create({
#                     'name': f'Token for {user.login}',
#                     'user_id': user.id,
#                 })
#
#                 # Desactivar token anterior
#                 token_record.write({'active': False})
#
#                 return self._response_success({
#                     'token': new_token.token,
#                     'expiration': new_token.expiration_date
#                 })
#
#             return self._response_error(404, 'Token no encontrado', 'No se encontró un token activo para este usuario')
#
#         except Exception as e:
#             return self._response_error(500, 'Error interno', str(e))

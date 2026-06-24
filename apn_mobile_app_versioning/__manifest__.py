{
    'name': 'APN - Pilates Mobile App Versioning',
    'version': '18.0.0.0.0',
    'category': 'Tools',
    'summary': 'Manage versions and releases for mobile applications',
    'description': """
        Control de versiones para aplicaciones móviles.
        Permite gestionar versiones, plataformas configurables, fechas, URLs y notas.
    """,
    'depends': [
        'base',
        'web',
        'apn_group',
        'apn_company',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/platform_data.xml',
        'views/mobile_platform_views.xml',
        'views/mobile_version_views.xml',
        'views/menu_views.xml',
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
    "sequence": 1,
}
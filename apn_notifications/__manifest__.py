{
    "name": "APN - Pilates Notifications",
    "version": "18.0.0.0.0",
    "author": "IdooGroup",
    "website": "https://www.idoogroup.com",
    "license": "LGPL-3",
    'depends': [
        'base',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/fcm_device_views.xml',
        'views/res_config_settings_views.xml',
        'views/menu_views.xml',
    ],
    'external_dependencies': {
        'python': ['firebase_admin'],
    },
    "installable": True,
    "auto_install": False,
    "application": True,
    "sequence": 1,
}
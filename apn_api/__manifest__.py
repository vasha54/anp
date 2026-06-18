{
    "name": "APN - Pilates API",
    "version": "18.0.0.0.0",
    'license': 'LGPL-3',
    "category": "API/Integration",
    'depends': [
        'base',
        'web',
        'apn_group',
        'apn_notifications',
    ],
    'data': [
        "data/ir_cron.xml",
        'views/swagger_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            "apn_api/static/src/swagger/swagger-ui.css",
            # "apn_api/static/src/swagger/swagger-ui-bundle.js",
            # "apn_api/static/src/swagger/swagger-ui-standalone-preset.js",
        ],
        'web.assets_frontend': [
            "apn_api/static/src/swagger/swagger-ui.css",
            # "apn_api/static/src/swagger/swagger-ui-bundle.js",
            # "apn_api/static/src/swagger/swagger-ui-standalone-preset.js",
        ],
    },
    "installable": True,
    "auto_install": False,
    "application": True,
    "sequence": 1,
}
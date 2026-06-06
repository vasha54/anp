{
    "name": "APN - Pilates Groups & Users",
    "version": "18.0.0.0.0",
    'depends': [
        'base',
        'web',
        'sales_team',
        'sale',
    ],
    'data': [
        # Archivos de seguridad
        'security/apn_groups.xml',
        "data/apn_user.xml",
        "views/res_groups_views.xml",
        "views/res_users_views.xml",
        "views/views_menu.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
    "sequence": 1,
}
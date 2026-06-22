{
    "name": "APN - Pilates Signup",
    "version": "18.0.0.0.0",
    'category': 'Authentication',
    'depends': [
        'base',
        'auth_signup',
        'auth_oauth',
        'apn_group',
    ],
    "data": [
        'data/ir_config_parameter.xml',
        'data/ir_cron.xml',
        'templates/email_template_user_activation.xml',
        'templates/email_template_password_reset.xml',
        'views/res_users_views.xml',
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
    "sequence": 1,
}
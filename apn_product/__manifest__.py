{
    "name": "APN - Pilates Product",
    "version": "18.0.0.0.0",
    'depends': [
        'base',
        'web',
        'product',
        'apn_group',
    ],
    'data': [
        'data/data_product_category.xml',
        'views/classes_product_views.xml',
        'views/membership_product_views.xml',
        'views/accessories_product_views.xml',
        'views/product_tag_views.xml',
        'views/menu_views.xml',
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
    "sequence": 1,
}
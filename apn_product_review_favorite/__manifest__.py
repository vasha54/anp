{
    "name": "APN - Pilates Product Review Favorite",
    "version": "18.0.0.0.0",
    'depends': [
        'base',
        'web',
        'product',
        'rating',
    ],
    'data': [
        'views/product_product_rating_views.xml',
        'views/product_template_rating_views.xml',
        'views/menu_views.xml',
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
    "sequence": 1,
}
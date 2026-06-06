import logging

_logger = logging.getLogger(__name__)

def post_init_hook(env):
    _logger.info("Ejecutando post_init_hook sc_base")
    env["res.company"].sudo()._set_default_company()

def post_update_hook(env):
    _logger.info("Ejecutando post_update_hook sc_base")
    env["res.company"].sudo()._set_default_company()

import logging
_logger = logging.getLogger(__name__)

# Lista de módulos cuyos grupos serán renombrados.
# Agrega aquí los nombres técnicos de los addons que quieras procesar.
MODULES_TO_PREFIX = ['event','event_product']


def set_noupdate_groups(env):
    for module_name in MODULES_TO_PREFIX:
        env.cr.execute(f"UPDATE ir_model_data SET noupdate = TRUE WHERE module = '{module_name}' AND model = 'res.groups' AND noupdate = FALSE")
    env.cr.commit()
    _logger.info("Filas actualizadas: %s", env.cr.rowcount)
    _logger.info("=== FIN HOOK ===")

def rename_groups_with_module_prefix(env):
    """
    Para cada módulo en MODULES_TO_PREFIX, busca sus res.groups
    y renombra con el formato: '<nombre_del_modulo> <nombre_actual_grupo>'
    si es que el grupo aún no tiene ese prefijo.
    """
    groups_model = env['res.groups'].sudo()
    data_model = env['ir.model.data'].sudo()

    for module_name in MODULES_TO_PREFIX:
        # Busca todos los xml_id de ese módulo que apunten a res.groups
        xml_ids = data_model.search([
            ('module', '=', module_name),
            ('model', '=', 'res.groups'),
        ])
        if not xml_ids:
            _logger.info("No se encontraron grupos para el módulo '%s'", module_name)
            continue

        prefijo = module_name.title()  # O puedes usar module_name directamente, p.ej. 'hr', 'account'

        for xml_id in xml_ids:
            grupo_id = xml_id.res_id
            grupo = groups_model.browse(grupo_id)
            if not grupo:
                continue

            # Nombre antiguo
            old_name = grupo.name
            new_name = f"{prefijo} {old_name}"

            # Si el nombre ya empieza con el prefijo, lo saltamos para evitar doble renombrado
            if old_name.startswith(f"{prefijo} "):
                _logger.debug("El grupo '%s' (xml_id=%s.%s) ya tiene el prefijo.",
                              old_name, module_name, xml_id.name)
                continue

            # Verificar que no exista otro grupo con el nuevo nombre (colisión con otros módulos)
            existing = groups_model.search([
                ('name', '=', new_name),
                ('id', '!=', grupo.id),
            ], limit=1)
            if existing:
                _logger.error(
                    "No se puede renombrar '%s' a '%s': otro grupo ya tiene ese nombre (id=%s).",
                    old_name, new_name, existing.id)
                continue

            # Aplicar nuevo nombre
            grupo.name = new_name
            _logger.info("Grupo renombrado: '%s' -> '%s' (módulo '%s')",
                         old_name, new_name, module_name)

    env.cr.commit()

def adjust_addons_parents(env):
    rename_groups_with_module_prefix(env)
    set_noupdate_groups(env)
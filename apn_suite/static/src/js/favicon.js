/** @odoo-module **/

import { loadJS, loadXML } from "@web/core/assets";
import { session } from "@web/session";

// Función para cambiar el favicon
function changeFavicon() {
    const faviconPath = '/apn_suite/static/src/img/favicon.ico';

    // Remover todos los favicons existentes
    const existingIcons = document.querySelectorAll('link[rel*="icon"]');
    existingIcons.forEach(icon => icon.remove());

    // Crear nuevo favicon
    const link = document.createElement('link');
    link.type = 'image/x-icon';
    link.rel = 'shortcut icon';
    link.href = faviconPath;
    document.head.appendChild(link);

    // Para compatibilidad
    const link2 = document.createElement('link');
    link2.type = 'image/x-icon';
    link2.rel = 'icon';
    link2.href = faviconPath;
    document.head.appendChild(link2);
}

// Ejecutar cuando se cargue el DOM
document.addEventListener('DOMContentLoaded', function() {
    changeFavicon();
});

// También ejecutar después de un tiempo por si es una carga dinámica
setTimeout(changeFavicon, 1000);
setTimeout(changeFavicon, 3000);
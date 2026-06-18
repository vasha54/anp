odoo.define('apn_suite.hide_login_elements', function (require) {
    'use strict';

    var core = require('web.core');
    var publicWidget = require('web.public.widget');

    var _t = core._t;

    publicWidget.registry.HideLoginElements = publicWidget.Widget.extend({
        selector: '.oe_login_form',

        start: function () {
            this._super.apply(this, arguments);
            this._hideElements();
            return this;
        },

        _hideElements: function () {
            var self = this;
            // Ejecutar después de que todo esté cargado
            setTimeout(function () {
                // Ocultar "Login as Admin/Demo/Portal"
                $('a[data-username]').parent().parent().parent().hide();
                $('a[data-username]').hide();
                $('.btn-group-sm').hide();

                // Ocultar "Log in with Odoo.com"
                $('.o_login_auth').hide();
                $('a[href*="odoo.com"]').hide();
                $('a[href*="auth_oauth"]').hide();

                // Eliminar completamente del DOM
                $('a[data-username]').remove();
                $('.o_login_auth').remove();
                $('a[href*="odoo.com"]').remove();

                console.log('✅ Elementos del login ocultados exitosamente');
            }, 200);

            // También ejecutar cuando el DOM cambie
            var observer = new MutationObserver(function(mutations) {
                self._hideElements();
            });

            observer.observe(document.body, { childList: true, subtree: true });
        },
    });

    return publicWidget.registry.HideLoginElements;
});
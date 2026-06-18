/** @odoo-module **/
import { Component } from "@odoo/owl";

export class KPICard extends Component {
    static template = "apn_suite.KPICardTemplate";
    static props = {
        title: { type: String },
        value: { type: String },
        icon: { type: String },
        trend: { type: Number, optional: true },
        trendLabel: { type: String, optional: true },
        color: { type: String, optional: true },
        isLoading: { type: Boolean, optional: true },
    };

    setup() {
        // Ya no necesitamos lógica adicional, todo se maneja con CSS
    }
}
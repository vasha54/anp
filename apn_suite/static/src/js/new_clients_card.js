/** @odoo-module **/
import { Component } from "@odoo/owl";
import { KPICard } from "./kpi_card";

export class NewClientsCard extends Component {
    static template = "apn_suite.NewClientsCardTemplate";
    static components = { KPICard };

    static props = {
        newClients: { type: Number, optional: true },
        trend: { type: Number, optional: true },
        isLoading: { type: Boolean, optional: true },
    };

    get formattedValue() {
        if (this.props.newClients === undefined || this.props.newClients === null) {
            return '--';
        }
        return `+${this.props.newClients}`;
    }
}
/** @odoo-module **/
import { Component } from "@odoo/owl";
import { KPICard } from "./kpi_card";

export class OccupancyCard extends Component {
    static template = "apn_suite.OccupancyCardTemplate";
    static components = { KPICard };

    static props = {
        occupancyRate: { type: Number, optional: true },
        trend: { type: Number, optional: true },
        isLoading: { type: Boolean, optional: true },
    };

    get formattedValue() {
        if (this.props.occupancyRate === undefined || this.props.occupancyRate === null) {
            return '--';
        }
        return `${Math.round(this.props.occupancyRate)}%`;
    }
}
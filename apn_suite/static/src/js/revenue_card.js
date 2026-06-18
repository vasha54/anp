/** @odoo-module **/
import { Component } from "@odoo/owl";
import { KPICard } from "./kpi_card";

export class RevenueCard extends Component {
    static template = "apn_suite.RevenueCardTemplate";
    static components = { KPICard };

    static props = {
        totalRevenue: { type: Number, optional: true },
        trend: { type: Number, optional: true },
        isLoading: { type: Boolean, optional: true },
    };

    get formattedValue() {
        if (this.props.totalRevenue === undefined || this.props.totalRevenue === null) {
            return '--';
        }
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(this.props.totalRevenue);
    }
}
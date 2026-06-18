/** @odoo-module **/
import { Component } from "@odoo/owl";
import { KPICard } from "./kpi_card";

export class ClassesCard extends Component {
    static template = "apn_suite.ClassesCardTemplate";
    static components = { KPICard };

    static props = {
        totalClasses: { type: Number, optional: true },
        trend: { type: Number, optional: true },
        isLoading: { type: Boolean, optional: true },
    };

    get formattedValue() {
        if (this.props.totalClasses === undefined || this.props.totalClasses === null) {
            return '--';
        }
        return this.props.totalClasses.toString();
    }
}
/** @odoo-module **/
import { Component, useState } from "@odoo/owl"
import { registry } from "@web/core/registry"
import { useService } from "@web/core/utils/hooks"
import { MultiLineChart } from "@apn_charts/js/multiline_chart"
const actionRegistry = registry.category("actions")

export class CardInfoWeeklyAttendanceTrend extends Component {

     static components = {
        MultiLineChart,
    }
    // EXPORT
    setup() {
        console.log("CardInfoWeeklyAttendanceTrend mounted")
        this.actionService = useService("action")
        this.ormService = useService("orm")
        this.state = useState({
           chartData: {
                labels: ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'],
                datasets: [
                    { label: 'Yoga', values: [25, 30, 28, 35, 40, 20, 8], color: '#9b59b6' },
                    { label: 'Pilates', values: [20, 22, 20, 23, 22, 18, 7], color: '#4154f1' },
                    { label: 'Spinning', values: [15, 18, 22, 25, 30, 15, 5], color: '#e74c3c' },
                    { label: 'CrossFit', values: [10, 12, 15, 18, 20, 10, 3], color: '#51cf66' },
                ]
            },
            chartOptions: {
                position_legend: 'bottom'
            }

        });
        this._loadCardData()
    }

    async _loadCardData() {

    }
}

CardInfoWeeklyAttendanceTrend.template = "apn_suite.CardInfoWeeklyAttendanceTrendTemplate"
CardInfoWeeklyAttendanceTrend.props = {

}

// También regístralo globalmente
registry.category("components").add("CardInfoWeeklyAttendanceTrend", CardInfoWeeklyAttendanceTrend)

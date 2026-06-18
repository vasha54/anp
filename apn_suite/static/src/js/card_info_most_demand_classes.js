/** @odoo-module **/
import { Component, useState } from "@odoo/owl"
import { registry } from "@web/core/registry"
import { useService } from "@web/core/utils/hooks"
import { BarVChart } from "@apn_charts/js/bar_chart"
const actionRegistry = registry.category("actions")

export class CardInfoMostDemandClasses extends Component {

     static components = {
        BarVChart,
    }
    // EXPORT
    setup() {
        console.log("CardInfoMostDemandClasses mounted")
        this.actionService = useService("action")
        this.ormService = useService("orm")
        this.state = useState({
           chartData: {
                labels: ['Yoga', 'Pilates', 'Spinning', 'CrossFit', 'Zumba', 'Boxing'],
                values: [85, 72, 95, 68, 78, 55],
                colors: ['#9b59b6', '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#1abc9c']
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

CardInfoMostDemandClasses.template = "apn_suite.CardInfoMostDemandClassesTemplate"
CardInfoMostDemandClasses.props = {

}

// También regístralo globalmente
registry.category("components").add("CardInfoMostDemandClasses", CardInfoMostDemandClasses)

/** @odoo-module **/
import { Component, useState } from "@odoo/owl"
import { registry } from "@web/core/registry"
import { useService } from "@web/core/utils/hooks"
import { PieChart } from "@apn_charts/js/pie_chart"
const actionRegistry = registry.category("actions")

export class CardInfoDistributionRevenue extends Component {

     static components = {
        PieChart,
    }
    // EXPORT
    setup() {
        console.log("CardInfoDistributionRevenue mounted")
        this.actionService = useService("action")
        this.ormService = useService("orm")
        this.state = useState({
            chartData: {
                labels: ['Phone', 'Email', 'Web', 'In Person'],
                values: [60, 100, 120, 34],
                colors: ['#71639e', '#0180a5', '#d23f3a', '#008818']
            },
            chartOptions: {
                position_legend: 'right'
            }

        });
        this._loadCardData()
    }

    async _loadCardData() {

    }
}

CardInfoDistributionRevenue.template = "apn_suite.CardInfoDistributionRevenueTemplate"
CardInfoDistributionRevenue.props = {

}

// También regístralo globalmente
registry.category("components").add("CardInfoDistributionRevenue", CardInfoDistributionRevenue)

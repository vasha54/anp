/** @odoo-module **/
import { Component, useState } from "@odoo/owl"
import { registry } from "@web/core/registry"
import { useService } from "@web/core/utils/hooks"
const actionRegistry = registry.category("actions")

export class CardInfoBuildConstruction extends Component {
    // EXPORT
    setup() {
        console.log("CardInfoBuildConstruction mounted")
        this.actionService = useService("action")
        this.ormService = useService("orm")
        this.state = useState({


        });
        this._loadCardData()
    }

    async _loadCardData() {
        // try {
        //     const result = await this.ormService.call(
        //         "suite.dashboard",
        //         "get_count_residents",
        //         [],
        //         {}
        //     );
        //     this.state.countResidents = result.count_residents;
        //     console.log("Filter residence data:", result);
        // } catch (error) {
        //     console.error("Error loading filter residence data", error);
        // }
    }
}

CardInfoBuildConstruction.template = "apn_suite.CardInfoBuildConstructionTemplate"
CardInfoBuildConstruction.props = {
     title_card: { type: String, optional: true },
}

// También regístralo globalmente
registry.category("components").add("CardInfoBuildConstruction", CardInfoBuildConstruction)

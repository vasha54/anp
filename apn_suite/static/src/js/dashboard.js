/** @odoo-module **/
import { registry } from "@web/core/registry"
import { useService } from "@web/core/utils/hooks"
import {
    Component,
    onMounted,
    useState,
} from "@odoo/owl"
import {CardInfoBuildConstruction} from "./card_info_build_construction";

const actionRegistry = registry.category("actions")

class APNDashboard extends Component {
    static components = {
        CardInfoBuildConstruction
    }

    setup() {
        this.ormService = useService("orm")
        this.actionService = useService("action")


        this.state = useState({
            user_name: "",
            user_email: "",
        })

        onMounted(() => {
            this._loadUserData()
            this._loadData()
        })
    }

    async _loadUserData() {
        try {
            

            console.log("Usuario cargado:", this.state.user_name, this.state.user_email);

        } catch (error) {
            console.error("Error loading user data:", error);
            this.state.user_name = "Usuario";
            this.state.user_email = "";
        }
    }

    async _loadData() {
        console.log("Dashboard cargado para:", this.state.user_name);
    }
}

APNDashboard.template = "apn_suite.APNDashboardTemplate"
actionRegistry.add("apn_dashboard_tag", APNDashboard)
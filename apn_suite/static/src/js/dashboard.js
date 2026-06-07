/** @odoo-module **/
import { registry } from "@web/core/registry"
import { useService } from "@web/core/utils/hooks"
import {
    Component,
    onMounted,
    useState,
} from "@odoo/owl"
import {CardInfoBuildConstruction} from "./card_info_build_construction";
import {DateFilterComponent} from "./date_filter_component";
import {OccupancyCard} from "./occupancy_card";
import {RevenueCard} from "./revenue_card";
import {ClassesCard} from "./classes_card";
import {NewClientsCard} from "./new_clients_card";
import {CardInfoDistributionRevenue} from "./card_info_distribution_revenue";
import {CardInfoMostDemandClasses} from "./card_info_most_demand_classes";
import {CardInfoWeeklyAttendanceTrend} from "./card_info_weekly_attendance_trend"

const actionRegistry = registry.category("actions")

class APNDashboard extends Component {
    static components = {
        CardInfoBuildConstruction,
        DateFilterComponent,
        OccupancyCard,
        RevenueCard,
        ClassesCard,
        NewClientsCard,
        CardInfoDistributionRevenue,
        CardInfoMostDemandClasses,
        CardInfoWeeklyAttendanceTrend,
    }

    setup() {
        this.ormService = useService("orm")
        this.actionService = useService("action")

        this.state = useState({
            user_name: "",
            user_email: "",
            filterData: null,
            kpis: {
                occupancyRate: null,
                occupancyTrend: null,
                totalRevenue: null,
                revenueTrend: null,
                totalClasses: null,
                classesTrend: null,
                newClients: null,
                clientsTrend: null,
            },
            isLoading: true,
        })

        // Bind del método para mantener el contexto
        this.onFilterChange = this.onFilterChange.bind(this);

        onMounted(() => {
            this._loadUserData()
            this._loadData()
        })
    }

    async _loadUserData() {
        try {
            const userInfo = await this.ormService.call(
                "res.users",
                "get_current_user_info",
                [],
                {}
            );

            console.log("User info desde backend:", userInfo);

            if (userInfo) {
                this.state.user_name = userInfo.user_name || "Usuario";
                this.state.user_email = userInfo.user_email || "";

                // Cargar preferencias de filtro guardadas
                if (userInfo.filter_period) {
                    this.state.filterData = {
                        period: userInfo.filter_period,
                        startDate: userInfo.filter_start_date,
                        endDate: userInfo.filter_end_date,
                    };
                    console.log("Preferencias de filtro cargadas:", this.state.filterData);
                }
            } else {
                this.state.user_name = "Usuario";
                this.state.user_email = "";
            }

        } catch (error) {
            console.error("Error loading user data:", error);
            this.state.user_name = "Usuario";
            this.state.user_email = "";
        }
    }

    async onFilterChange(filterData) {
        console.log('Filter applied:', filterData);
        this.state.filterData = filterData;

        // Guardar en el backend
        try {
            // Convertir las fechas a strings ISO
            const filterPayload = {
                period: filterData.period,
                startDate: filterData.startDate instanceof Date ?
                    filterData.startDate.toISOString().split('T')[0] :
                    String(filterData.startDate).split('T')[0],
                endDate: filterData.endDate instanceof Date ?
                    filterData.endDate.toISOString().split('T')[0] :
                    String(filterData.endDate).split('T')[0],
            };

            console.log('Enviando al backend:', filterPayload);

            // Llamada RPC correcta
            const result = await this.ormService.call(
                "res.users",
                "save_user_filter",
                [filterPayload],  // Pasar como primer argumento del array
                {}  // Sin kwargs
            );

            console.log("Resultado del guardado:", result);

        } catch (error) {
            console.error("Error guardando preferencias de filtro:", error);
        }

        // Recargar datos
        this._loadData();
    }

    async _loadDataORMParameters(_model, _method, _args, _filters) {
        var data = null
        try {
            const result = await this.ormService.call(
                _model,
                _method,
                _args,
                _filters
            )
            data = result.data ? result.data.toString() : JSON.stringify(result)
            console.log("Response", _model, _method, ":", result)
        } catch (error) {
            console.error("Error loading ", _model, _method, ":", error)
        }
        return data
    }

    async _loadData() {
        this.state.isLoading = true;

        // Simular carga de datos (reemplazar con llamadas reales al backend)
        setTimeout(() => {
            this.state.kpis = {
                occupancyRate: 75,
                occupancyTrend: 5.2,
                totalRevenue: 125000,
                revenueTrend: -2.1,
                totalClasses: 248,
                classesTrend: 8.5,
                newClients: 45,
                clientsTrend: 12.3,
            };
            this.state.isLoading = false;
        }, 1000);

        console.log("Dashboard cargado para:", this.state.user_name);

    }
}

APNDashboard.template = "apn_suite.APNDashboardTemplate"
actionRegistry.add("apn_dashboard_tag", APNDashboard)
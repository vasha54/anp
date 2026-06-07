import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, onWillUnmount, onPatched, useState, useRef } from "@odoo/owl";
const actionRegistry = registry.category("actions");

export class PolarAreaChart extends Component {
    setup() {
        this.canvasRef = useRef("canvaChart");
        this.chart = null;
        this.actionService = useService("action");
        this.ormService = useService("orm");
        this.state = useState({
            loading: true,
            hasData: false,
            labels: [],
            dataset:[],
        });
        
        onMounted(() => this._init());
        onPatched(() => this._maybeRenderChart());
        onWillUnmount(() => this._destroyChart());
    }

    // ------------------------------------------------------------
    // Ciclo de vida
    // ------------------------------------------------------------

    async _init() {
        await this._ensureChartJs();
        await this._loadData();
    }

    _destroyChart() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }

    // ------------------------------------------------------------
    // Chart.js
    // ------------------------------------------------------------

    async _ensureChartJs() {
        if (window.Chart) {
            return;
        }

        await new Promise((resolve, reject) => {
            const script = document.createElement("script");
            script.src = "/apn_charts/static/lib/chart.js/chart.umd.min.js";
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    _maybeRenderChart() {
        if (
            !this.state.loading &&
            this.state.hasData &&
            this.canvasRef.el &&
            !this.chart
        ) {
            this._renderChart();
        }
    }

    // ------------------------------------------------------------
    // Data
    // ------------------------------------------------------------

    async _loadData() {
        // const result = await this.ormService.call(
        //     "suite.dashboard",
        //     "get_week_appointments",
        //     [],
        //     {}
        // );

        // this.state.labels = result.labels;
        // this.state.hasData = result.has_data;
        // this.state.dataset = result.dataset;
        // this.state.loading = false;
        // console.log("Data Bar Char appointments:", result);
    }

    

    _renderChart() {
        // if (!this.state.hasData || !this.canvasRef.el) {
        //     return;
        // }

        // this._destroyChart();

        // const ctx = this.canvasRef.el.getContext("2d");

        // const data = {
        //         labels: this.state.labels,
        //         datasets: this.state.dataset,
        //     };
        
        // const config = {
        //         type: 'bar',
        //         data: data,
        //         options: {
        //             responsive: true,
        //             maintainAspectRatio: false, // Esto permite que ocupe todo el ancho
        //             layout: {
        //                 padding: {
        //                     left: 0,
        //                     right: 0,
        //                     top: 0,
        //                     bottom: 0
        //                 }
        //             },
        //             plugins: {
        //                 legend: {
        //                     position: 'bottom',
        //                 },
        //                 title: {
        //                     display: false,
        //                     text: 'Citas Médicas - Próximos 7 Días'
        //                 }
        //             },
        //             scales: {
        //                 x: {
        //                     title: {
        //                         display: false,
        //                         text: 'Días'
        //                     },
        //                     grid: {
        //                         display: true
        //                     }
        //                     // Para una escala de tiempo más precisa, puedes usar:
        //                     // type: 'time',
        //                     // time: { unit: 'day', tooltipFormat: 'DD MMM' }
        //                 },
        //                 y: {
        //                     beginAtZero: true,
        //                     title: {
        //                         display: true,
        //                         text: 'Cantidad de Consultas' 
        //                     },
        //                     ticks: {
        //                         stepSize: 1 // Asegura valores enteros
        //                     },
        //                     grid: {
        //                         display: false
        //                     }
        //                 }
        //             }
        //         }
        //     };

        //     // 5. Crea la gráfica
        //     this.chart = new Chart(ctx, config);
    }
    
    
}

PolarAreaChart.template = "apn_charts.PolarAreaChartTemplate";

// También regístralo globalmente
registry.category("components").add("PolarAreaChart", PolarAreaChart);
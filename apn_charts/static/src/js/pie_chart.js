import { registry } from "@web/core/registry"
import {
    Component,
    onMounted,
    onWillUnmount,
    onWillUpdateProps,
    onPatched,
    useState,
    useRef,
} from "@odoo/owl"

export class PieChart extends Component {
    setup() {
        this.canvasRef = useRef("canvaChart")
        this.chart = null
        this.state = useState({
            loading: true,
            hasData: false,
            chartData: null,
            legendPosition: 'right',
        })
        this._shouldRender = false

        onMounted(() => this._init())
        onWillUpdateProps((nextProps) => {
            // Comparar datos anteriores con los nuevos para decidir si recargar
            const oldData = this._getChartDataFromProps(this.props)
            const newData = this._getChartDataFromProps(nextProps)
            if (JSON.stringify(oldData) !== JSON.stringify(newData)) {
                this._onRecordChange()
            }
        })
        onPatched(() => this._onPatched())
        onWillUnmount(() => this._destroyChart())
    }

    async _init() {
        await this._ensureChartJs()
        this._loadData()
        this._shouldRender = true
    }

    _onRecordChange() {
        this._destroyChart()
        this.state.loading = true
        this.state.hasData = false
        this._shouldRender = false
        this._loadData()
        this._shouldRender = true
    }

    _onPatched() {
        if (this._shouldRender) {
            this._renderChart()
            this._shouldRender = false
        }
    }

    _destroyChart() {
        if (this.chart) {
            this.chart.destroy()
            this.chart = null
        }
    }

    async _ensureChartJs() {
        if (window.Chart) return
        return new Promise((resolve, reject) => {
            const script = document.createElement("script")
            script.src =
                "/apn_charts/static/lib/chart.js/chart.umd.min.js"
            script.onload = resolve
            script.onerror = reject
            document.head.appendChild(script)
        })
    }

    // Método auxiliar para extraer datos de props (record+name o data directo)
    _getChartDataFromProps(props) {
        // Prioridad 1: props.data directo
        if (props.data && props.data.labels && props.data.values && props.data.colors) {
            return props.data
        }
        // Prioridad 2: desde un campo del record
        if (props.record && props.name) {
            const fieldValue = props.record.data[props.name]
            if (fieldValue) {
                try {
                    return JSON.parse(fieldValue)
                } catch (e) {
                    console.error("Error parsing chart data from record:", e)
                    return null
                }
            }
        }
        return null
    }

    _loadData() {
        const chartData = this._getChartDataFromProps(this.props)
        this.state.legendPosition = this.props.options?.position_legend || "right"

        if (!chartData) {
            this.state.hasData = false
            this.state.loading = false
            return
        }

        // Validar estructura
        if (
            chartData.labels &&
            chartData.values &&
            chartData.colors &&
            chartData.labels.length > 0 &&
            chartData.values.length > 0
        ) {
            this.state.chartData = chartData
            this.state.hasData = true
        } else {
            this.state.hasData = false
        }
        this.state.loading = false
    }

    _renderChart() {
        if (!this.state.hasData || !this.canvasRef.el) return
        if (typeof Chart === "undefined") return

        const canvas = this.canvasRef.el
        canvas.width = canvas.clientWidth || 500
        canvas.height = canvas.clientHeight || 250

        const ctx = canvas.getContext("2d")
        this._destroyChart()

        const { labels, values, colors } = this.state.chartData

        this.chart = new Chart(ctx, {
            type: "pie",
            data: {
                labels: labels,
                datasets: [
                    {
                        data: values,
                        backgroundColor: colors,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: this.state.legendPosition,
                        align: "start",
                        labels: {
                            boxWidth: 20,
                            font: { size: 12, weight: "normal" },
                            color: "#333",
                            usePointStyle: true,
                        },
                    },
                    tooltip: {
                        enabled: true,
                        callbacks: {
                            label: function (context) {
                                const label = context.label || ""
                                const valor = context.raw
                                const total = context.dataset.data.reduce(
                                    (acc, val) => acc + val,
                                    0
                                )
                                const porcentaje = (
                                    (valor / total) *
                                    100
                                ).toFixed(1)
                                return ` ${valor} (${porcentaje}%)`
                            },
                        },
                        backgroundColor: "rgba(0,0,0,0.7)",
                        titleColor: "#ffcc00",
                        bodyColor: "#fff",
                    },
                },
            },
        })
    }
}

PieChart.template = "apn_charts.PieChartTemplate"
registry.category("components").add("PieChart", PieChart)
registry.category("fields").add("pie_chart", { component: PieChart })

export { PieChart };
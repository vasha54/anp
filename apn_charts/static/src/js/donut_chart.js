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

export class DonutChart extends Component {
    setup() {
        this.canvasRef = useRef("canvaChart")
        this.chart = null
        this.state = useState({
            loading: true,
            hasData: false,
            chartData: null,
            legendPosition: 'right',
        })

        // Bandera para saber si debemos renderizar después del patched
        this._shouldRender = false

        onMounted(() => this._init())
        onWillUpdateProps(() => this._onRecordChange())
        onPatched(() => this._onPatched())
        onWillUnmount(() => this._destroyChart())
    }

    async _init() {
        await this._ensureChartJs()
        this._loadData()
        this._shouldRender = true
        // No renderizamos aquí directamente, lo haremos en el primer patched
    }

    _onRecordChange() {
        // Cuando cambia el registro, destruimos el gráfico y reiniciamos estado
        this._destroyChart()
        this.state.loading = true
        this.state.hasData = false
        this._shouldRender = false
        this._loadData() // actualiza state con nuevos datos
        this._shouldRender = true // marcamos para renderizar en el próximo patched
    }

    _onPatched() {
        // El DOM ya está actualizado con el nuevo estado (loading, hasData, etc.)
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
        this.state.legendPosition = this.props.options?.position_legend || "right";

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
            type: "doughnut",
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
                        position: this.state.legendPosition, // ← Posición: 'top', 'left', 'bottom', 'right'.
                        align: "start", // ← Alineación dentro de la posición: 'start', 'center', 'end'.
                        labels: {
                            boxWidth: 20, // ← Ancho de la caja de color de la leyenda.
                            font: { size: 12, weight: "normal" }, // ← Estilo de la fuente.
                            color: "#333", // ← Color del texto.
                            usePointStyle: true, // ← Usa un círculo en lugar de un rectángulo en la leyenda.
                        },
                    },
                    tooltip: {
                        enabled: true, // ← Habilita o deshabilita los tooltips.
                        callbacks: {
                            // ← Personaliza el contenido del tooltip.
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
                        backgroundColor: "rgba(0,0,0,0.7)", // ← Fondo del tooltip.
                        titleColor: "#ffcc00", // ← Color del título.
                        bodyColor: "#fff", // ← Color del cuerpo.
                    },
                },
            },
        })
    }
}

DonutChart.template = "apn_charts.DonutChartTemplate"
registry.category("components").add("DonutChart", DonutChart)
registry.category("fields").add("donut_chart", { component: DonutChart })

export { DonutChart };

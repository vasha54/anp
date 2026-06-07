/** @odoo-module **/
import { registry } from "@web/core/registry"
import { Component, onMounted, onWillUnmount, onWillUpdateProps, onPatched, useState, useRef } from "@odoo/owl"

export class AreaChart extends Component {

    setup() {
        this.canvasRef = useRef("canvaChart")
        this.chart = null
        this.state = useState({
            loading: true,
            hasData: false,
            chartData: null,
            legendPosition: "bottom",
        })
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
            script.src = "/apn_charts/static/lib/chart.js/chart.umd.min.js"
            script.onload = resolve
            script.onerror = reject
            document.head.appendChild(script)
        })
    }

    _getChartDataFromProps(props) {
        if (props.data && props.data.labels && props.data.values) {
            return props.data
        }
        if (props.record && props.name) {
            const fieldValue = props.record.data[props.name]
            if (fieldValue) {
                try { return JSON.parse(fieldValue) }
                catch (e) { console.error("Error parsing chart data:", e); return null }
            }
        }
        return null
    }

    _loadData() {
        const chartData = this._getChartDataFromProps(this.props)
        this.state.legendPosition = this.props.options?.position_legend || "bottom"
        if (!chartData) {
            this.state.hasData = false
            this.state.loading = false
            return
        }
        if (chartData.labels && chartData.values &&
            chartData.labels.length > 0 && chartData.values.length > 0) {
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

        const { labels, values } = this.state.chartData
        const lineColor = this.props.options?.lineColor || '#4154f1'
        const areaColor = this.props.options?.areaColor || lineColor

        // Crear gradiente para el área
        let gradientFill = areaColor + '20' // 20 = 12% opacidad
        if (this.props.options?.useGradient !== false) {
            gradientFill = (context) => {
                const chart = context.chart
                const { ctx, chartArea } = chart
                if (!chartArea) return areaColor + '20'
                const gradient = ctx.createLinearGradient(0, chartArea.bottom, 0, chartArea.top)
                gradient.addColorStop(0, areaColor + '05')
                gradient.addColorStop(0.5, areaColor + '20')
                gradient.addColorStop(1, areaColor + '40')
                return gradient
            }
        }

        this.chart = new Chart(ctx, {
            type: "line",
            data: {
                labels: labels,
                datasets: [{
                    label: this.props.options?.datasetLabel || "",
                    data: values,
                    borderColor: lineColor,
                    backgroundColor: gradientFill,
                    borderWidth: 2.5,
                    pointBackgroundColor: lineColor,
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    tension: 0.4,
                    fill: true, // IMPORTANTE: Rellenar área bajo la curva
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 750,
                },
                plugins: {
                    legend: {
                        display: true,
                        position: this.state.legendPosition,
                        align: "center",
                        onClick: (e, legendItem, legend) => { return false; },
                        labels: {
                            boxWidth: 30,
                            boxHeight: 3,
                            padding: 15,
                            font: { size: 12, weight: "normal" },
                            color: "#333",
                            usePointStyle: true,
                            pointStyleWidth: 30,
                            generateLabels: (chart) => {
                                const dataset = chart.data.datasets[0];
                                return [{
                                    text: dataset.label || 'Valores',
                                    fillStyle: dataset.borderColor,
                                    strokeStyle: dataset.borderColor,
                                    lineWidth: 2,
                                    hidden: false,
                                    index: 0,
                                    pointStyle: 'line',
                                }];
                            }
                        },
                    },
                    tooltip: {
                        enabled: true,
                        callbacks: {
                            label: (context) => {
                                const label = context.dataset.label || ''
                                const val = context.raw
                                return `${label ? label + ": " : ""}${val}`
                            },
                        },
                        backgroundColor: "rgba(0,0,0,0.7)",
                        titleColor: "#ffcc00",
                        bodyColor: "#fff",
                    },
                },
                scales: {
                    x: {
                        grid: {
                            display: false,
                        },
                        ticks: {
                            font: { size: 11 }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0,0,0,0.05)',
                        },
                        ticks: {
                            font: { size: 11 }
                        }
                    },
                },
            },
        })
    }
}

AreaChart.template = "apn_charts.AreaChartTemplate"
registry.category("components").add("AreaChart", AreaChart)
registry.category("fields").add("area_chart", { component: AreaChart })
export { AreaChart }
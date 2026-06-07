/** @odoo-module **/
import { registry } from "@web/core/registry"
import { Component, onMounted, onWillUnmount, onWillUpdateProps, onPatched, useState, useRef } from "@odoo/owl"

export class MultiLineChart extends Component {
    static template = "apn_charts.MultiLineChartTemplate"

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
        // Soporta datasets múltiples: { labels: [], datasets: [{ label, values, color }, ...] }
        if (props.data && props.data.labels && props.data.datasets) {
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
        if (chartData.labels && chartData.datasets &&
            chartData.labels.length > 0 && chartData.datasets.length > 0) {
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

        const { labels, datasets } = this.state.chartData

        // Construir datasets para Chart.js
        const chartDatasets = datasets.map((ds, index) => ({
            label: ds.label || `Dataset ${index + 1}`,
            data: ds.values,
            borderColor: ds.color || this._getDefaultColor(index),
            backgroundColor: 'transparent',
            borderWidth: 2.5,
            pointBackgroundColor: ds.color || this._getDefaultColor(index),
            pointBorderColor: '#ffffff',
            pointBorderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6,
            tension: 0.3,
            fill: false,
        }))

        this.chart = new Chart(ctx, {
            type: "line",
            data: {
                labels: labels,
                datasets: chartDatasets,
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 750,
                },
                interaction: {
                    mode: 'index',
                    intersect: false,
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
                        },
                    },
                    tooltip: {
                        enabled: true,
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: (context) => {
                                const label = context.dataset.label || ''
                                const val = context.raw
                                return `${label}: ${val}`
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

    _getDefaultColor(index) {
        const colors = [
            '#4154f1', '#ff6b6b', '#51cf66', '#ffa502',
            '#9775fa', '#339af0', '#ff6348', '#00b894'
        ]
        return colors[index % colors.length]
    }
}

MultiLineChart.template = "apn_charts.MultiLineChartTemplate"
registry.category("components").add("MultiLineChart", MultiLineChart)
registry.category("fields").add("multi_line_chart", { component: MultiLineChart })
export { MultiLineChart }
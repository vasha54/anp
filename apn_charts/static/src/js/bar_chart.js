import { registry } from "@web/core/registry"
import { Component, onMounted, onWillUnmount, onWillUpdateProps, onPatched, useState, useRef } from "@odoo/owl"

export class BarHChart extends Component {
    static template = "apn_charts.BarHChartTemplate"

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
        if (props.data && props.data.labels && props.data.values && props.data.colors) {
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
        if (chartData.labels && chartData.values && chartData.colors &&
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

        const { labels, values, colors } = this.state.chartData

        this.chart = new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: this.props.options?.datasetLabel || "",
                    data: values,
                    backgroundColor: colors,
                    borderColor: colors,
                    borderWidth: 1,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: "y",
                animation: {
                    duration: 750,
                    onComplete: function() {
                        // Estabilizar después de la animación
                    }
                },
                transitions: {
                    show: {
                        animations: {
                            x: { from: 0 },
                            y: { from: 0 }
                        }
                    },
                    hide: {
                        animations: {
                            x: { to: 0 },
                            y: { to: 0 }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: this.state.legendPosition,
                        align: "center",
                        // DESACTIVAR CLICK EN LA LEYENDA
                        onClick: (e, legendItem, legend) => {
                            // No hacer nada - previene el error
                            return false;
                        },
                        labels: {
                            boxWidth: 15,
                            boxHeight: 15,
                            padding: 15,
                            font: {
                                size: 12,
                                weight: "normal"
                            },
                            color: "#333",
                            usePointStyle: true,
                            pointStyleWidth: 10,
                            generateLabels: (chart) => {
                                const dataset = chart.data.datasets[0];
                                return chart.data.labels.map((label, i) => ({
                                    text: label,
                                    fillStyle: dataset.backgroundColor[i],
                                    strokeStyle: dataset.borderColor[i],
                                    lineWidth: 1,
                                    hidden: false,
                                    index: i,
                                    pointStyle: 'rectRounded',
                                }));
                            }
                        },
                    },
                    tooltip: {
                        enabled: true,
                        callbacks: {
                            label: (context) => {
                                const label = context.chart.data.labels[context.dataIndex]
                                const val = context.raw
                                const total = context.dataset.data.reduce((a, b) => a + b, 0)
                                const pct = ((val / total) * 100).toFixed(1)
                                return `${label}: ${val} (${pct}%)`
                            },
                        },
                        backgroundColor: "rgba(0,0,0,0.7)",
                        titleColor: "#ffcc00",
                        bodyColor: "#fff",
                    },
                },
                scales: {
                    x: { beginAtZero: true },
                },
            },
        })
    }
}

export class BarVChart extends Component {
    static template = "apn_charts.BarVChartTemplate"

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
        if (props.data && props.data.labels && props.data.values && props.data.colors) {
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
        if (chartData.labels && chartData.values && chartData.colors &&
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

        const { labels, values, colors } = this.state.chartData

        this.chart = new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: this.props.options?.datasetLabel || "",
                    data: values,
                    backgroundColor: colors,
                    borderColor: colors,
                    borderWidth: 1,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: "x",
                animation: {
                    duration: 750,
                },
                transitions: {
                    show: {
                        animations: {
                            x: { from: 0 },
                            y: { from: 0 }
                        }
                    },
                    hide: {
                        animations: {
                            x: { to: 0 },
                            y: { to: 0 }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: this.state.legendPosition,
                        align: "center",
                        // DESACTIVAR CLICK EN LA LEYENDA
                        onClick: (e, legendItem, legend) => {
                            // No hacer nada - previene el error
                            return false;
                        },
                        labels: {
                            boxWidth: 15,
                            boxHeight: 15,
                            padding: 15,
                            font: {
                                size: 12,
                                weight: "normal"
                            },
                            color: "#333",
                            usePointStyle: true,
                            pointStyleWidth: 10,
                            generateLabels: (chart) => {
                                const dataset = chart.data.datasets[0];
                                return chart.data.labels.map((label, i) => ({
                                    text: label,
                                    fillStyle: dataset.backgroundColor[i],
                                    strokeStyle: dataset.borderColor[i],
                                    lineWidth: 1,
                                    hidden: false,
                                    index: i,
                                    pointStyle: 'rectRounded',
                                }));
                            }
                        },
                    },
                    tooltip: {
                        enabled: true,
                        callbacks: {
                            label: (context) => {
                                const label = context.chart.data.labels[context.dataIndex]
                                const val = context.raw
                                const total = context.dataset.data.reduce((a, b) => a + b, 0)
                                const pct = ((val / total) * 100).toFixed(1)
                                return `${label}: ${val} (${pct}%)`
                            },
                        },
                        backgroundColor: "rgba(0,0,0,0.7)",
                        titleColor: "#ffcc00",
                        bodyColor: "#fff",
                    },
                },
                scales: {
                    y: { beginAtZero: true },
                },
            },
        })
    }
}

// Registros
registry.category("components").add("BarVChart", BarVChart)
registry.category("fields").add("bar_v_chart", { component: BarVChart })
registry.category("components").add("BarHChart", BarHChart)
registry.category("fields").add("bar_h_chart", { component: BarHChart })

export { BarVChart, BarHChart }
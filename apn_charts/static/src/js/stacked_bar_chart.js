/** @odoo-module **/
import { registry } from "@web/core/registry"
import { Component, onMounted, onWillUnmount, onWillUpdateProps, onPatched, useState, useRef } from "@odoo/owl"

export class StackedBarVChart extends Component {

    setup() {
        this.canvasRef = useRef("canvaChart")
        this.chart = null
        this.state = useState({
            loading: true,
            hasData: false,
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
        this._validateData()
        this._shouldRender = true
    }

    _onRecordChange() {
        this._destroyChart()
        this.state.loading = true
        this.state.hasData = false
        this._shouldRender = false
        this._validateData()
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

    _validateData() {
        const data = this._getChartDataFromProps(this.props)
        this.state.legendPosition = this.props.options?.position_legend || "bottom"

        if (!data || !data.labels || !data.datasets || data.labels.length === 0 || data.datasets.length === 0) {
            this.state.hasData = false
            this.state.loading = false
            return
        }

        // Comprobar que cada dataset tenga 'data' (array) y 'backgroundColor' (string o array)
        const valid = data.datasets.every(ds =>
            ds.data &&
            ds.data.length === data.labels.length &&
            ds.backgroundColor
        )
        this.state.hasData = valid
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

        const { labels, datasets } = this._getChartDataFromProps(this.props)

        // Mapear datasets a la estructura de Chart.js
        const chartDatasets = datasets.map(ds => ({
            label: ds.label || "",
            data: ds.data,
            backgroundColor: ds.backgroundColor,
            borderColor: ds.borderColor || ds.backgroundColor,
            borderWidth: 1,
        }))

        this.chart = new Chart(ctx, {
            type: "bar",
            data: { labels, datasets: chartDatasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: "x",                     // ← barras verticales
                plugins: {
                    legend: {
                        position: this.state.legendPosition,
                        align: "center",
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
                            label: (context) => {
                                const label = context.dataset.label || ""
                                const val = context.raw
                                // Porcentaje respecto al total del grupo (misma categoría)
                                const total = context.chart.data.datasets.reduce((sum, ds) => sum + (ds.data[context.dataIndex] || 0), 0)
                                const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0
                                return ` ${label}: ${val} (${pct}%)`
                            },
                        },
                        backgroundColor: "rgba(0,0,0,0.7)",
                        titleColor: "#ffcc00",
                        bodyColor: "#fff",
                    },
                },
                scales: {
                    x: { stacked: true },
                    y: { stacked: true, beginAtZero: true },
                },
            },
        })
    }
}


export class StackedBarHChart extends Component {

    setup() {
        this.canvasRef = useRef("canvaChart")
        this.chart = null
        this.state = useState({
            loading: true,
            hasData: false,
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
        this._validateData()
        this._shouldRender = true
    }

    _onRecordChange() {
        this._destroyChart()
        this.state.loading = true
        this.state.hasData = false
        this._shouldRender = false
        this._validateData()
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

    _validateData() {
        const data = this._getChartDataFromProps(this.props)
        this.state.legendPosition = this.props.options?.position_legend || "bottom"

        if (!data || !data.labels || !data.datasets || data.labels.length === 0 || data.datasets.length === 0) {
            this.state.hasData = false
            this.state.loading = false
            return
        }

        const valid = data.datasets.every(ds =>
            ds.data &&
            ds.data.length === data.labels.length &&
            ds.backgroundColor
        )
        this.state.hasData = valid
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

        const { labels, datasets } = this._getChartDataFromProps(this.props)

        const chartDatasets = datasets.map(ds => ({
            label: ds.label || "",
            data: ds.data,
            backgroundColor: ds.backgroundColor,
            borderColor: ds.borderColor || ds.backgroundColor,
            borderWidth: 1,
        }))

        this.chart = new Chart(ctx, {
            type: "bar",
            data: { labels, datasets: chartDatasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: "y",                     // ← barras horizontales
                plugins: {
                    legend: {
                        position: this.state.legendPosition,
                        align: "center",
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
                            label: (context) => {
                                const label = context.dataset.label || ""
                                const val = context.raw
                                const total = context.chart.data.datasets.reduce((sum, ds) => sum + (ds.data[context.dataIndex] || 0), 0)
                                const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0
                                return ` ${label}: ${val} (${pct}%)`
                            },
                        },
                        backgroundColor: "rgba(0,0,0,0.7)",
                        titleColor: "#ffcc00",
                        bodyColor: "#fff",
                    },
                },
                scales: {
                    x: { stacked: true, beginAtZero: true },
                    y: { stacked: true },
                },
            },
        })
    }
}

StackedBarHChart.template = "apn_charts.StackedBarHChartTemplate"
registry.category("components").add("StackedBarHChart", StackedBarHChart)
registry.category("fields").add("stacked_bar_h_chart", { component: StackedBarHChart })

export { StackedBarHChart }

StackedBarVChart.template = "apn_charts.StackedBarVChartTemplate"
registry.category("components").add("StackedBarVChart", StackedBarVChart)
registry.category("fields").add("stacked_bar_v_chart", { component: StackedBarVChart })

export { StackedBarVChart }


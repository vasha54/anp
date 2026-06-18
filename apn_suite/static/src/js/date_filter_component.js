/** @odoo-module **/
import { Component, useState } from "@odoo/owl";

export class DateFilterComponent extends Component {
    static template = "apn_suite.DateFilterTemplate";
    static props = {
        onFilter: { type: Function, optional: true }
    };

    setup() {
        this.state = useState({
            selectedPeriod: 'today',  // Cambiado a 'today'
            customStartDate: '',
            customEndDate: '',
            showCustomDates: false,
        });

        this.onFilterClick = this.onFilterClick.bind(this);
    }

    get periods() {
        return [
            { id: 'today', label: 'Today' },
            { id: 'yesterday', label: 'Yesterday' },
            { id: 'this_week', label: 'This Week' },
            { id: 'last_week', label: 'Last Week' },
            { id: 'this_month', label: 'This Month' },
            { id: 'last_month', label: 'Last Month' },
            { id: 'this_quarter', label: 'This Quarter' },
            { id: 'last_quarter', label: 'Last Quarter' },
            { id: 'this_year', label: 'This Year' },
            { id: 'last_year', label: 'Last Year' },
            { id: 'custom', label: 'Custom' },
        ];
    }

    onPeriodChange(ev) {
        const value = ev.target.value;
        this.state.selectedPeriod = value;
        this.state.showCustomDates = value === 'custom';
    }

    onFilterClick() {
        const filterData = this.getFilterData();
        if (this.props.onFilter) {
            this.props.onFilter(filterData);
        } else {
            console.log('Filter data:', filterData);
        }
    }

    getFilterData() {
        const today = new Date();
        let startDate, endDate;

        switch (this.state.selectedPeriod) {
            case 'today':
                startDate = new Date(today.getFullYear(), today.getMonth(), today.getDate());
                endDate = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 23, 59, 59);
                break;
            case 'yesterday':
                const yesterday = new Date(today);
                yesterday.setDate(yesterday.getDate() - 1);
                startDate = new Date(yesterday.getFullYear(), yesterday.getMonth(), yesterday.getDate());
                endDate = new Date(yesterday.getFullYear(), yesterday.getMonth(), yesterday.getDate(), 23, 59, 59);
                break;
            case 'this_week':
                const startOfWeek = new Date(today);
                startOfWeek.setDate(today.getDate() - today.getDay() + 1); // Lunes
                startDate = new Date(startOfWeek.getFullYear(), startOfWeek.getMonth(), startOfWeek.getDate());
                const endOfWeek = new Date(today);
                endOfWeek.setDate(today.getDate() - today.getDay() + 7); // Domingo
                endDate = new Date(endOfWeek.getFullYear(), endOfWeek.getMonth(), endOfWeek.getDate(), 23, 59, 59);
                break;
            case 'last_week':
                const lastWeekStart = new Date(today);
                lastWeekStart.setDate(today.getDate() - today.getDay() - 6); // Lunes pasado
                startDate = new Date(lastWeekStart.getFullYear(), lastWeekStart.getMonth(), lastWeekStart.getDate());
                const lastWeekEnd = new Date(today);
                lastWeekEnd.setDate(today.getDate() - today.getDay()); // Domingo pasado
                endDate = new Date(lastWeekEnd.getFullYear(), lastWeekEnd.getMonth(), lastWeekEnd.getDate(), 23, 59, 59);
                break;
            case 'this_month':
                startDate = new Date(today.getFullYear(), today.getMonth(), 1);
                endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0, 23, 59, 59);
                break;
            case 'last_month':
                startDate = new Date(today.getFullYear(), today.getMonth() - 1, 1);
                endDate = new Date(today.getFullYear(), today.getMonth(), 0, 23, 59, 59);
                break;
            case 'this_quarter':
                const currentQuarter = Math.floor(today.getMonth() / 3);
                startDate = new Date(today.getFullYear(), currentQuarter * 3, 1);
                endDate = new Date(today.getFullYear(), (currentQuarter + 1) * 3, 0, 23, 59, 59);
                break;
            case 'last_quarter':
                const lastQuarter = Math.floor(today.getMonth() / 3) - 1;
                const year = lastQuarter < 0 ? today.getFullYear() - 1 : today.getFullYear();
                const quarter = lastQuarter < 0 ? 3 : lastQuarter;
                startDate = new Date(year, quarter * 3, 1);
                endDate = new Date(year, (quarter + 1) * 3, 0, 23, 59, 59);
                break;
            case 'this_year':
                startDate = new Date(today.getFullYear(), 0, 1);
                endDate = new Date(today.getFullYear(), 11, 31, 23, 59, 59);
                break;
            case 'last_year':
                startDate = new Date(today.getFullYear() - 1, 0, 1);
                endDate = new Date(today.getFullYear() - 1, 11, 31, 23, 59, 59);
                break;
            case 'custom':
                startDate = this.state.customStartDate ? new Date(this.state.customStartDate) : null;
                endDate = this.state.customEndDate ? new Date(this.state.customEndDate + 'T23:59:59') : null;
                break;
        }

        return {
            period: this.state.selectedPeriod,
            startDate: startDate,
            endDate: endDate,
        };
    }
}
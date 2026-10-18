/**
 * CartCompass-BI - Dashboard Application Logic
 * Integrates Chart.js visualizations, currency formatting, filter management,
 * and RESTful API communications with the Flask backend.
 */

// Application State
const state = {
    currency: 'INR',
    currencySymbol: '₹',
    usdExchangeRate: 0.012, // 1 INR ~ 0.012 USD
    statusMode: 'delivered',
    startDate: '',
    endDate: '',
    cachedData: {
        kpis: null,
        monthly: null,
        categories: null,
        regions: null,
        growth: null,
        statusDist: null
    },
    charts: {
        monthly: null,
        category: null,
        regional: null,
        period: null,
        status: null
    },
    activeTab: 'cat-tab'
};

// Modern Chart Palette
const CHART_COLORS = {
    primary: '#2563eb',
    primaryAlpha: 'rgba(37, 99, 235, 0.15)',
    emerald: '#10b981',
    emeraldAlpha: 'rgba(16, 185, 129, 0.20)',
    indigo: '#6366f1',
    amber: '#f59e0b',
    rose: '#f43f5e',
    cyan: '#06b6d4',
    palette: ['#2563eb', '#10b981', '#f59e0b', '#6366f1', '#f43f5e', '#06b6d4'],
    slateGrid: 'rgba(226, 232, 240, 0.8)',
    textMuted: '#64748b'
};

// Document Ready Initialization
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    checkHealth();
    loadDashboardData();
});

// Event Listeners Setup
function initEventListeners() {
    // Currency Switcher
    const currInrBtn = document.getElementById('curr-inr');
    const currUsdBtn = document.getElementById('curr-usd');

    if (currInrBtn && currUsdBtn) {
        currInrBtn.addEventListener('click', () => setCurrency('INR'));
        currUsdBtn.addEventListener('click', () => setCurrency('USD'));
    }

    // Filter Buttons
    document.getElementById('btn-apply-filters')?.addEventListener('click', applyFilters);
    document.getElementById('btn-reset-filters')?.addEventListener('click', resetFilters);
    document.getElementById('btn-refresh')?.addEventListener('click', () => loadDashboardData(true));

    // Preset Timeframe Buttons
    const presetButtons = document.querySelectorAll('.preset-btn');
    presetButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            presetButtons.forEach(b => b.classList.remove('active'));
            e.currentTarget.classList.add('active');
            handleTimeframePreset(e.currentTarget.dataset.preset);
        });
    });

    // Summary Table Tabs
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            tabButtons.forEach(b => b.classList.remove('active'));
            e.currentTarget.classList.add('active');
            state.activeTab = e.currentTarget.dataset.tab;
            renderSummaryTable();
        });
    });

    // Mobile Sidebar Toggle
    const mobileToggle = document.getElementById('mobile-sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    if (mobileToggle && sidebar) {
        mobileToggle.addEventListener('click', () => {
            sidebar.classList.toggle('mobile-open');
        });
    }

    // Close error banner
    document.getElementById('close-error-banner')?.addEventListener('click', () => {
        const errorBanner = document.getElementById('error-banner');
        if (errorBanner) errorBanner.style.display = 'none';
    });

    // Static Charts view button
    document.getElementById('btn-regenerate-static-charts')?.addEventListener('click', () => {
        document.getElementById('reports-section')?.scrollIntoView({ behavior: 'smooth' });
    });
}

// Currency Conversion & Formatting
function setCurrency(curr) {
    state.currency = curr;
    state.currencySymbol = curr === 'INR' ? '₹' : '$';

    document.getElementById('curr-inr')?.classList.toggle('active', curr === 'INR');
    document.getElementById('curr-usd')?.classList.toggle('active', curr === 'USD');

    // Re-render UI with new currency formatting
    if (state.cachedData.kpis) {
        updateKpiDisplay(state.cachedData.kpis);
    }
    if (state.cachedData.monthly) {
        renderMonthlyRevenueChart(state.cachedData.monthly);
    }
    if (state.cachedData.categories) {
        renderCategoryRevenueChart(state.cachedData.categories);
    }
    if (state.cachedData.regions) {
        renderRegionalRevenueChart(state.cachedData.regions);
    }
    if (state.cachedData.growth) {
        renderPeriodComparisonChart(state.cachedData.growth);
    }
    renderSummaryTable();
}

function formatCurrency(val) {
    if (val === null || val === undefined || isNaN(val)) return '--';
    let numericVal = Number(val);
    if (state.currency === 'USD') {
        numericVal = numericVal * state.usdExchangeRate;
        return '$' + numericVal.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
    // Indian Rupee formatting
    return '₹' + numericVal.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatNumber(val) {
    if (val === null || val === undefined || isNaN(val)) return '--';
    return Number(val).toLocaleString();
}

function formatPercent(val) {
    if (val === null || val === undefined || isNaN(val)) return 'N/A';
    const num = Number(val);
    const sign = num > 0 ? '+' : '';
    return `${sign}${num.toFixed(1)}%`;
}

// Preset Timeframes
function handleTimeframePreset(preset) {
    const startDateInput = document.getElementById('filter-start-date');
    const endDateInput = document.getElementById('filter-end-date');

    if (preset === 'all') {
        startDateInput.value = '';
        endDateInput.value = '';
    } else if (preset === '12m') {
        startDateInput.value = '2025-03-01';
        endDateInput.value = '2026-02-28';
    } else if (preset === '6m') {
        startDateInput.value = '2025-09-01';
        endDateInput.value = '2026-02-28';
    } else if (preset === 'q4') {
        startDateInput.value = '2025-10-01';
        endDateInput.value = '2025-12-31';
    }

    applyFilters();
}

function applyFilters() {
    state.startDate = document.getElementById('filter-start-date')?.value || '';
    state.endDate = document.getElementById('filter-end-date')?.value || '';
    state.statusMode = document.getElementById('filter-status-mode')?.value || 'delivered';

    // Update active policy badge
    const badge = document.getElementById('active-policy-badge');
    if (badge) {
        if (state.statusMode === 'delivered') {
            badge.textContent = 'Policy: Realized Sales (Delivered)';
        } else if (state.statusMode === 'all_active') {
            badge.textContent = 'Policy: Active Orders (Delivered + Shipped + Pending)';
        } else {
            badge.textContent = 'Policy: All Orders (Including Cancelled)';
        }
    }

    loadDashboardData();
}

function resetFilters() {
    document.getElementById('filter-start-date').value = '';
    document.getElementById('filter-end-date').value = '';
    document.getElementById('filter-status-mode').value = 'delivered';

    // Reset preset active state
    document.querySelectorAll('.preset-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.preset === 'all');
    });

    state.startDate = '';
    state.endDate = '';
    state.statusMode = 'delivered';

    const badge = document.getElementById('active-policy-badge');
    if (badge) badge.textContent = 'Policy: Realized Sales (Delivered)';

    loadDashboardData();
}

// Health Check API
async function checkHealth() {
    try {
        const res = await fetch('/api/health');
        if (!res.ok) throw new Error('Health check response not OK');
        const data = await res.json();
        
        const statusIndicator = document.getElementById('system-status-indicator');
        const statusText = document.getElementById('system-status-text');
        const dbMeta = document.getElementById('db-meta-info');

        if (statusIndicator && statusText) {
            statusIndicator.className = 'status-indicator online';
            statusText.textContent = 'SQLite Connected';
        }
        if (dbMeta && data.database?.records) {
            const r = data.database.records;
            dbMeta.textContent = `${r.orders} Orders | ${r.products} Products | ${r.order_items} Items`;
        }
    } catch (err) {
        const statusIndicator = document.getElementById('system-status-indicator');
        const statusText = document.getElementById('system-status-text');
        if (statusIndicator && statusText) {
            statusIndicator.className = 'status-indicator';
            statusIndicator.style.backgroundColor = '#f43f5e';
            statusText.textContent = 'Backend Offline';
        }
    }
}

// Show/Hide Loading and Error Overlays
function setLoading(isLoading) {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.style.display = isLoading ? 'flex' : 'none';
}

function showError(msg) {
    const errorBanner = document.getElementById('error-banner');
    const errorText = document.getElementById('error-message-text');
    if (errorBanner && errorText) {
        errorText.textContent = msg || 'Failed to load dashboard data. Check backend console.';
        errorBanner.style.display = 'flex';
    }
}

function hideError() {
    const errorBanner = document.getElementById('error-banner');
    if (errorBanner) errorBanner.style.display = 'none';
}

// Main Data Fetcher
async function loadDashboardData(forceRefresh = false) {
    setLoading(true);
    hideError();

    const queryParams = new URLSearchParams();
    if (state.startDate) queryParams.append('start_date', state.startDate);
    if (state.endDate) queryParams.append('end_date', state.endDate);
    if (state.statusMode) queryParams.append('status_mode', state.statusMode);

    const qs = queryParams.toString() ? `?${queryParams.toString()}` : '';

    try {
        // Fetch all 6 analytical endpoints in parallel
        const [kpisRes, monthlyRes, catRes, regRes, growthRes, statusRes] = await Promise.all([
            fetch(`/api/kpis${qs}`),
            fetch(`/api/revenue/monthly${qs}`),
            fetch(`/api/categories${qs}`),
            fetch(`/api/regions${qs}`),
            fetch(`/api/revenue/growth${qs}`),
            fetch(`/api/status-distribution${qs}`)
        ]);

        if (!kpisRes.ok || !monthlyRes.ok || !catRes.ok || !regRes.ok || !growthRes.ok || !statusRes.ok) {
            const errJson = await kpisRes.json().catch(() => ({ message: 'API error' }));
            throw new Error(errJson.message || 'One or more API endpoints returned an error.');
        }

        const kpisData = (await kpisRes.json()).data;
        const monthlyData = (await monthlyRes.json()).data;
        const catData = (await catRes.json()).data;
        const regData = (await regRes.json()).data;
        const growthData = (await growthRes.json()).data;
        const statusData = (await statusRes.json()).data;

        // Cache responses
        state.cachedData.kpis = kpisData;
        state.cachedData.monthly = monthlyData;
        state.cachedData.categories = catData;
        state.cachedData.regions = regData;
        state.cachedData.growth = growthData;
        state.cachedData.statusDist = statusData;

        // Render UI Components
        updateKpiDisplay(kpisData);
        renderMonthlyRevenueChart(monthlyData);
        renderCategoryRevenueChart(catData);
        renderRegionalRevenueChart(regData);
        renderPeriodComparisonChart(growthData);
        renderOrderStatusChart(statusData);
        renderSummaryTable();

    } catch (err) {
        console.error('Error loading dashboard data:', err);
        showError(err.message);
    } finally {
        setLoading(false);
    }
}

// 1. Update KPI Cards
function updateKpiDisplay(kpis) {
    document.getElementById('kpi-gross-sales').textContent = formatCurrency(kpis.gross_sales);
    document.getElementById('kpi-net-sales').textContent = formatCurrency(kpis.net_sales);
    document.getElementById('kpi-total-orders').textContent = formatNumber(kpis.total_orders);
    document.getElementById('kpi-aov').textContent = formatCurrency(kpis.average_order_value);
    document.getElementById('kpi-discount-amount').textContent = formatCurrency(kpis.discount_amount);
    document.getElementById('kpi-return-amount').textContent = formatCurrency(kpis.return_amount);

    // Revenue Growth Badge
    const growthVal = kpis.growth?.revenue_growth_pct;
    const growthElem = document.getElementById('kpi-revenue-growth');
    const badgeElem = document.getElementById('growth-badge');

    if (growthElem) {
        if (growthVal !== null && growthVal !== undefined) {
            growthElem.textContent = formatPercent(growthVal);
            if (badgeElem) {
                badgeElem.className = 'trend-badge ' + (growthVal >= 0 ? 'positive' : 'negative');
                badgeElem.textContent = growthVal >= 0 ? '▲ Growth vs Baseline' : '▼ Decline vs Baseline';
            }
        } else {
            growthElem.textContent = 'N/A';
            if (badgeElem) {
                badgeElem.className = 'trend-badge';
                badgeElem.textContent = 'Baseline Zero / N/A';
            }
        }
    }
}

// 2. Chart 1: Monthly Net Revenue Trend (Line Chart)
function renderMonthlyRevenueChart(data) {
    const ctx = document.getElementById('monthlyRevenueChart')?.getContext('2d');
    if (!ctx) return;

    if (state.charts.monthly) {
        state.charts.monthly.destroy();
    }

    const emptyState = document.getElementById('monthly-empty-state');
    if (!data || data.length === 0) {
        if (emptyState) emptyState.style.display = 'flex';
        return;
    }
    if (emptyState) emptyState.style.display = 'none';

    const labels = data.map(d => d.year_month);
    const netSales = data.map(d => state.currency === 'USD' ? d.net_sales * state.usdExchangeRate : d.net_sales);
    const grossSales = data.map(d => state.currency === 'USD' ? d.gross_sales * state.usdExchangeRate : d.gross_sales);

    // Gradient fill
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(37, 99, 235, 0.25)');
    gradient.addColorStop(1, 'rgba(37, 99, 235, 0.00)');

    state.charts.monthly = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: `Net Revenue (${state.currencySymbol})`,
                    data: netSales,
                    borderColor: CHART_COLORS.primary,
                    backgroundColor: gradient,
                    borderWidth: 2.8,
                    pointBackgroundColor: CHART_COLORS.primary,
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 4.5,
                    pointHoverRadius: 7,
                    tension: 0.35,
                    fill: true
                },
                {
                    label: `Gross Sales (${state.currencySymbol})`,
                    data: grossSales,
                    borderColor: '#94a3b8',
                    borderWidth: 1.8,
                    borderDash: [5, 5],
                    pointRadius: 0,
                    tension: 0.35,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        boxWidth: 12,
                        font: { family: 'Inter', size: 12, weight: '500' }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${formatCurrency(state.currency === 'USD' ? context.raw / state.usdExchangeRate : context.raw)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { family: 'Inter', size: 11 }, color: CHART_COLORS.textMuted }
                },
                y: {
                    grid: { color: CHART_COLORS.slateGrid },
                    ticks: {
                        font: { family: 'Inter', size: 11 },
                        color: CHART_COLORS.textMuted,
                        callback: function(val) {
                            if (val >= 1000000) return `${state.currencySymbol}${(val / 1000000).toFixed(1)}M`;
                            if (val >= 1000) return `${state.currencySymbol}${(val / 1000).toFixed(0)}k`;
                            return `${state.currencySymbol}${val}`;
                        }
                    }
                }
            }
        }
    });
}

// 3. Chart 2: Revenue by Product Category (Horizontal Bar Chart)
function renderCategoryRevenueChart(data) {
    const ctx = document.getElementById('categoryRevenueChart')?.getContext('2d');
    if (!ctx) return;

    if (state.charts.category) {
        state.charts.category.destroy();
    }

    if (!data || data.length === 0) return;

    const labels = data.map(d => d.category);
    const netSales = data.map(d => state.currency === 'USD' ? d.net_sales * state.usdExchangeRate : d.net_sales);

    state.charts.category = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: `Category Revenue (${state.currencySymbol})`,
                data: netSales,
                backgroundColor: CHART_COLORS.palette.slice(0, data.length),
                borderRadius: 6,
                maxBarThickness: 32
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const raw = context.raw;
                            const origVal = state.currency === 'USD' ? raw / state.usdExchangeRate : raw;
                            const item = data[context.dataIndex];
                            return `Revenue: ${formatCurrency(origVal)} (${item.revenue_share_pct}%)`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: CHART_COLORS.slateGrid },
                    ticks: {
                        font: { family: 'Inter', size: 11 },
                        color: CHART_COLORS.textMuted,
                        callback: val => `${state.currencySymbol}${(val / 1000).toFixed(0)}k`
                    }
                },
                y: {
                    grid: { display: false },
                    ticks: { font: { family: 'Inter', size: 11 }, color: CHART_COLORS.textMuted }
                }
            }
        }
    });
}

// 4. Chart 3: Regional Sales Performance (Vertical Bar Chart)
function renderRegionalRevenueChart(data) {
    const ctx = document.getElementById('regionalRevenueChart')?.getContext('2d');
    if (!ctx) return;

    if (state.charts.regional) {
        state.charts.regional.destroy();
    }

    if (!data || data.length === 0) return;

    const labels = data.map(d => d.region);
    const netSales = data.map(d => state.currency === 'USD' ? d.net_sales * state.usdExchangeRate : d.net_sales);

    state.charts.regional = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: `Regional Sales (${state.currencySymbol})`,
                data: netSales,
                backgroundColor: CHART_COLORS.primary,
                hoverBackgroundColor: '#1d4ed8',
                borderRadius: 6,
                maxBarThickness: 38
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const raw = context.raw;
                            const origVal = state.currency === 'USD' ? raw / state.usdExchangeRate : raw;
                            const item = data[context.dataIndex];
                            return [
                                `Net Revenue: ${formatCurrency(origVal)}`,
                                `Total Orders: ${formatNumber(item.total_orders)}`,
                                `AOV: ${formatCurrency(item.average_order_value)}`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { family: 'Inter', size: 11 }, color: CHART_COLORS.textMuted }
                },
                y: {
                    grid: { color: CHART_COLORS.slateGrid },
                    ticks: {
                        font: { family: 'Inter', size: 11 },
                        color: CHART_COLORS.textMuted,
                        callback: val => `${state.currencySymbol}${(val / 1000).toFixed(0)}k`
                    }
                }
            }
        }
    });
}

// 5. Chart 4: Period-over-Period Performance (Grouped Bar Chart)
function renderPeriodComparisonChart(growthData) {
    const ctx = document.getElementById('periodComparisonChart')?.getContext('2d');
    if (!ctx) return;

    if (state.charts.period) {
        state.charts.period.destroy();
    }

    if (!growthData) return;

    const currNet = growthData.current_period?.net_sales || 0;
    const prevNet = growthData.previous_metrics?.net_sales || 0;
    const currOrders = growthData.current_period?.total_orders || 0;
    const prevOrders = growthData.previous_metrics?.total_orders || 0;

    const currVal = state.currency === 'USD' ? currNet * state.usdExchangeRate : currNet;
    const prevVal = state.currency === 'USD' ? prevNet * state.usdExchangeRate : prevNet;

    state.charts.period = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Net Revenue', 'Order Volume'],
            datasets: [
                {
                    label: 'Previous Period',
                    data: [prevVal, prevOrders],
                    backgroundColor: '#cbd5e1',
                    borderRadius: 6,
                    maxBarThickness: 42
                },
                {
                    label: 'Current Period',
                    data: [currVal, currOrders],
                    backgroundColor: CHART_COLORS.emerald,
                    borderRadius: 6,
                    maxBarThickness: 42
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: { font: { family: 'Inter', size: 11, weight: '500' }, boxWidth: 12 }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            if (context.dataIndex === 0) {
                                const origVal = state.currency === 'USD' ? context.raw / state.usdExchangeRate : context.raw;
                                return `${context.dataset.label}: ${formatCurrency(origVal)}`;
                            }
                            return `${context.dataset.label}: ${formatNumber(context.raw)} Orders`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { family: 'Inter', size: 11 }, color: CHART_COLORS.textMuted }
                },
                y: {
                    grid: { color: CHART_COLORS.slateGrid },
                    ticks: {
                        font: { family: 'Inter', size: 11 },
                        color: CHART_COLORS.textMuted,
                        callback: function(val) {
                            if (val >= 1000) return `${(val / 1000).toFixed(0)}k`;
                            return val;
                        }
                    }
                }
            }
        }
    });
}

// 6. Chart 5: Order Status Distribution (Doughnut Chart)
function renderOrderStatusChart(statusData) {
    const ctx = document.getElementById('orderStatusChart')?.getContext('2d');
    if (!ctx) return;

    if (state.charts.status) {
        state.charts.status.destroy();
    }

    if (!statusData || !statusData.distribution) return;

    const labels = statusData.distribution.map(s => s.status.charAt(0).toUpperCase() + s.status.slice(1));
    const counts = statusData.distribution.map(s => s.order_count);
    const colors = [CHART_COLORS.emerald, CHART_COLORS.primary, CHART_COLORS.amber, CHART_COLORS.rose];

    state.charts.status = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: counts,
                backgroundColor: colors.slice(0, labels.length),
                borderWidth: 2,
                borderColor: '#ffffff',
                hoverOffset: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '68%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        padding: 12,
                        font: { family: 'Inter', size: 11, weight: '500' }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const count = context.raw;
                            const total = statusData.total_orders;
                            const pct = total > 0 ? ((count / total) * 100).toFixed(1) : 0;
                            return ` ${context.label}: ${formatNumber(count)} (${pct}%)`;
                        }
                    }
                }
            }
        }
    });
}

// 7. Render Summary Data Table
function renderSummaryTable() {
    const tbody = document.getElementById('table-body');
    const theadRow = document.getElementById('table-head-row');
    if (!tbody || !theadRow) return;

    tbody.innerHTML = '';

    if (state.activeTab === 'cat-tab') {
        const data = state.cachedData.categories;
        if (!data || data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="loading-cell">No category data available.</td></tr>';
            return;
        }

        theadRow.innerHTML = `
            <th>Product Category</th>
            <th>Net Sales</th>
            <th>Discounts</th>
            <th>Returns</th>
            <th>Items Sold</th>
            <th>Revenue Share</th>
        `;

        data.forEach(item => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${item.category}</strong></td>
                <td>${formatCurrency(item.net_sales)}</td>
                <td>${formatCurrency(item.discount_amount)}</td>
                <td>${formatCurrency(item.return_amount)}</td>
                <td>${formatNumber(item.total_items)}</td>
                <td><span class="trend-badge">${item.revenue_share_pct}%</span></td>
            `;
            tbody.appendChild(tr);
        });

    } else {
        const data = state.cachedData.regions;
        if (!data || data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="loading-cell">No regional data available.</td></tr>';
            return;
        }

        theadRow.innerHTML = `
            <th>Geographical Region</th>
            <th>Net Sales</th>
            <th>Discounts</th>
            <th>Returns</th>
            <th>Orders (AOV)</th>
            <th>Revenue Share</th>
        `;

        data.forEach(item => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${item.region}</strong></td>
                <td>${formatCurrency(item.net_sales)}</td>
                <td>${formatCurrency(item.discount_amount)}</td>
                <td>${formatCurrency(item.return_amount)}</td>
                <td>${formatNumber(item.total_orders)} (${formatCurrency(item.average_order_value)})</td>
                <td><span class="trend-badge">${item.revenue_share_pct}%</span></td>
            `;
            tbody.appendChild(tr);
        });
    }
}

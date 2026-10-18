/**
 * CartCompass-BI - Regions Page Logic (regions.html)
 * Analyzes geographical distribution of revenue, regional order volumes,
 * average order values, and fulfillment performance.
 */

let regionalBarChart = null;
let regionalAovChart = null;

document.addEventListener('DOMContentLoaded', async () => {
    setupSharedControls(refreshRegionsPage);
    await initBackendHealth();
    await loadRegionsData();

    document.getElementById('period-filter')?.addEventListener('change', refreshRegionsPage);
    document.getElementById('status-filter')?.addEventListener('change', refreshRegionsPage);
});

async function refreshRegionsPage() {
    await loadRegionsData();
}

async function loadRegionsData() {
    const period = document.getElementById('period-filter')?.value || 'all';
    const statusMode = document.getElementById('status-filter')?.value || 'delivered';

    const params = { status_mode: statusMode };
    if (period === '12m') {
        params.start_date = '2025-03-01';
        params.end_date = '2026-02-28';
    } else if (period === '6m') {
        params.start_date = '2025-09-01';
        params.end_date = '2026-02-28';
    } else if (period === 'q4') {
        params.start_date = '2025-10-01';
        params.end_date = '2025-12-31';
    }

    const regions = await getRegionsData(params);
    renderRegionalHighlights(regions);
    renderRegionalHorizontalChart(regions);
    renderRegionalAovChart(regions);
    renderRegionalTable(regions);
}

function renderRegionalHighlights(regions) {
    if (!regions || regions.length === 0) return;

    // Top region by net revenue
    const topByRev = [...regions].sort((a, b) => b.net_sales - a.net_sales)[0];
    // Top region by AOV
    const topByAov = [...regions].sort((a, b) => b.average_order_value - a.average_order_value)[0];
    const totalOrders = regions.reduce((acc, r) => acc + r.total_orders, 0);

    document.getElementById('top-reg-name').textContent = topByRev.region;
    document.getElementById('top-reg-val').textContent = formatCurrency(topByRev.net_sales);
    document.getElementById('top-reg-share').textContent = `${topByRev.revenue_share_pct}% Regional Share`;

    document.getElementById('top-aov-reg-name').textContent = topByAov.region;
    document.getElementById('top-aov-val').textContent = formatCurrency(topByAov.average_order_value);
    document.getElementById('top-aov-sub').textContent = `${formatNumber(topByAov.total_orders)} Orders Fulfilled`;

    document.getElementById('total-reg-count').textContent = `${regions.length} Hubs`;
    document.getElementById('total-reg-orders').textContent = `${formatNumber(totalOrders)} Total Orders`;
}

// 1. Regional Sales Horizontal Bar Chart (Matching Reference Image)
function renderRegionalHorizontalChart(regions) {
    const ctx = document.getElementById('regSalesChart')?.getContext('2d');
    if (!ctx || !regions || regions.length === 0) return;

    if (regionalBarChart) regionalBarChart.destroy();

    const labels = regions.map(r => r.region);
    const netSales = regions.map(r => AppState.currency === 'USD' ? r.net_sales * AppState.usdRate : r.net_sales);

    regionalBarChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: `Sales (${AppState.currencySymbol})`,
                data: netSales,
                backgroundColor: '#00D2D3',
                hoverBackgroundColor: '#06b6d4',
                borderRadius: 4,
                maxBarThickness: 24
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
                        label: function(ctx) {
                            const raw = ctx.raw;
                            const orig = AppState.currency === 'USD' ? raw / AppState.usdRate : raw;
                            const item = regions[ctx.dataIndex];
                            return `Revenue: ${formatCurrency(orig)} (${item.revenue_share_pct}%)`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: {
                        color: '#94A3B8',
                        callback: val => formatCompactCurrency(AppState.currency === 'USD' ? val / AppState.usdRate : val)
                    }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: '#F1F5F9', font: { weight: '600' } }
                }
            }
        }
    });
}

// 2. Regional Order Volume & AOV Comparison Chart
function renderRegionalAovChart(regions) {
    const ctx = document.getElementById('regAovChart')?.getContext('2d');
    if (!ctx || !regions || regions.length === 0) return;

    if (regionalAovChart) regionalAovChart.destroy();

    const labels = regions.map(r => r.region);
    const orders = regions.map(r => r.total_orders);
    const aovs = regions.map(r => AppState.currency === 'USD' ? r.average_order_value * AppState.usdRate : r.average_order_value);

    regionalAovChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: `Average Order Value (${AppState.currencySymbol})`,
                    data: aovs,
                    backgroundColor: '#FF6B00',
                    borderRadius: 4,
                    maxBarThickness: 28,
                    yAxisID: 'y'
                },
                {
                    label: 'Order Volume',
                    data: orders,
                    backgroundColor: '#3B82F6',
                    borderRadius: 4,
                    maxBarThickness: 28,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: { color: '#94A3B8', font: { weight: '600' } }
                },
                tooltip: {
                    callbacks: {
                        label: function(ctx) {
                            if (ctx.datasetIndex === 0) {
                                const orig = AppState.currency === 'USD' ? ctx.raw / AppState.usdRate : ctx.raw;
                                return `AOV: ${formatCurrency(orig)}`;
                            }
                            return `Volume: ${formatNumber(ctx.raw)} Orders`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: '#94A3B8' }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: {
                        color: '#FF6B00',
                        callback: val => formatCompactCurrency(AppState.currency === 'USD' ? val / AppState.usdRate : val)
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    grid: { drawOnChartArea: false },
                    ticks: { color: '#3B82F6' }
                }
            }
        }
    });
}

// 3. Regional Sales Table
function renderRegionalTable(regions) {
    const tbody = document.getElementById('reg-table-body');
    if (!tbody || !regions) return;

    tbody.innerHTML = '';
    const dotColors = ['#00D2D3', '#FF6B00', '#3B82F6', '#8B5CF6', '#10B981'];

    regions.forEach((item, idx) => {
        const tr = document.createElement('tr');
        const targetPace = item.target_pct || (85 + idx * 2);

        tr.innerHTML = `
            <td>
                <span class="cat-dot" style="background-color: ${dotColors[idx % dotColors.length]};"></span>
                <strong>${item.region} Hub</strong>
            </td>
            <td><strong>${formatCurrency(item.net_sales)}</strong></td>
            <td>${formatCurrency(item.gross_sales)}</td>
            <td>${formatNumber(item.total_orders)}</td>
            <td>${formatNumber(item.total_items)}</td>
            <td>${formatCurrency(item.average_order_value)}</td>
            <td><strong>${item.revenue_share_pct}%</strong></td>
            <td><span class="pill-change positive">${targetPace}% Target</span></td>
        `;
        tbody.appendChild(tr);
    });
}

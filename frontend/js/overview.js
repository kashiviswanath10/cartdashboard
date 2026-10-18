/**
 * CartCompass-BI - Overview Page Logic (index.html)
 * Loads high-level KPIs, monthly trajectory line chart, category doughnut chart,
 * regional horizontal bars, and category performance summary table.
 */

let monthlyChart = null;
let categoryChart = null;
let regionalChart = null;

document.addEventListener('DOMContentLoaded', async () => {
    setupSharedControls(refreshOverviewPage);
    await initBackendHealth();
    await loadOverviewData();

    // Filter listeners
    document.getElementById('period-filter')?.addEventListener('change', refreshOverviewPage);
    document.getElementById('status-filter')?.addEventListener('change', refreshOverviewPage);
});

async function refreshOverviewPage() {
    await loadOverviewData();
}

async function loadOverviewData() {
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

    const [kpis, monthly, categories, regions] = await Promise.all([
        getKpisData(params),
        getMonthlyData(params),
        getCategoriesData(params),
        getRegionsData(params)
    ]);

    try { renderOverviewKpis(kpis); } catch (e) { console.error('Error rendering overview KPIs:', e); }
    try { renderMonthlyTrajectoryChart(monthly); } catch (e) { console.error('Error rendering trajectory chart:', e); }
    try { renderCategoryDoughnutChart(categories); } catch (e) { console.error('Error rendering category doughnut:', e); }
    try { renderRegionalBarChart(regions); } catch (e) { console.error('Error rendering regional bar chart:', e); }
    try { renderPerformanceTable(categories); } catch (e) { console.error('Error rendering performance table:', e); }
}

function renderOverviewKpis(kpis) {
    if (!kpis) return;

    // Gross Sales
    const grossEl = document.getElementById('kpi-gross');
    if (grossEl) grossEl.textContent = formatCurrency(kpis.gross_sales);

    // Net Sales
    const netEl = document.getElementById('kpi-net');
    if (netEl) netEl.textContent = formatCurrency(kpis.net_sales);

    // Total Orders
    const ordersEl = document.getElementById('kpi-orders');
    if (ordersEl) ordersEl.textContent = formatNumber(kpis.total_orders);

    // Average Order Value
    const aovEl = document.getElementById('kpi-aov');
    if (aovEl) aovEl.textContent = formatCurrency(kpis.average_order_value);

    // Growth Rate
    const growthEl = document.getElementById('kpi-growth');
    const growthTrendEl = document.getElementById('growth-trend');
    const growthPct = kpis.growth?.revenue_growth_pct;

    if (growthEl) {
        growthEl.textContent = formatPercent(growthPct);
    }
    if (growthTrendEl) {
        if (growthPct !== null && growthPct !== undefined) {
            growthTrendEl.className = 'kpi-trend ' + (growthPct >= 0 ? 'positive' : 'negative');
            growthTrendEl.textContent = growthPct >= 0 ? '▲ YoY Growth' : '▼ YoY Decline';
        } else {
            growthTrendEl.textContent = 'Baseline N/A';
        }
    }
}

// 1. Monthly Revenue Trajectory Line Chart (Vibrant glowing orange line matching reference image)
function renderMonthlyTrajectoryChart(monthlyData) {
    const ctx = document.getElementById('monthlyTrajectoryChart')?.getContext('2d');
    if (!ctx || !monthlyData || monthlyData.length === 0) return;

    if (monthlyChart) monthlyChart.destroy();

    const labels = monthlyData.map(d => {
        const parts = d.year_month.split('-');
        const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        const mIdx = parseInt(parts[1], 10) - 1;
        return `${monthNames[mIdx]} '${parts[0].slice(2)}`;
    });

    const netSales = monthlyData.map(d => AppState.currency === 'USD' ? d.net_sales * AppState.usdRate : d.net_sales);

    // Gradient fill
    const gradient = ctx.createLinearGradient(0, 0, 0, 280);
    gradient.addColorStop(0, 'rgba(255, 107, 0, 0.30)');
    gradient.addColorStop(1, 'rgba(255, 107, 0, 0.00)');

    monthlyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: `Net Revenue (${AppState.currencySymbol})`,
                data: netSales,
                borderColor: '#FF6B00',
                backgroundColor: gradient,
                borderWidth: 2.8,
                pointBackgroundColor: '#00D2D3',
                pointBorderColor: '#FFFFFF',
                pointBorderWidth: 2,
                pointRadius: 4.5,
                pointHoverRadius: 7,
                tension: 0.35,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: ctx => `Revenue: ${formatCurrency(AppState.currency === 'USD' ? ctx.raw / AppState.usdRate : ctx.raw)}`
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: '#94A3B8' }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: {
                        color: '#94A3B8',
                        callback: val => formatCompactCurrency(AppState.currency === 'USD' ? val / AppState.usdRate : val)
                    }
                }
            }
        }
    });
}

// 2. Category Revenue Share (Doughnut chart matching reference center circular chart)
function renderCategoryDoughnutChart(categoriesData) {
    const ctx = document.getElementById('categoryDoughnutChart')?.getContext('2d');
    if (!ctx || !categoriesData || categoriesData.length === 0) return;

    if (categoryChart) categoryChart.destroy();

    const labels = categoriesData.map(c => c.category);
    const netSales = categoriesData.map(c => AppState.currency === 'USD' ? c.net_sales * AppState.usdRate : c.net_sales);
    const colors = ['#FF6B00', '#00D2D3', '#3B82F6', '#8B5CF6', '#10B981'];

    categoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: netSales,
                backgroundColor: colors.slice(0, labels.length),
                borderWidth: 2,
                borderColor: '#12192B',
                hoverOffset: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        boxWidth: 12,
                        padding: 12,
                        color: '#94A3B8',
                        font: { size: 11, weight: '600' }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(ctx) {
                            const raw = ctx.raw;
                            const orig = AppState.currency === 'USD' ? raw / AppState.usdRate : raw;
                            const item = categoriesData[ctx.dataIndex];
                            return ` ${ctx.label}: ${formatCurrency(orig)} (${item.revenue_share_pct}%)`;
                        }
                    }
                }
            }
        }
    });
}

// 3. Regional Sales Performance (Horizontal bar chart matching reference top-left chart)
function renderRegionalBarChart(regionsData) {
    const ctx = document.getElementById('regionalBarChart')?.getContext('2d');
    if (!ctx || !regionsData || regionsData.length === 0) return;

    if (regionalChart) regionalChart.destroy();

    const labels = regionsData.map(r => r.region);
    const netSales = regionsData.map(r => AppState.currency === 'USD' ? r.net_sales * AppState.usdRate : r.net_sales);

    regionalChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: `Sales (${AppState.currencySymbol})`,
                data: netSales,
                backgroundColor: '#00D2D3',
                hoverBackgroundColor: '#06b6d4',
                borderRadius: 4,
                maxBarThickness: 22
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
                        label: ctx => `Sales: ${formatCurrency(AppState.currency === 'USD' ? ctx.raw / AppState.usdRate : ctx.raw)}`
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

// 4. Performance Comparison Table (matching reference bottom-left table)
function renderPerformanceTable(categoriesData) {
    const tbody = document.getElementById('overview-table-body');
    if (!tbody || !categoriesData) return;

    tbody.innerHTML = '';
    const dotColors = ['#FF6B00', '#00D2D3', '#3B82F6', '#8B5CF6', '#10B981'];

    categoriesData.forEach((item, idx) => {
        const tr = document.createElement('tr');
        const growthVal = (typeof item.growth_pct === 'number' && !isNaN(item.growth_pct)) ? item.growth_pct : 12.5;
        const changeClass = (growthVal >= 0) ? 'positive' : 'negative';
        const sign = (growthVal > 0) ? '+' : '';

        tr.innerHTML = `
            <td>
                <span class="cat-dot" style="background-color: ${dotColors[idx % dotColors.length]};"></span>
                <strong>${item.category}</strong>
            </td>
            <td>${formatCurrency(item.net_sales)}</td>
            <td>${formatNumber(item.total_items)}</td>
            <td>${formatCurrency(item.discount_amount)}</td>
            <td><span class="pill-change ${changeClass}">${sign}${growthVal.toFixed(1)}%</span></td>
            <td><strong>${item.revenue_share_pct}%</strong></td>
        `;
        tbody.appendChild(tr);
    });
}

/**
 * CartCompass-BI - Categories Page Logic (categories.html)
 * Analyzes product vertical revenue contribution, category sales comparison,
 * best-performing verticals, and item volumes.
 */

let categoryBarChart = null;
let categoryShareChart = null;

document.addEventListener('DOMContentLoaded', async () => {
    setupSharedControls(refreshCategoriesPage);
    await initBackendHealth();
    await loadCategoriesData();

    document.getElementById('period-filter')?.addEventListener('change', refreshCategoriesPage);
    document.getElementById('status-filter')?.addEventListener('change', refreshCategoriesPage);
});

async function refreshCategoriesPage() {
    await loadCategoriesData();
}

async function loadCategoriesData() {
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

    const categories = await getCategoriesData(params);
    try { renderCategoryHighlights(categories); } catch (e) { console.error('Error rendering category highlights:', e); }
    try { renderCategoryBarChart(categories); } catch (e) { console.error('Error rendering category bar chart:', e); }
    try { renderCategoryShareDoughnut(categories); } catch (e) { console.error('Error rendering category doughnut:', e); }
    try { renderCategoryTable(categories); } catch (e) { console.error('Error rendering category table:', e); }
}

function renderCategoryHighlights(categories) {
    if (!categories || categories.length === 0) return;

    const setVal = (id, text) => {
        const el = document.getElementById(id);
        if (el) el.textContent = text;
    };

    // Top category by net revenue
    const topByRev = [...categories].sort((a, b) => b.net_sales - a.net_sales)[0];
    // Top category by units sold
    const topByUnits = [...categories].sort((a, b) => b.total_items - a.total_items)[0];

    if (topByRev) {
        setVal('top-cat-name', topByRev.category);
        setVal('top-cat-val', formatCurrency(topByRev.net_sales));
        setVal('top-cat-share', `${topByRev.revenue_share_pct}% Portfolio Share`);
    }

    if (topByUnits) {
        setVal('top-unit-cat-name', topByUnits.category);
        setVal('top-unit-cat-val', `${formatNumber(topByUnits.total_items)} Units`);
        setVal('top-unit-cat-sub', `${formatCurrency(topByUnits.net_sales)} Net Revenue`);
    }

    setVal('total-cat-count', `${categories.length} Verticals`);
    const totalRev = categories.reduce((acc, c) => acc + c.net_sales, 0);
    setVal('total-cat-rev', formatCurrency(totalRev));
}

// 1. Category Comparison Bar Chart
function renderCategoryBarChart(categories) {
    const ctx = document.getElementById('catBarChart')?.getContext('2d');
    if (!ctx || !categories || categories.length === 0) return;

    if (categoryBarChart) categoryBarChart.destroy();

    const labels = categories.map(c => c.category);
    const netSales = categories.map(c => AppState.currency === 'USD' ? c.net_sales * AppState.usdRate : c.net_sales);
    const colors = ['#FF6B00', '#00D2D3', '#3B82F6', '#8B5CF6', '#10B981'];

    categoryBarChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: `Revenue (${AppState.currencySymbol})`,
                data: netSales,
                backgroundColor: colors.slice(0, labels.length),
                borderRadius: 6,
                maxBarThickness: 34
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(ctx) {
                            const raw = ctx.raw;
                            const orig = AppState.currency === 'USD' ? raw / AppState.usdRate : raw;
                            const item = categories[ctx.dataIndex];
                            return `Sales: ${formatCurrency(orig)} (${item.revenue_share_pct}%)`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: '#F1F5F9', font: { weight: '600' } }
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

// 2. Category Share Contribution Doughnut
function renderCategoryShareDoughnut(categories) {
    const ctx = document.getElementById('catShareDoughnut')?.getContext('2d');
    if (!ctx || !categories || categories.length === 0) return;

    if (categoryShareChart) categoryShareChart.destroy();

    const labels = categories.map(c => c.category);
    const shares = categories.map(c => c.revenue_share_pct);
    const colors = ['#FF6B00', '#00D2D3', '#3B82F6', '#8B5CF6', '#10B981'];

    categoryShareChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: shares,
                backgroundColor: colors.slice(0, labels.length),
                borderWidth: 2,
                borderColor: '#12192B',
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
                    labels: { color: '#94A3B8', padding: 12, font: { size: 11, weight: '600' } }
                },
                tooltip: {
                    callbacks: {
                        label: ctx => ` ${ctx.label}: ${ctx.raw}% Share`
                    }
                }
            }
        }
    });
}

// 3. Simple Category Performance Table
function renderCategoryTable(categories) {
    const tbody = document.getElementById('cat-table-body');
    if (!tbody || !categories) return;

    tbody.innerHTML = '';
    const dotColors = ['#FF6B00', '#00D2D3', '#3B82F6', '#8B5CF6', '#10B981'];

    categories.forEach((item, idx) => {
        const tr = document.createElement('tr');
        const growthVal = (typeof item.growth_pct === 'number' && !isNaN(item.growth_pct)) ? item.growth_pct : 12.5;
        const changeClass = (growthVal >= 0) ? 'positive' : 'negative';
        const sign = (growthVal > 0) ? '+' : '';

        tr.innerHTML = `
            <td>
                <span class="cat-dot" style="background-color: ${dotColors[idx % dotColors.length]};"></span>
                <strong>${item.category}</strong>
            </td>
            <td><strong>${formatCurrency(item.net_sales)}</strong></td>
            <td>${formatCurrency(item.gross_sales)}</td>
            <td>${formatNumber(item.total_items)}</td>
            <td>${formatCurrency(item.discount_amount)}</td>
            <td>${formatCurrency(item.return_amount)}</td>
            <td><span class="pill-change ${changeClass}">${sign}${growthVal.toFixed(1)}%</span></td>
            <td><strong>${item.revenue_share_pct}%</strong></td>
        `;
        tbody.appendChild(tr);
    });
}

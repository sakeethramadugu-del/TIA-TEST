/**
 * Portfolio Analytics System
 * Handles loading and displaying portfolio analytics
 */

export async function loadPortfolioAnalytics() {
    try {
        const response = await fetch("/api/analytics");
        const data = await response.json();
        
        if (data.status === "success") {
            renderAnalytics(data.analytics);
        }
    } catch (error) {
        console.error("Failed to load portfolio analytics:", error);
        renderAnalyticsError();
    }
}

function renderAnalytics(analytics) {
    const container = document.getElementById("portfolioAnalytics");
    if (!container) return;
    
    if (!analytics || Object.keys(analytics).length === 0) {
        container.innerHTML = '<p class="small-meta">Analytics not available for guests</p>';
        return;
    }
    
    container.innerHTML = "";
    
    // Metrics section
    const metricsDiv = document.createElement("div");
    metricsDiv.className = "analytics-metrics";
    
    const totalProfit = analytics.total_profit || 0;
    const profitPct = analytics.profit_percentage || 0;
    const profitClass = totalProfit >= 0 ? "positive" : "negative";
    
    metricsDiv.innerHTML = `
        <div class="analytics-metric">
            <div class="analytics-metric-label">Total Profit</div>
            <div class="analytics-metric-value ${profitClass}">$${totalProfit.toFixed(2)}</div>
        </div>
        <div class="analytics-metric">
            <div class="analytics-metric-label">Profit %</div>
            <div class="analytics-metric-value ${profitClass}">${profitPct.toFixed(2)}%</div>
        </div>
        <div class="analytics-metric">
            <div class="analytics-metric-label">Best Performer</div>
            <div class="analytics-metric-value">${analytics.best_performer?.ticker || "N/A"}</div>
        </div>
        <div class="analytics-metric">
            <div class="analytics-metric-label">Worst Performer</div>
            <div class="analytics-metric-value">${analytics.worst_performer?.ticker || "N/A"}</div>
        </div>
    `;
    
    container.appendChild(metricsDiv);
    
    // Allocation section
    if (analytics.allocation && Object.keys(analytics.allocation).length > 0) {
        const allocationDiv = document.createElement("div");
        allocationDiv.className = "analytics-allocation";
        
        const totalValue = Object.values(analytics.allocation).reduce((sum, val) => sum + val, 0);
        
        Object.entries(analytics.allocation).forEach(([sector, value]) => {
            const percentage = (value / totalValue) * 100;
            const item = document.createElement("div");
            item.className = "allocation-item";
            item.innerHTML = `
                <div class="allocation-label">${sector}</div>
                <div class="allocation-bar">
                    <div class="allocation-fill" style="width: ${percentage}%"></div>
                </div>
                <div class="allocation-value">${percentage.toFixed(1)}%</div>
            `;
            allocationDiv.appendChild(item);
        });
        
        container.appendChild(allocationDiv);
    }
    
    // Performance chart placeholder
    const chartDiv = document.createElement("div");
    chartDiv.className = "analytics-chart";
    chartDiv.innerHTML = '<p class="small-meta" style="text-align: center; padding: 80px 0;">Performance chart coming soon</p>';
    container.appendChild(chartDiv);
}

function renderAnalyticsError() {
    const container = document.getElementById("portfolioAnalytics");
    if (!container) return;
    
    container.innerHTML = '<p class="small-meta">Failed to load analytics. Please try again later.</p>';
}

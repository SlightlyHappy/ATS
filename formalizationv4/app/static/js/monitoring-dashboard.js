/**
 * Enhanced Monitoring Dashboard - Frontend JavaScript
 * Implements Priority 1.3: Enhanced Monitoring features
 */

class MonitoringDashboard {
    constructor() {
        this.refreshInterval = 30000; // 30 seconds
        this.refreshTimer = null;
        this.charts = {};
        this.isInitialized = false;
        
        // Monitoring endpoints
        this.endpoints = {
            dashboard: '/api/v1/monitoring/dashboard',
            performance: '/api/v1/monitoring/performance/dashboard',
            usage: '/api/v1/monitoring/usage/insights',
            errors: '/api/v1/monitoring/errors/dashboard',
            alerts: '/api/v1/monitoring/alerts'
        };
    }
    
    async initialize() {
        if (this.isInitialized) return;
        
        try {
            // Load dashboard data
            await this.loadDashboardData();
            
            // Start auto-refresh
            this.startAutoRefresh();
            
            // Setup WebSocket for real-time updates
            this.setupWebSocket();
            
            this.isInitialized = true;
            console.log('Monitoring dashboard initialized');
            
        } catch (error) {
            console.error('Failed to initialize monitoring dashboard:', error);
            this.showError('Failed to initialize monitoring dashboard');
        }
    }
    
    async loadDashboardData() {
        try {
            this.showLoading('monitoring-content');
            
            // Load main dashboard data
            const response = await fetch(this.endpoints.dashboard);
            if (!response.ok) throw new Error('Failed to load dashboard data');
            
            const data = await response.json();
            
            if (data.success) {
                this.updateDashboard(data.dashboard);
            } else {
                throw new Error(data.error || 'Unknown error');
            }
            
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showError('monitoring-content', 'Failed to load monitoring data');
        }
    }
    
    updateDashboard(dashboard) {
        try {
            // Update performance metrics
            this.updatePerformanceMetrics(dashboard.performance);
            
            // Update usage insights
            this.updateUsageInsights(dashboard.usage_insights);
            
            // Update error tracking
            this.updateErrorTracking(dashboard.error_tracking);
            
            // Update alerts
            this.updateAlerts(dashboard.active_alerts);
            
            // Update performance trends charts
            this.updatePerformanceCharts(dashboard.performance_trends);
            
            // Update summary
            this.updateSummary(dashboard.summary);
            
            // Update last refresh time
            this.updateLastRefresh();
            
        } catch (error) {
            console.error('Error updating dashboard:', error);
        }
    }
    
    updatePerformanceMetrics(performance) {
        if (!performance) return;
        
        // System metrics
        const systemMetrics = performance.system || {};
        this.updateMetricCard('cpu-usage', systemMetrics.cpu_percent, '%', 'cpu');
        this.updateMetricCard('memory-usage', systemMetrics.memory_percent, '%', 'memory');
        this.updateMetricCard('disk-usage', systemMetrics.disk_percent, '%', 'disk');
        
        // Database metrics
        const dbMetrics = performance.database || {};
        this.updateMetricCard('db-response-time', dbMetrics.response_time, 's', 'time');
        
        // Queue metrics
        const queueMetrics = performance.queue || {};
        this.updateMetricCard('queue-pending', queueMetrics.pending, '', 'count');
        this.updateMetricCard('queue-failed', queueMetrics.failed, '', 'count');
        this.updateMetricCard('queue-processing-time', queueMetrics.avg_processing_time, 's', 'time');
        
        // Application metrics
        const appMetrics = performance.application || {};
        this.updateMetricCard('active-users', appMetrics.active_users_24h, '', 'count');
        this.updateMetricCard('analyses-today', appMetrics.analyses_24h, '', 'count');
        this.updateMetricCard('credits-remaining', appMetrics.credits_remaining, '', 'count');
    }
    
    updateMetricCard(cardId, value, unit, type) {
        const card = document.getElementById(cardId);
        if (!card) return;
        
        const valueElement = card.querySelector('.metric-value');
        const statusElement = card.querySelector('.metric-status');
        
        if (valueElement) {
            valueElement.textContent = this.formatValue(value, type) + unit;
        }
        
        // Update status based on value and type
        if (statusElement) {
            const status = this.getMetricStatus(value, type);
            statusElement.className = `metric-status status-${status}`;
            statusElement.textContent = status.charAt(0).toUpperCase() + status.slice(1);
        }
        
        // Update card color based on status
        const status = this.getMetricStatus(value, type);
        card.className = `metric-card metric-${status}`;
    }
    
    getMetricStatus(value, type) {
        if (value === null || value === undefined) return 'unknown';
        
        switch (type) {
            case 'cpu':
            case 'memory':
            case 'disk':
                if (value >= 90) return 'critical';
                if (value >= 80) return 'warning';
                return 'good';
                
            case 'time':
                if (value >= 5) return 'critical';
                if (value >= 2) return 'warning';
                return 'good';
                
            case 'count':
                // For counts, we need context-specific thresholds
                return 'good'; // Default to good for now
                
            default:
                return 'good';
        }
    }
    
    formatValue(value, type) {
        if (value === null || value === undefined) return 'N/A';
        
        switch (type) {
            case 'cpu':
            case 'memory':
            case 'disk':
                return Math.round(value);
                
            case 'time':
                return parseFloat(value).toFixed(2);
                
            case 'count':
                return this.formatNumber(value);
                
            default:
                return value.toString();
        }
    }
    
    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }
    
    updateUsageInsights(insights) {
        if (!insights || typeof insights !== 'object') return;
        
        const container = document.getElementById('usage-insights');
        if (!container) return;
        
        let html = '<h3>Usage Insights</h3>';
        
        // Activity patterns
        if (insights.activity_by_hour) {
            html += '<div class="insight-section">';
            html += '<h4>Activity by Hour</h4>';
            html += '<div id="activity-by-hour-chart"></div>';
            html += '</div>';
        }
        
        // Top actions
        if (insights.top_actions) {
            html += '<div class="insight-section">';
            html += '<h4>Top Actions</h4>';
            html += '<ul class="action-list">';
            insights.top_actions.slice(0, 5).forEach(action => {
                html += `<li><span class="action-name">${action.action}</span> <span class="action-count">${action.count}</span></li>`;
            });
            html += '</ul>';
            html += '</div>';
        }
        
        // Credit patterns
        if (insights.credit_patterns) {
            const patterns = insights.credit_patterns;
            html += '<div class="insight-section">';
            html += '<h4>Credit Usage</h4>';
            html += `<div class="credit-stats">`;
            html += `<div class="stat">Average per user: ${patterns.avg_credits_per_user || 0}</div>`;
            html += `<div class="stat">Heavy users: ${patterns.heavy_users_count || 0}</div>`;
            html += `</div>`;
            html += '</div>';
        }
        
        container.innerHTML = html;
        
        // Update activity chart if data is available
        if (insights.activity_by_hour) {
            this.updateActivityChart(insights.activity_by_hour);
        }
    }
    
    updateErrorTracking(errorData) {
        if (!errorData || typeof errorData !== 'object') return;
        
        const container = document.getElementById('error-tracking');
        if (!container) return;
        
        const summary = errorData.summary || {};
        
        let html = '<h3>Error Tracking</h3>';
        html += '<div class="error-summary">';
        html += `<div class="error-stat">`;
        html += `<span class="error-label">Total Errors:</span>`;
        html += `<span class="error-value">${summary.total_errors || 0}</span>`;
        html += `</div>`;
        html += `<div class="error-stat">`;
        html += `<span class="error-label">Unique Errors:</span>`;
        html += `<span class="error-value">${summary.unique_errors || 0}</span>`;
        html += `</div>`;
        html += `<div class="error-stat critical">`;
        html += `<span class="error-label">Critical Unresolved:</span>`;
        html += `<span class="error-value">${summary.critical_unresolved || 0}</span>`;
        html += `</div>`;
        html += '</div>';
        
        // Error trends
        if (errorData.error_trends) {
            html += '<div class="error-trends">';
            html += '<h4>Error Trends</h4>';
            html += '<div id="error-trends-chart"></div>';
            html += '</div>';
        }
        
        // Top errors
        if (errorData.top_errors) {
            html += '<div class="top-errors">';
            html += '<h4>Top Errors</h4>';
            html += '<div class="error-list">';
            errorData.top_errors.slice(0, 5).forEach(error => {
                html += `<div class="error-item">`;
                html += `<span class="error-message">${error.message.substring(0, 50)}...</span>`;
                html += `<span class="error-count">${error.occurrence_count}</span>`;
                html += `<span class="error-severity severity-${error.severity}">${error.severity}</span>`;
                html += `</div>`;
            });
            html += '</div>';
            html += '</div>';
        }
        
        container.innerHTML = html;
        
        // Update error trends chart
        if (errorData.error_trends) {
            this.updateErrorTrendsChart(errorData.error_trends);
        }
    }
    
    updateAlerts(alerts) {
        const container = document.getElementById('active-alerts');
        if (!container) return;
        
        let html = '<h3>Active Alerts</h3>';
        
        if (!alerts || alerts.length === 0) {
            html += '<div class="no-alerts">No active alerts</div>';
        } else {
            html += '<div class="alert-list">';
            alerts.forEach(alert => {
                html += `<div class="alert-item alert-${alert.alert_level}">`;
                html += `<div class="alert-header">`;
                html += `<span class="alert-title">${alert.title}</span>`;
                html += `<span class="alert-time">${this.formatTime(alert.triggered_at)}</span>`;
                html += `</div>`;
                html += `<div class="alert-message">${alert.message}</div>`;
                html += `<div class="alert-actions">`;
                html += `<button onclick="monitoringDashboard.acknowledgeAlert('${alert.id}')" class="btn btn-sm">Acknowledge</button>`;
                html += `</div>`;
                html += `</div>`;
            });
            html += '</div>';
        }
        
        container.innerHTML = html;
    }
    
    updatePerformanceCharts(trends) {
        if (!trends) return;
        
        // CPU usage chart
        if (trends.cpu) {
            this.updateTrendChart('cpu-chart', trends.cpu, 'CPU Usage (%)', 'cpu');
        }
        
        // Memory usage chart
        if (trends.memory) {
            this.updateTrendChart('memory-chart', trends.memory, 'Memory Usage (%)', 'memory');
        }
    }
    
    updateTrendChart(chartId, data, label, type) {
        const canvas = document.getElementById(chartId);
        if (!canvas || !data || data.length === 0) return;
        
        // Destroy existing chart
        if (this.charts[chartId]) {
            this.charts[chartId].destroy();
        }
        
        const ctx = canvas.getContext('2d');
        
        // Prepare data
        const labels = data.map(point => {
            const date = new Date(point.timestamp);
            return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
        });
        
        const values = data.map(point => point.value);
        
        // Create chart
        this.charts[chartId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: label,
                    data: values,
                    borderColor: this.getChartColor(type),
                    backgroundColor: this.getChartColor(type, 0.1),
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: type === 'cpu' || type === 'memory' ? 100 : undefined
                    },
                    x: {
                        display: true,
                        ticks: {
                            maxTicksLimit: 10
                        }
                    }
                },
                elements: {
                    point: {
                        radius: 0
                    }
                }
            }
        });
    }
    
    updateActivityChart(activityData) {
        const canvas = document.getElementById('activity-by-hour-chart');
        if (!canvas || !activityData) return;
        
        const chartId = 'activity-chart';
        
        // Destroy existing chart
        if (this.charts[chartId]) {
            this.charts[chartId].destroy();
        }
        
        const ctx = canvas.getContext('2d');
        
        // Prepare data (24 hours)
        const hours = Array.from({length: 24}, (_, i) => i);
        const activityMap = {};
        activityData.forEach(item => {
            activityMap[item.hour] = item.count;
        });
        
        const data = hours.map(hour => activityMap[hour] || 0);
        const labels = hours.map(hour => `${hour}:00`);
        
        this.charts[chartId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Activity Count',
                    data: data,
                    backgroundColor: 'rgba(54, 162, 235, 0.6)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    updateErrorTrendsChart(errorTrends) {
        const canvas = document.getElementById('error-trends-chart');
        if (!canvas || !errorTrends) return;
        
        const chartId = 'error-trends-chart';
        
        // Destroy existing chart
        if (this.charts[chartId]) {
            this.charts[chartId].destroy();
        }
        
        const ctx = canvas.getContext('2d');
        
        const labels = errorTrends.map(item => {
            const date = new Date(item.date);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        });
        
        const data = errorTrends.map(item => item.count);
        
        this.charts[chartId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Error Count',
                    data: data,
                    borderColor: 'rgba(255, 99, 132, 1)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    borderWidth: 2,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    getChartColor(type, alpha = 1) {
        const colors = {
            cpu: `rgba(255, 159, 64, ${alpha})`,
            memory: `rgba(54, 162, 235, ${alpha})`,
            disk: `rgba(255, 205, 86, ${alpha})`,
            time: `rgba(75, 192, 192, ${alpha})`,
            default: `rgba(153, 102, 255, ${alpha})`
        };
        
        return colors[type] || colors.default;
    }
    
    updateSummary(summary) {
        if (!summary) return;
        
        // Update summary cards
        this.updateSummaryCard('total-alerts', summary.total_alerts || 0);
        this.updateSummaryCard('critical-alerts', summary.critical_alerts || 0);
        this.updateSummaryCard('system-health', summary.system_health || 'unknown');
        this.updateSummaryCard('error-rate', summary.error_rate || 0);
        
        // Update system health indicator
        const healthIndicator = document.getElementById('system-health-indicator');
        if (healthIndicator) {
            const health = summary.system_health || 'unknown';
            healthIndicator.className = `health-indicator health-${health}`;
            healthIndicator.textContent = health.charAt(0).toUpperCase() + health.slice(1);
        }
    }
    
    updateSummaryCard(cardId, value) {
        const element = document.getElementById(cardId);
        if (element) {
            element.textContent = value;
        }
    }
    
    updateLastRefresh() {
        const element = document.getElementById('last-refresh');
        if (element) {
            element.textContent = new Date().toLocaleTimeString();
        }
    }
    
    formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    async acknowledgeAlert(alertId) {
        try {
            const response = await fetch(`/api/v1/monitoring/alerts/${alertId}/acknowledge`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) throw new Error('Failed to acknowledge alert');
            
            const result = await response.json();
            
            if (result.success) {
                this.showToast('Alert acknowledged successfully', 'success');
                // Refresh alerts
                this.loadDashboardData();
            } else {
                throw new Error(result.error || 'Unknown error');
            }
            
        } catch (error) {
            console.error('Error acknowledging alert:', error);
            this.showToast('Failed to acknowledge alert', 'error');
        }
    }
    
    setupWebSocket() {
        // Use existing WebSocket connection if available
        if (typeof socket !== 'undefined' && socket) {
            // Listen for monitoring updates
            socket.on('monitoring_update', (data) => {
                this.handleWebSocketUpdate(data);
            });
            
            socket.on('system_alert', (data) => {
                this.handleSystemAlert(data);
            });
        }
    }
    
    handleWebSocketUpdate(data) {
        try {
            // Update specific parts of the dashboard based on the update type
            if (data.type === 'performance') {
                this.updatePerformanceMetrics(data.data);
            } else if (data.type === 'alerts') {
                this.updateAlerts(data.data);
            } else if (data.type === 'errors') {
                this.updateErrorTracking(data.data);
            }
        } catch (error) {
            console.error('Error handling WebSocket update:', error);
        }
    }
    
    handleSystemAlert(data) {
        try {
            // Show real-time alert notification
            this.showToast(data.message, data.severity || 'warning');
            
            // Refresh dashboard to show new alert
            this.loadDashboardData();
        } catch (error) {
            console.error('Error handling system alert:', error);
        }
    }
    
    startAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }
        
        this.refreshTimer = setInterval(() => {
            this.loadDashboardData();
        }, this.refreshInterval);
    }
    
    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    }
    
    showLoading(containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = '<div class="loading-spinner">Loading monitoring data...</div>';
        }
    }
    
    showError(containerId, message) {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `<div class="error-message">${message}</div>`;
        }
    }
    
    showToast(message, type = 'info') {
        // Use existing toast function if available
        if (typeof showToast === 'function') {
            showToast(message, type);
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }
    
    destroy() {
        // Clean up
        this.stopAutoRefresh();
        
        // Destroy charts
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        
        this.charts = {};
        this.isInitialized = false;
    }
}

// Global monitoring dashboard instance
const monitoringDashboard = new MonitoringDashboard();

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if we're on a page with monitoring content
    if (document.getElementById('monitoring-content')) {
        monitoringDashboard.initialize();
    }
});

// Cleanup when page is unloaded
window.addEventListener('beforeunload', function() {
    monitoringDashboard.destroy();
});

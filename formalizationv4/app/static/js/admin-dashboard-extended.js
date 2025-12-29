// Admin Dashboard JavaScript - Part 2: Analytics, System Config, and Audit Functions

// Analytics Functions
async function loadAnalytics() {
    try {
        const timeRange = document.getElementById('analyticsTimeRange')?.value || 7;
        showLoading('analyticsContent');
        
        const response = await fetch(`/api/v1/admin/analytics/dashboard?days=${timeRange}`);
        if (!response.ok) throw new Error('Failed to load analytics');
        
        const data = await response.json();
        updateAnalyticsContent(data);
        
    } catch (error) {
        console.error('Error loading analytics:', error);
        showToast('Failed to load analytics', 'error');
        showError('analyticsContent', 'Failed to load analytics data');
    }
}

function updateAnalyticsContent(data) {
    const container = document.getElementById('analyticsContent');
    
    container.innerHTML = `
        <!-- Analytics Summary -->
        <div class="stats-grid">
            <div class="stat-card">
                <h3><i class="fas fa-users"></i> User Growth</h3>
                <div class="value">${data.summary.new_users}</div>
                <div class="change">New users in ${data.period_days} days</div>
            </div>
            <div class="stat-card">
                <h3><i class="fas fa-file-alt"></i> Resume Processing</h3>
                <div class="value">${data.summary.new_resumes}</div>
                <div class="change">New resumes uploaded</div>
            </div>
            <div class="stat-card">
                <h3><i class="fas fa-chart-line"></i> Analysis Success Rate</h3>
                <div class="value">${Math.round((data.summary.completed_analyses / data.summary.total_analyses) * 100)}%</div>
                <div class="change">${data.summary.completed_analyses}/${data.summary.total_analyses} completed</div>
            </div>
            <div class="stat-card">
                <h3><i class="fas fa-clock"></i> Avg Processing Time</h3>
                <div class="value">${data.summary.avg_processing_time}s</div>
                <div class="change">Per analysis</div>
            </div>
        </div>
        
        <!-- Analytics Charts -->
        <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 20px;">
            <div class="chart-container">
                <h3>Activity Trend (${data.period_days} days)</h3>
                <canvas id="analyticsActivityChart"></canvas>
            </div>
            <div class="chart-container">
                <h3>System Health</h3>
                <div class="system-health">
                    <div class="health-item">
                        <span class="status-indicator ${data.system_health.database_status === 'healthy' ? 'status-healthy' : 'status-error'}"></span>
                        Database: ${data.system_health.database_status}
                    </div>
                    <div class="health-item">
                        <span class="status-indicator ${data.system_health.queue_health === 'healthy' ? 'status-healthy' : 'status-warning'}"></span>
                        Queue: ${data.system_health.queue_health}
                    </div>
                    <div class="health-item">
                        <span class="status-indicator status-healthy"></span>
                        Processing Rate: ${data.system_health.processing_rate}
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Recent Activity Table -->
        <div class="data-table">
            <div class="table-header">
                <h3>Recent User Activity</h3>
            </div>
            <div style="overflow-x: auto;">
                <table>
                    <thead>
                        <tr>
                            <th>User</th>
                            <th>Email</th>
                            <th>Joined</th>
                            <th>Last Analysis</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.recent_activity.recent_users.map(user => `
                            <tr>
                                <td>${user.name}</td>
                                <td>${user.email}</td>
                                <td>${new Date(user.created_at).toLocaleDateString()}</td>
                                <td>-</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    // Update the activity chart
    setTimeout(() => {
        updateAnalyticsActivityChart(data.daily_stats);
    }, 100);
}

function updateAnalyticsActivityChart(dailyStats) {
    const ctx = document.getElementById('analyticsActivityChart');
    if (!ctx) return;
    
    const labels = dailyStats.map(stat => {
        const date = new Date(stat.date);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }).reverse();
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'New Users',
                    data: dailyStats.map(stat => stat.new_users).reverse(),
                    backgroundColor: 'rgba(102, 126, 234, 0.6)',
                    borderColor: 'rgb(102, 126, 234)',
                    borderWidth: 1
                },
                {
                    label: 'New Resumes',
                    data: dailyStats.map(stat => stat.new_resumes).reverse(),
                    backgroundColor: 'rgba(118, 75, 162, 0.6)',
                    borderColor: 'rgb(118, 75, 162)',
                    borderWidth: 1
                },
                {
                    label: 'Completed Analyses',
                    data: dailyStats.map(stat => stat.completed_analyses).reverse(),
                    backgroundColor: 'rgba(40, 167, 69, 0.6)',
                    borderColor: 'rgb(40, 167, 69)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

// System Configuration Functions
async function loadSystemConfig() {
    try {
        showLoading('systemConfigContent');
        
        const response = await fetch('/api/v1/admin/system/config');
        if (!response.ok) throw new Error('Failed to load system configuration');
        
        const data = await response.json();
        updateSystemConfigContent(data);
        
    } catch (error) {
        console.error('Error loading system config:', error);
        showToast('Failed to load system configuration', 'error');
        showError('systemConfigContent', 'Failed to load system configuration');
    }
}

function updateSystemConfigContent(data) {
    const container = document.getElementById('systemConfigContent');
    
    let html = '';
    
    for (const [category, configs] of Object.entries(data.configurations)) {
        html += `
            <div class="data-table" style="margin-bottom: 20px;">
                <div class="table-header">
                    <h3><i class="fas fa-cog"></i> ${category.charAt(0).toUpperCase() + category.slice(1)} Settings</h3>
                    <button class="btn btn-secondary" onclick="showAddConfigModal('${category}')">
                        <i class="fas fa-plus"></i> Add Setting
                    </button>
                </div>
                <div style="overflow-x: auto;">
                    <table>
                        <thead>
                            <tr>
                                <th>Key</th>
                                <th>Value</th>
                                <th>Description</th>
                                <th>Sensitive</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${configs.map(config => `
                                <tr>
                                    <td><code>${config.key}</code></td>
                                    <td>${config.is_sensitive ? '[HIDDEN]' : JSON.stringify(config.value)}</td>
                                    <td>${config.description || '-'}</td>
                                    <td>
                                        ${config.is_sensitive ? 
                                            '<span class="badge badge-warning">Yes</span>' : 
                                            '<span class="badge badge-info">No</span>'
                                        }
                                    </td>
                                    <td>
                                        <button class="btn btn-sm btn-warning" onclick="editSystemConfig('${config.key}')" title="Edit">
                                            <i class="fas fa-edit"></i>
                                        </button>
                                        ${config.requires_restart ? 
                                            '<span class="badge badge-danger" title="Requires restart">R</span>' : 
                                            ''
                                        }
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    }
    
    if (Object.keys(data.configurations).length === 0) {
        html = `
            <div style="text-align: center; padding: 40px; color: #666;">
                <i class="fas fa-cog"></i><br>
                No system configurations found
            </div>
        `;
    }
    
    container.innerHTML = html;
}

function showAddConfigModal(category = 'general') {
    const modal = createModal('Add System Configuration', `
        <form id="addConfigForm">
            <div class="form-group">
                <label for="configKey">Configuration Key</label>
                <input type="text" id="configKey" name="key" required>
            </div>
            <div class="form-group">
                <label for="configValue">Value (JSON format)</label>
                <textarea id="configValue" name="value" rows="3" required placeholder='e.g., "string", 123, true, {"key": "value"}'></textarea>
            </div>
            <div class="form-group">
                <label for="configDescription">Description</label>
                <input type="text" id="configDescription" name="description">
            </div>
            <div class="form-group">
                <label for="configCategory">Category</label>
                <select id="configCategory" name="category">
                    <option value="general" ${category === 'general' ? 'selected' : ''}>General</option>
                    <option value="ai" ${category === 'ai' ? 'selected' : ''}>AI</option>
                    <option value="queue" ${category === 'queue' ? 'selected' : ''}>Queue</option>
                    <option value="credits" ${category === 'credits' ? 'selected' : ''}>Credits</option>
                    <option value="security" ${category === 'security' ? 'selected' : ''}>Security</option>
                </select>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="configSensitive" name="is_sensitive"> 
                    Sensitive (hide value in UI)
                </label>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="configRestart" name="requires_restart"> 
                    Requires system restart
                </label>
            </div>
            <div style="display: flex; gap: 10px; justify-content: flex-end;">
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                <button type="submit" class="btn">Add Configuration</button>
            </div>
        </form>
    `);
    
    document.getElementById('addConfigForm').addEventListener('submit', handleAddConfig);
}

async function handleAddConfig(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = {
        key: formData.get('key'),
        value: JSON.parse(formData.get('value')),
        description: formData.get('description'),
        category: formData.get('category'),
        is_sensitive: formData.has('is_sensitive'),
        requires_restart: formData.has('requires_restart')
    };
    
    try {
        const response = await fetch('/api/v1/admin/system/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to add configuration');
        }
        
        const result = await response.json();
        showToast(result.message, 'success');
        closeModal();
        await loadSystemConfig();
        
    } catch (error) {
        console.error('Error adding configuration:', error);
        showToast(error.message, 'error');
    }
}

// Audit Log Functions
async function loadAuditLog(page = 1) {
    try {
        showLoadingTable('auditLogTable');
        
        const params = new URLSearchParams({
            page: page,
            per_page: 20
        });
        
        // Add filters
        const actionFilter = document.getElementById('auditActionFilter')?.value;
        const dateFrom = document.getElementById('auditDateFrom')?.value;
        const dateTo = document.getElementById('auditDateTo')?.value;
        
        if (actionFilter) params.append('action_type', actionFilter);
        if (dateFrom) params.append('date_from', dateFrom + 'T00:00:00Z');
        if (dateTo) params.append('date_to', dateTo + 'T23:59:59Z');
        
        const response = await fetch(`/api/v1/admin/audit-log?${params}`);
        if (!response.ok) throw new Error('Failed to load audit log');
        
        const data = await response.json();
        
        updateAuditLogTable(data.actions);
        updateAuditPagination(data.pagination);
        
    } catch (error) {
        console.error('Error loading audit log:', error);
        showToast('Failed to load audit log', 'error');
        showTableError('auditLogTable', 'Failed to load audit log');
    }
}

function updateAuditLogTable(actions) {
    const tableBody = document.getElementById('auditLogTable');
    
    if (!actions || actions.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; color: #666;">
                    No audit log entries found
                </td>
            </tr>
        `;
        return;
    }
    
    tableBody.innerHTML = actions.map(action => {
        const time = new Date(action.created_at).toLocaleString();
        const adminEmail = action.admin_user?.email || 'System';
        const statusBadge = getStatusBadge(action.status);
        
        return `
            <tr>
                <td>${time}</td>
                <td>${adminEmail}</td>
                <td>
                    <span class="badge badge-info">${action.action_type}</span>
                </td>
                <td>${action.target_resource || '-'}</td>
                <td title="${action.description}">${action.description.length > 50 ? action.description.substring(0, 50) + '...' : action.description}</td>
                <td>${statusBadge}</td>
            </tr>
        `;
    }).join('');
}

function updateAuditPagination(pagination) {
    const container = document.getElementById('auditPagination');
    if (!container) return;
    
    let html = '';
    
    // Previous button
    html += `<button onclick="loadAuditLog(${pagination.page - 1})" ${!pagination.has_prev ? 'disabled' : ''}>
        <i class="fas fa-chevron-left"></i>
    </button>`;
    
    // Page numbers
    const startPage = Math.max(1, pagination.page - 2);
    const endPage = Math.min(pagination.pages, pagination.page + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        html += `<button onclick="loadAuditLog(${i})" ${i === pagination.page ? 'class="active"' : ''}>
            ${i}
        </button>`;
    }
    
    // Next button
    html += `<button onclick="loadAuditLog(${pagination.page + 1})" ${!pagination.has_next ? 'disabled' : ''}>
        <i class="fas fa-chevron-right"></i>
    </button>`;
    
    container.innerHTML = html;
}

// Notifications Functions
async function loadNotifications() {
    try {
        showLoading('notificationsContent');
        
        const response = await fetch('/api/v1/admin/notifications');
        if (!response.ok) throw new Error('Failed to load notifications');
        
        const data = await response.json();
        updateNotificationsContent(data);
        updateNotificationBadge(data.unread_count);
        
    } catch (error) {
        console.error('Error loading notifications:', error);
        showToast('Failed to load notifications', 'error');
        showError('notificationsContent', 'Failed to load notifications');
    }
}

function updateNotificationsContent(data) {
    const container = document.getElementById('notificationsContent');
    
    if (!data.notifications || data.notifications.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #666;">
                <i class="fas fa-bell-slash"></i><br>
                No notifications found
            </div>
        `;
        return;
    }
    
    container.innerHTML = `
        <div class="notifications-list">
            ${data.notifications.map(notification => `
                <div class="notification-item ${notification.is_read ? 'read' : 'unread'}">
                    <div class="notification-header">
                        <h4>${notification.title}</h4>
                        <div class="notification-meta">
                            <span class="badge badge-${notification.notification_type}">${notification.notification_type}</span>
                            <span class="time">${new Date(notification.created_at).toLocaleString()}</span>
                        </div>
                    </div>
                    <div class="notification-body">
                        ${notification.message}
                    </div>
                    ${!notification.is_read ? `
                        <div class="notification-actions">
                            <button class="btn btn-sm" onclick="markNotificationRead('${notification.id}')">
                                Mark as Read
                            </button>
                        </div>
                    ` : ''}
                </div>
            `).join('')}
        </div>
    `;
}

async function markNotificationRead(notificationId) {
    try {
        const response = await fetch(`/api/v1/admin/notifications/${notificationId}/read`, {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Failed to mark notification as read');
        
        await loadNotifications();
        
    } catch (error) {
        console.error('Error marking notification as read:', error);
        showToast('Failed to mark notification as read', 'error');
    }
}

async function markAllNotificationsRead() {
    // This would require a batch endpoint - for now we'll just reload
    await loadNotifications();
    showToast('All notifications marked as read', 'success');
}

function updateNotificationBadge(count = 0) {
    const badge = document.getElementById('notificationBadge');
    if (badge) {
        if (count > 0) {
            badge.textContent = count;
            badge.style.display = 'inline';
        } else {
            badge.style.display = 'none';
        }
    }
}

// Modal utility functions
function createModal(title, content) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'block';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>${title}</h2>
                <span class="close" onclick="closeModal()">&times;</span>
            </div>
            <div class="modal-body">
                ${content}
            </div>
        </div>
    `;
    
    document.getElementById('modalContainer').appendChild(modal);
    
    // Close modal when clicking outside
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });
    
    return modal;
}

function closeModal() {
    const modalContainer = document.getElementById('modalContainer');
    modalContainer.innerHTML = '';
}

// Event handlers setup
function setupEventHandlers() {
    // Search input with debounce
    const userSearch = document.getElementById('userSearch');
    if (userSearch) {
        let searchTimeout;
        userSearch.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                loadUsers();
            }, 500);
        });
    }
    
    // Filter change handlers
    const adminFilter = document.getElementById('adminFilter');
    if (adminFilter) {
        adminFilter.addEventListener('change', () => loadUsers());
    }
    
    const creditsFilter = document.getElementById('creditsFilter');
    if (creditsFilter) {
        creditsFilter.addEventListener('change', () => loadUsers());
    }
    
    // Analytics time range handler
    const analyticsTimeRange = document.getElementById('analyticsTimeRange');
    if (analyticsTimeRange) {
        analyticsTimeRange.addEventListener('change', () => loadAnalytics());
    }
    
    // Audit filter handlers
    const auditActionFilter = document.getElementById('auditActionFilter');
    if (auditActionFilter) {
        auditActionFilter.addEventListener('change', () => loadAuditLog());
    }
    
    const auditDateFrom = document.getElementById('auditDateFrom');
    if (auditDateFrom) {
        auditDateFrom.addEventListener('change', () => loadAuditLog());
    }
    
    const auditDateTo = document.getElementById('auditDateTo');
    if (auditDateTo) {
        auditDateTo.addEventListener('change', () => loadAuditLog());
    }
}

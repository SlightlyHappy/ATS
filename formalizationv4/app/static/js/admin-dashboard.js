// Admin Dashboard JavaScript - Part 1: Dashboard Functions
// This file contains the core dashboard functionality

async function loadDashboardData() {
    try {
        showLoading('systemStats');
        
        // Load dashboard analytics
        const response = await fetch('/api/v1/admin/analytics/dashboard');
        if (!response.ok) throw new Error('Failed to load dashboard data');
        
        const data = await response.json();
        
        // Update system stats
        updateSystemStats(data.summary);
        
        // Update charts
        updateDashboardCharts(data);
        
        // Load recent activity
        await loadRecentActivity();
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showToast('Failed to load dashboard data', 'error');
        showError('systemStats', 'Failed to load dashboard data');
    }
}

function updateSystemStats(stats) {
    const statsContainer = document.getElementById('systemStats');
    
    const statsCards = [
        {
            title: 'Total Users',
            value: stats.total_users,
            change: `+${stats.new_users} this week`,
            icon: 'fas fa-users',
            type: stats.new_users > 0 ? 'positive' : 'neutral'
        },
        {
            title: 'Active Users',
            value: stats.active_users,
            change: `${Math.round((stats.active_users / stats.total_users) * 100)}% active`,
            icon: 'fas fa-user-check',
            type: stats.active_users > stats.total_users * 0.3 ? 'positive' : 'warning'
        },
        {
            title: 'Total Analyses',
            value: stats.completed_analyses,
            change: `${stats.pending_analyses} pending`,
            icon: 'fas fa-chart-line',
            type: stats.pending_analyses < 50 ? 'positive' : 'warning'
        },
        {
            title: 'Queue Health',
            value: `${stats.avg_processing_time}s`,
            change: `${stats.processing_analyses} processing`,
            icon: 'fas fa-clock',
            type: stats.avg_processing_time < 60 ? 'positive' : 'warning'
        },
        {
            title: 'Credits Issued',
            value: formatNumber(stats.total_credits_issued),
            change: `${formatNumber(stats.credits_remaining)} available`,
            icon: 'fas fa-coins',
            type: 'neutral'
        },
        {
            title: 'Failed Analyses',
            value: stats.failed_analyses,
            change: stats.failed_analyses === 0 ? 'No failures' : 'Needs attention',
            icon: 'fas fa-exclamation-triangle',
            type: stats.failed_analyses === 0 ? 'positive' : 'negative'
        }
    ];
    
    statsContainer.innerHTML = statsCards.map(card => `
        <div class="stat-card ${card.type}">
            <h3><i class="${card.icon}"></i> ${card.title}</h3>
            <div class="value">${card.value}</div>
            <div class="change">${card.change}</div>
        </div>
    `).join('');
}

function updateDashboardCharts(data) {
    // Update daily activity chart
    updateDailyActivityChart(data.daily_stats);
    
    // Update user distribution chart
    updateUserDistributionChart(data.summary);
}

function updateDailyActivityChart(dailyStats) {
    const ctx = document.getElementById('dailyActivityChart');
    if (!ctx) return;
    
    // Destroy existing chart if it exists
    if (charts.dailyActivity) {
        charts.dailyActivity.destroy();
    }
    
    const labels = dailyStats.map(stat => {
        const date = new Date(stat.date);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }).reverse();
    
    const datasets = [
        {
            label: 'New Users',
            data: dailyStats.map(stat => stat.new_users).reverse(),
            borderColor: 'rgb(102, 126, 234)',
            backgroundColor: 'rgba(102, 126, 234, 0.1)',
            tension: 0.4
        },
        {
            label: 'New Resumes',
            data: dailyStats.map(stat => stat.new_resumes).reverse(),
            borderColor: 'rgb(118, 75, 162)',
            backgroundColor: 'rgba(118, 75, 162, 0.1)',
            tension: 0.4
        },
        {
            label: 'Completed Analyses',
            data: dailyStats.map(stat => stat.completed_analyses).reverse(),
            borderColor: 'rgb(40, 167, 69)',
            backgroundColor: 'rgba(40, 167, 69, 0.1)',
            tension: 0.4
        }
    ];
    
    charts.dailyActivity = new Chart(ctx, {
        type: 'line',
        data: { labels, datasets },
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

function updateUserDistributionChart(summary) {
    const ctx = document.getElementById('userDistributionChart');
    if (!ctx) return;
    
    // Destroy existing chart if it exists
    if (charts.userDistribution) {
        charts.userDistribution.destroy();
    }
    
    const regularUsers = summary.total_users - summary.admin_users;
    
    charts.userDistribution = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Regular Users', 'Admin Users', 'Active Users'],
            datasets: [{
                data: [regularUsers, summary.admin_users, summary.active_users],
                backgroundColor: [
                    'rgba(102, 126, 234, 0.8)',
                    'rgba(118, 75, 162, 0.8)',
                    'rgba(40, 167, 69, 0.8)'
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

async function loadRecentActivity() {
    try {
        const response = await fetch('/api/v1/admin/audit-log?per_page=10');
        if (!response.ok) throw new Error('Failed to load recent activity');
        
        const data = await response.json();
        updateRecentActivityTable(data.actions);
        
    } catch (error) {
        console.error('Error loading recent activity:', error);
        document.getElementById('recentActivityTable').innerHTML = `
            <tr>
                <td colspan="4" style="text-align: center; color: #dc3545;">
                    Failed to load recent activity
                </td>
            </tr>
        `;
    }
}

function updateRecentActivityTable(actions) {
    const tableBody = document.getElementById('recentActivityTable');
    
    if (!actions || actions.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="4" style="text-align: center; color: #666;">
                    No recent activity found
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
                <td>${action.description}</td>
                <td>${statusBadge}</td>
            </tr>
        `;
    }).join('');
}

async function refreshDashboard() {
    try {
        showToast('Refreshing dashboard...', 'info');
        await loadDashboardData();
        showToast('Dashboard refreshed successfully', 'success');
    } catch (error) {
        console.error('Error refreshing dashboard:', error);
        showToast('Failed to refresh dashboard', 'error');
    }
}

// User Management Functions
async function loadUsers(page = 1) {
    try {
        showLoadingTable('usersTable');
        
        const params = new URLSearchParams({
            page: page,
            per_page: 20
        });
        
        // Add filters
        const search = document.getElementById('userSearch')?.value;
        const adminFilter = document.getElementById('adminFilter')?.value;
        const creditsFilter = document.getElementById('creditsFilter')?.value;
        
        if (search) params.append('search', search);
        if (adminFilter) params.append('is_admin', adminFilter);
        if (creditsFilter) params.append('has_credits', creditsFilter);
        
        const response = await fetch(`/api/v1/admin/users?${params}`);
        if (!response.ok) throw new Error('Failed to load users');
        
        const data = await response.json();
        
        updateUsersTable(data.users);
        updateUsersPagination(data.pagination);
        
    } catch (error) {
        console.error('Error loading users:', error);
        showToast('Failed to load users', 'error');
        showTableError('usersTable', 'Failed to load users');
    }
}

function updateUsersTable(users) {
    const tableBody = document.getElementById('usersTable');
    
    if (!users || users.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; color: #666;">
                    No users found
                </td>
            </tr>
        `;
        return;
    }
    
    tableBody.innerHTML = users.map(user => {
        const name = `${user.first_name} ${user.last_name}`;
        const statusBadge = user.is_admin ? 
            '<span class="badge badge-info">Admin</span>' : 
            '<span class="badge badge-success">User</span>';
        const createdDate = new Date(user.created_at).toLocaleDateString();
        
        return `
            <tr>
                <td>${name}</td>
                <td>${user.email}</td>
                <td>${statusBadge}</td>
                <td>
                    <span class="badge ${user.credits_balance > 0 ? 'badge-success' : 'badge-warning'}">
                        ${user.credits_balance}
                    </span>
                </td>
                <td>${user.total_resumes}</td>
                <td>${createdDate}</td>
                <td>
                    <button class="btn btn-sm" onclick="viewUserDetails('${user.id}')" title="View Details">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-warning" onclick="modifyUserCredits('${user.id}')" title="Modify Credits">
                        <i class="fas fa-coins"></i>
                    </button>
                    ${!user.is_admin ? 
                        `<button class="btn btn-sm btn-success" onclick="toggleAdminStatus('${user.id}', true)" title="Make Admin">
                            <i class="fas fa-user-shield"></i>
                        </button>` :
                        `<button class="btn btn-sm btn-danger" onclick="toggleAdminStatus('${user.id}', false)" title="Remove Admin">
                            <i class="fas fa-user-minus"></i>
                        </button>`
                    }
                </td>
            </tr>
        `;
    }).join('');
}

function updateUsersPagination(pagination) {
    const container = document.getElementById('usersPagination');
    if (!container) return;
    
    let html = '';
    
    // Previous button
    html += `<button onclick="loadUsers(${pagination.page - 1})" ${!pagination.has_prev ? 'disabled' : ''}>
        <i class="fas fa-chevron-left"></i>
    </button>`;
    
    // Page numbers
    const startPage = Math.max(1, pagination.page - 2);
    const endPage = Math.min(pagination.pages, pagination.page + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        html += `<button onclick="loadUsers(${i})" ${i === pagination.page ? 'class="active"' : ''}>
            ${i}
        </button>`;
    }
    
    // Next button
    html += `<button onclick="loadUsers(${pagination.page + 1})" ${!pagination.has_next ? 'disabled' : ''}>
        <i class="fas fa-chevron-right"></i>
    </button>`;
    
    container.innerHTML = html;
}

// User action functions
async function viewUserDetails(userId) {
    try {
        const response = await fetch(`/api/v1/admin/users/${userId}`);
        if (!response.ok) throw new Error('Failed to load user details');
        
        const user = await response.json();
        showUserDetailsModal(user);
        
    } catch (error) {
        console.error('Error loading user details:', error);
        showToast('Failed to load user details', 'error');
    }
}

async function modifyUserCredits(userId) {
    const amount = prompt('Enter credit amount (positive to add, negative to remove):');
    if (!amount || isNaN(amount)) return;
    
    const description = prompt('Enter description (optional):') || 'Admin credit adjustment';
    
    try {
        const response = await fetch(`/api/v1/admin/users/${userId}/credits`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                amount: parseInt(amount),
                description: description
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to modify credits');
        }
        
        const result = await response.json();
        showToast(result.message, 'success');
        
        // Reload users to update the display
        await loadUsers();
        
    } catch (error) {
        console.error('Error modifying user credits:', error);
        showToast(error.message, 'error');
    }
}

async function toggleAdminStatus(userId, makeAdmin) {
    if (!confirm(`Are you sure you want to ${makeAdmin ? 'grant' : 'revoke'} admin privileges?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/v1/admin/users/${userId}/admin-status`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                make_admin: makeAdmin,
                role: makeAdmin ? 'admin' : undefined,
                access_level: makeAdmin ? 50 : undefined
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to update admin status');
        }
        
        const result = await response.json();
        showToast(result.message, 'success');
        
        // Reload users to update the display
        await loadUsers();
        
    } catch (error) {
        console.error('Error updating admin status:', error);
        showToast(error.message, 'error');
    }
}

// Utility functions
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function getStatusBadge(status) {
    const statusMap = {
        'success': 'badge-success',
        'completed': 'badge-success',
        'failed': 'badge-danger',
        'error': 'badge-danger',
        'pending': 'badge-warning',
        'processing': 'badge-warning',
        'info': 'badge-info'
    };
    
    const badgeClass = statusMap[status] || 'badge-info';
    return `<span class="badge ${badgeClass}">${status}</span>`;
}

function showLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div style="text-align: center; padding: 40px;">
                <div class="loading"></div> Loading...
            </div>
        `;
    }
}

function showLoadingTable(tableId) {
    const table = document.getElementById(tableId);
    if (table) {
        table.innerHTML = `
            <tr>
                <td colspan="10" style="text-align: center; padding: 40px;">
                    <div class="loading"></div> Loading...
                </td>
            </tr>
        `;
    }
}

function showError(containerId, message) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #dc3545;">
                <i class="fas fa-exclamation-triangle"></i> ${message}
            </div>
        `;
    }
}

function showTableError(tableId, message) {
    const table = document.getElementById(tableId);
    if (table) {
        table.innerHTML = `
            <tr>
                <td colspan="10" style="text-align: center; padding: 40px; color: #dc3545;">
                    <i class="fas fa-exclamation-triangle"></i> ${message}
                </td>
            </tr>
        `;
    }
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    if (!toast) return;
    
    toast.textContent = message;
    toast.className = `notification ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

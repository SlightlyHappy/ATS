// Admin Dashboard JavaScript - Part 3: User Details Modal and Additional Components

function showUserDetailsModal(user) {
    const modal = createModal('User Details', `
        <div class="user-details">
            <!-- User Basic Info -->
            <div class="user-info-section">
                <h3><i class="fas fa-user"></i> Basic Information</h3>
                <div class="info-grid">
                    <div class="info-item">
                        <label>Name:</label>
                        <span>${user.first_name} ${user.last_name}</span>
                    </div>
                    <div class="info-item">
                        <label>Email:</label>
                        <span>${user.email}</span>
                    </div>
                    <div class="info-item">
                        <label>Status:</label>
                        <span class="badge ${user.is_admin ? 'badge-info' : 'badge-success'}">
                            ${user.is_admin ? 'Admin' : 'User'}
                        </span>
                    </div>
                    <div class="info-item">
                        <label>Credits Balance:</label>
                        <span class="badge ${user.credits_balance > 0 ? 'badge-success' : 'badge-warning'}">
                            ${user.credits_balance}
                        </span>
                    </div>
                    <div class="info-item">
                        <label>Member Since:</label>
                        <span>${new Date(user.created_at).toLocaleDateString()}</span>
                    </div>
                    <div class="info-item">
                        <label>Last Login:</label>
                        <span>${user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}</span>
                    </div>
                </div>
            </div>
            
            <!-- Resume Statistics -->
            <div class="user-info-section">
                <h3><i class="fas fa-file-alt"></i> Resume Statistics</h3>
                <div class="stats-row">
                    <div class="stat-item">
                        <div class="stat-value">${user.resume_stats.total_resumes}</div>
                        <div class="stat-label">Total Resumes</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${user.resume_stats.recent_uploads}</div>
                        <div class="stat-label">Recent Uploads (30d)</div>
                    </div>
                </div>
            </div>
            
            <!-- Analysis Statistics -->
            <div class="user-info-section">
                <h3><i class="fas fa-chart-line"></i> Analysis Statistics</h3>
                <div class="stats-row">
                    <div class="stat-item">
                        <div class="stat-value">${user.analysis_stats.total_analyses}</div>
                        <div class="stat-label">Total Analyses</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${user.analysis_stats.completed_analyses}</div>
                        <div class="stat-label">Completed</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${user.analysis_stats.pending_analyses}</div>
                        <div class="stat-label">Pending</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${user.analysis_stats.processing_analyses}</div>
                        <div class="stat-label">Processing</div>
                    </div>
                </div>
            </div>
            
            <!-- Credit Transactions -->
            ${user.recent_transactions && user.recent_transactions.length > 0 ? `
                <div class="user-info-section">
                    <h3><i class="fas fa-coins"></i> Recent Credit Transactions</h3>
                    <div class="transactions-table">
                        <table style="width: 100%; font-size: 12px;">
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Type</th>
                                    <th>Amount</th>
                                    <th>Description</th>
                                    <th>Balance After</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${user.recent_transactions.map(transaction => `
                                    <tr>
                                        <td>${new Date(transaction.created_at).toLocaleDateString()}</td>
                                        <td>
                                            <span class="badge ${transaction.transaction_type === 'credit' ? 'badge-success' : 'badge-warning'}">
                                                ${transaction.transaction_type}
                                            </span>
                                        </td>
                                        <td>${transaction.transaction_type === 'credit' ? '+' : '-'}${transaction.amount}</td>
                                        <td>${transaction.description}</td>
                                        <td>${transaction.balance_after}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            ` : ''}
            
            <!-- Admin Profile (if applicable) -->
            ${user.admin_profile ? `
                <div class="user-info-section">
                    <h3><i class="fas fa-shield-alt"></i> Admin Profile</h3>
                    <div class="info-grid">
                        <div class="info-item">
                            <label>Role:</label>
                            <span class="badge badge-info">${user.admin_profile.role}</span>
                        </div>
                        <div class="info-item">
                            <label>Access Level:</label>
                            <span>${user.admin_profile.access_level}/100</span>
                        </div>
                        <div class="info-item">
                            <label>Status:</label>
                            <span class="badge ${user.admin_profile.is_active ? 'badge-success' : 'badge-danger'}">
                                ${user.admin_profile.is_active ? 'Active' : 'Inactive'}
                            </span>
                        </div>
                        <div class="info-item">
                            <label>Login Count:</label>
                            <span>${user.admin_profile.login_count}</span>
                        </div>
                        <div class="info-item">
                            <label>Actions Performed:</label>
                            <span>${user.admin_profile.actions_performed}</span>
                        </div>
                        <div class="info-item">
                            <label>Failed Login Attempts:</label>
                            <span class="badge ${user.admin_profile.failed_login_attempts > 0 ? 'badge-warning' : 'badge-success'}">
                                ${user.admin_profile.failed_login_attempts}
                            </span>
                        </div>
                    </div>
                </div>
            ` : ''}
            
            <!-- Action Buttons -->
            <div class="user-actions">
                <button class="btn btn-warning" onclick="modifyUserCredits('${user.id}'); closeModal();">
                    <i class="fas fa-coins"></i> Modify Credits
                </button>
                ${!user.is_admin ? 
                    `<button class="btn btn-success" onclick="toggleAdminStatus('${user.id}', true); closeModal();">
                        <i class="fas fa-user-shield"></i> Make Admin
                    </button>` :
                    `<button class="btn btn-danger" onclick="toggleAdminStatus('${user.id}', false); closeModal();">
                        <i class="fas fa-user-minus"></i> Remove Admin
                    </button>`
                }
                <button class="btn btn-secondary" onclick="closeModal()">
                    <i class="fas fa-times"></i> Close
                </button>
            </div>
        </div>
        
        <style>
            .user-details {
                max-height: 70vh;
                overflow-y: auto;
            }
            
            .user-info-section {
                margin-bottom: 25px;
                padding-bottom: 20px;
                border-bottom: 1px solid #eee;
            }
            
            .user-info-section:last-of-type {
                border-bottom: none;
            }
            
            .user-info-section h3 {
                color: #667eea;
                margin-bottom: 15px;
                font-size: 16px;
            }
            
            .info-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
            }
            
            .info-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 8px 0;
            }
            
            .info-item label {
                font-weight: 500;
                color: #555;
            }
            
            .stats-row {
                display: flex;
                gap: 20px;
                justify-content: space-around;
            }
            
            .stat-item {
                text-align: center;
                flex: 1;
            }
            
            .stat-value {
                font-size: 24px;
                font-weight: bold;
                color: #667eea;
                margin-bottom: 5px;
            }
            
            .stat-label {
                font-size: 12px;
                color: #666;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            .transactions-table {
                max-height: 200px;
                overflow-y: auto;
                border: 1px solid #eee;
                border-radius: 4px;
            }
            
            .user-actions {
                margin-top: 20px;
                padding-top: 20px;
                border-top: 1px solid #eee;
                display: flex;
                gap: 10px;
                justify-content: flex-end;
            }
            
            @media (max-width: 768px) {
                .info-grid {
                    grid-template-columns: 1fr;
                }
                
                .stats-row {
                    flex-direction: column;
                    gap: 10px;
                }
                
                .user-actions {
                    flex-direction: column;
                }
            }
        </style>
    `);
}

// Additional utility functions for the admin dashboard

function updateDashboardStats(data) {
    // Real-time update function for WebSocket data
    if (data && data.queue) {
        const pendingElement = document.querySelector('[data-stat="pending"]');
        const processingElement = document.querySelector('[data-stat="processing"]');
        const completedElement = document.querySelector('[data-stat="completed"]');
        
        if (pendingElement) pendingElement.textContent = data.queue.pending || 0;
        if (processingElement) processingElement.textContent = data.queue.processing || 0;
        if (completedElement) completedElement.textContent = data.queue.completed_today || 0;
    }
}

async function exportAuditLog() {
    try {
        const response = await fetch('/api/v1/admin/audit-log?per_page=1000&export=csv');
        if (!response.ok) throw new Error('Failed to export audit log');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `audit-log-${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showToast('Audit log exported successfully', 'success');
        
    } catch (error) {
        console.error('Error exporting audit log:', error);
        showToast('Failed to export audit log', 'error');
    }
}

function toggleTheme() {
    // Add dark mode toggle functionality
    const body = document.body;
    body.classList.toggle('dark-theme');
    
    const isDark = body.classList.contains('dark-theme');
    localStorage.setItem('admin-theme', isDark ? 'dark' : 'light');
    
    showToast(`Switched to ${isDark ? 'dark' : 'light'} theme`, 'info');
}

function initializeTheme() {
    const savedTheme = localStorage.getItem('admin-theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
    }
}

// Advanced search functionality
function setupAdvancedSearch() {
    const searchForm = document.getElementById('advancedSearchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const searchParams = {
                search: formData.get('search'),
                is_admin: formData.get('is_admin'),
                has_credits: formData.get('has_credits'),
                created_after: formData.get('created_after'),
                created_before: formData.get('created_before')
            };
            
            // Filter out empty values
            Object.keys(searchParams).forEach(key => {
                if (!searchParams[key]) delete searchParams[key];
            });
            
            await loadUsers(1, searchParams);
            closeModal();
        });
    }
}

// Bulk operations
async function bulkUserOperation(operation, userIds) {
    if (!confirm(`Are you sure you want to ${operation} ${userIds.length} users?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/v1/admin/users/bulk', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                operation: operation,
                user_ids: userIds
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Bulk operation failed');
        }
        
        const result = await response.json();
        showToast(result.message, 'success');
        
        await loadUsers();
        
    } catch (error) {
        console.error('Error performing bulk operation:', error);
        showToast(error.message, 'error');
    }
}

// Real-time dashboard updates
function startRealTimeUpdates() {
    if (socket) {
        socket.emit('subscribe_admin_updates');
        
        socket.on('user_created', (data) => {
            showToast(`New user registered: ${data.email}`, 'info');
            updateUserCount(1);
        });
        
        socket.on('analysis_completed', (data) => {
            updateAnalysisCount(1);
        });
        
        socket.on('system_alert', (data) => {
            showToast(data.message, data.level || 'warning');
        });
    }
}

function updateUserCount(increment) {
    const userCountElement = document.querySelector('[data-stat="total_users"] .value');
    if (userCountElement) {
        const currentCount = parseInt(userCountElement.textContent) || 0;
        userCountElement.textContent = currentCount + increment;
    }
}

function updateAnalysisCount(increment) {
    const analysisCountElement = document.querySelector('[data-stat="completed_analyses"] .value');
    if (analysisCountElement) {
        const currentCount = parseInt(analysisCountElement.textContent) || 0;
        analysisCountElement.textContent = currentCount + increment;
    }
}

// Initialize additional features when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeTheme();
    setupAdvancedSearch();
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // ESC to close modal
        if (e.key === 'Escape') {
            closeModal();
        }
        
        // Ctrl+R to refresh current section
        if (e.ctrlKey && e.key === 'r') {
            e.preventDefault();
            loadSectionData(currentSection);
        }
    });
});

// Performance monitoring
function trackPerformance(operation) {
    const start = performance.now();
    
    return {
        end: () => {
            const duration = performance.now() - start;
            console.log(`${operation} took ${duration.toFixed(2)}ms`);
            
            if (duration > 1000) {
                console.warn(`Slow operation detected: ${operation} (${duration.toFixed(2)}ms)`);
            }
        }
    };
}

// Error recovery
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    showToast('An unexpected error occurred. Please refresh the page.', 'error');
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
    showToast('A network error occurred. Please check your connection.', 'error');
});

// Dashboard JavaScript for Certificate Manager

// Global variables
let statsChart, activityChart, statusChart;
let autoRefreshInterval;
let isRefreshing = false;

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    setupEventListeners();
    startAutoRefresh();
});

// Initialize dashboard functionality
function initializeDashboard() {
    console.log('Initializing dashboard...');
    
    // Initialize tooltips
    initializeTooltips();
    
    // Setup real-time updates
    setupRealTimeUpdates();
    
    // Initialize any modals
    initializeModals();
}

// Setup event listeners
function setupEventListeners() {
    // Refresh button
    const refreshBtn = document.querySelector('[onclick="refreshStats()"]');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function(e) {
            e.preventDefault();
            refreshStats();
        });
    }
    
    // Auto-refresh toggle
    const autoRefreshToggle = document.getElementById('autoRefreshToggle');
    if (autoRefreshToggle) {
        autoRefreshToggle.addEventListener('change', function() {
            if (this.checked) {
                startAutoRefresh();
            } else {
                stopAutoRefresh();
            }
        });
    }
    
    // Search functionality
    const searchInput = document.getElementById('dashboardSearch');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(handleSearch, 300));
    }
}

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize modals
function initializeModals() {
    // Setup modal event listeners
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('show.bs.modal', function() {
            console.log('Modal opened:', this.id);
        });
        
        modal.addEventListener('hidden.bs.modal', function() {
            console.log('Modal closed:', this.id);
        });
    });
}

// Refresh statistics
async function refreshStats() {
    if (isRefreshing) {
        console.log('Already refreshing, skipping...');
        return;
    }
    
    isRefreshing = true;
    showRefreshIndicator(true);
    
    try {
        console.log('Refreshing dashboard statistics...');
        
        // Fetch updated statistics
        const response = await fetch('/api/stats', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const stats = await response.json();
        console.log('Updated stats:', stats);
        
        // Update statistics cards
        updateStatsCards(stats);
        
        // Update charts if they exist
        updateCharts(stats);
        
        // Show success message
        showNotification('Statistics updated successfully', 'success');
        
    } catch (error) {
        console.error('Error refreshing stats:', error);
        showNotification('Failed to refresh statistics', 'error');
    } finally {
        isRefreshing = false;
        showRefreshIndicator(false);
    }
}

// Update statistics cards
function updateStatsCards(stats) {
    const updates = [
        { id: 'total-students', value: stats.total_students },
        { id: 'pending-certs', value: stats.pending_certs },
        { id: 'sent-certs', value: stats.sent_certs },
        { id: 'failed-certs', value: stats.failed_certs },
        { id: 'verified-certs', value: stats.verified_certs },
        { id: 'success-rate', value: stats.success_rate + '%' }
    ];
    
    updates.forEach(update => {
        const element = document.getElementById(update.id);
        if (element) {
            // Animate the number change
            animateNumberChange(element, update.value);
        }
    });
}

// Animate number changes
function animateNumberChange(element, newValue) {
    const currentValue = parseInt(element.textContent) || 0;
    const targetValue = parseInt(newValue) || 0;
    
    if (currentValue === targetValue) return;
    
    const duration = 800; // milliseconds
    const steps = 20;
    const stepValue = (targetValue - currentValue) / steps;
    const stepDuration = duration / steps;
    
    let currentStep = 0;
    
    const interval = setInterval(() => {
        currentStep++;
        const value = Math.round(currentValue + (stepValue * currentStep));
        
        if (typeof newValue === 'string' && newValue.includes('%')) {
            element.textContent = value + '%';
        } else {
            element.textContent = value;
        }
        
        if (currentStep >= steps) {
            clearInterval(interval);
            element.textContent = newValue;
        }
    }, stepDuration);
}

// Update charts
function updateCharts(stats) {
    // Update status chart if it exists
    if (window.statusChart && window.statusChart.data) {
        window.statusChart.data.datasets[0].data = [
            stats.sent_certs,
            stats.pending_certs,
            stats.failed_certs,
            stats.verified_certs
        ];
        window.statusChart.update('active');
    }
    
    // Update activity chart with new data point if needed
    if (window.activityChart) {
        // This would typically involve fetching new time-series data
        console.log('Activity chart update would be implemented here');
    }
}

// Setup real-time updates
function setupRealTimeUpdates() {
    // In a real application, you might use WebSockets for real-time updates
    console.log('Real-time updates setup (WebSocket implementation would go here)');
}

// Start auto-refresh
function startAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    
    // Refresh every 30 seconds
    autoRefreshInterval = setInterval(() => {
        if (!document.hidden) { // Only refresh when tab is visible
            refreshStats();
        }
    }, 30000);
    
    console.log('Auto-refresh started');
}

// Stop auto-refresh
function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
    console.log('Auto-refresh stopped');
}

// Show refresh indicator
function showRefreshIndicator(show) {
    const indicators = document.querySelectorAll('.refresh-indicator');
    indicators.forEach(indicator => {
        if (show) {
            indicator.classList.add('d-inline-block');
            indicator.classList.remove('d-none');
        } else {
            indicator.classList.add('d-none');
            indicator.classList.remove('d-inline-block');
        }
    });
    
    // Update refresh button
    const refreshBtn = document.querySelector('[onclick="refreshStats()"]');
    if (refreshBtn) {
        const icon = refreshBtn.querySelector('i');
        if (icon) {
            if (show) {
                icon.classList.add('fa-spin');
            } else {
                icon.classList.remove('fa-spin');
            }
        }
        refreshBtn.disabled = show;
    }
}

// Show notification
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 1050; min-width: 300px;';
    
    notification.innerHTML = `
        <i class="fas fa-${getIconForType(type)} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Get icon for notification type
function getIconForType(type) {
    const icons = {
        success: 'check-circle',
        error: 'exclamation-triangle',
        warning: 'exclamation-circle',
        info: 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// Handle search functionality
function handleSearch(event) {
    const query = event.target.value.toLowerCase();
    console.log('Searching for:', query);
    
    // This would typically filter dashboard content
    // Implementation depends on what elements need to be searched
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export data functionality
function exportData(type = 'csv') {
    console.log('Exporting data as:', type);
    
    // This would implement data export functionality
    showNotification('Export functionality would be implemented here', 'info');
}

// Bulk operations
function bulkResendFailed() {
    if (confirm('This will resend certificates to all students with failed status. Continue?')) {
        console.log('Bulk resend initiated');
        showNotification('Bulk resend started. This may take a few minutes.', 'info');
        
        // Implementation would go here
    }
}

// Print functionality
function printDashboard() {
    window.print();
}

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        console.log('Page hidden - pausing auto-refresh');
    } else {
        console.log('Page visible - resuming auto-refresh');
        // Refresh immediately when page becomes visible
        if (autoRefreshInterval) {
            refreshStats();
        }
    }
});

// Handle window beforeunload
window.addEventListener('beforeunload', function() {
    stopAutoRefresh();
});

// Utility functions for chart management
function createChart(ctx, config) {
    return new Chart(ctx, config);
}

function updateChartData(chart, newData) {
    if (chart && chart.data) {
        chart.data = newData;
        chart.update();
    }
}

function destroyChart(chart) {
    if (chart) {
        chart.destroy();
    }
}

// Performance monitoring
function measurePerformance(name, fn) {
    const start = performance.now();
    const result = fn();
    const end = performance.now();
    console.log(`${name} took ${end - start} milliseconds`);
    return result;
}

// Error handling
window.addEventListener('error', function(event) {
    console.error('Dashboard error:', event.error);
    showNotification('An error occurred. Please refresh the page.', 'error');
});

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Ctrl/Cmd + R for refresh
    if ((event.ctrlKey || event.metaKey) && event.key === 'r') {
        event.preventDefault();
        refreshStats();
    }
    
    // Escape to close modals
    if (event.key === 'Escape') {
        const openModals = document.querySelectorAll('.modal.show');
        openModals.forEach(modal => {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                modalInstance.hide();
            }
        });
    }
});

// Console log for debugging
console.log('Dashboard JavaScript loaded successfully');

// Function to load execution logs from backend
async function loadLogs() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/login.html';
        return;
    }
    
    const container = document.getElementById('logsContainer');
    if (!container) return; // Container doesn't exist on this page
    
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/logs/`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const logs = await response.json();
            renderLogs(logs);
        } else if (response.status === 401) {
            // Token expired or invalid
            localStorage.removeItem('access_token');
            window.location.href = '/login.html';
        } else {
            throw new Error('Failed to load logs');
        }
    } catch (error) {
        console.error('Error loading logs:', error);
        container.innerHTML = `
            <div class="text-center" style="padding: var(--spacing-lg);">
                <i class="fas fa-exclamation-triangle" style="font-size: 2rem; color: var(--danger);"></i>
                <p class="mt-md">Failed to load execution logs. Please try again.</p>
                <button class="btn btn-outline btn-sm" onclick="loadLogs()">
                    <i class="fas fa-sync"></i> Retry
                </button>
            </div>
        `;
    }
}

// Function to render logs in the container
function renderLogs(logs) {
    const container = document.getElementById('logsContainer');
    if (!container) return;
    
    if (logs.length === 0) {
        container.innerHTML = `
            <tr>
                <td colspan="4" class="text-center" style="padding: var(--spacing-lg);">
                    <i class="fas fa-history" style="font-size: 2rem; color: var(--gray-400);"></i>
                    <p class="mt-md">No execution logs yet.</p>
                </td>
            </tr>
        `;
        return;
    }
    
    // Sort logs by ID (newest first)
    logs.sort((a, b) => b.id - a.id);
    
    container.innerHTML = logs.map(log => {
        const statusClass = log.status === 'success' ? 'log-success' : 
                           log.status === 'error' ? 'log-error' : 'log-warning';
        const statusIcon = log.status === 'success' ? 'check-circle' : 
                          log.status === 'error' ? 'exclamation-triangle' : 'exclamation-circle';
        
        return `
            <tr>
                <td>
                    <span class="${statusClass}">
                        <i class="fas fa-${statusIcon}"></i> ${log.status.charAt(0).toUpperCase() + log.status.slice(1)}
                    </span>
                </td>
                <td>Workflow #${log.workflow_id}</td>
                <td>${log.execution_time || 'N/A'}</td>
                <td>${log.details || 'No details provided'}</td>
            </tr>
        `;
    }).join('');
}

// Load logs when page loads (if logs container exists)
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('logsContainer')) {
        loadLogs();
    }
});

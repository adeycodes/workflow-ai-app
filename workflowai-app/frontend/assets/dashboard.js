// Load workflows and stats when page loads
document.addEventListener('DOMContentLoaded', async function() {
    // Check for access token in URL parameters (from Google OAuth callback)
    const urlParams = new URLSearchParams(window.location.search);
    const tokenFromUrl = urlParams.get('access_token');
    
    if (tokenFromUrl) {
        localStorage.setItem('access_token', tokenFromUrl);
        // Clean up the URL by removing the access_token
        window.history.replaceState({}, document.title, '/dashboard.html');
    }

    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/login.html';
        return;
    }
    
    loadWorkflows();
    loadStats();
});

// Load workflows from backend
async function loadWorkflows() {
    const token = localStorage.getItem('access_token');
    const container = document.getElementById('workflowsContainer');
    const alert = document.getElementById('alert');
    
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/workflows/`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const workflows = await response.json();
            renderWorkflows(workflows);
        } else if (response.status === 401) {
            // Token expired or invalid
            localStorage.removeItem('access_token');
            window.location.href = '/login.html';
        } else {
            throw new Error('Failed to load workflows');
        }
    } catch (error) {
        console.error('Error loading workflows:', error);
        container.innerHTML = `
            <div class="text-center" style="grid-column: 1 / -1; padding: var(--spacing-xl);">
                <i class="fas fa-exclamation-triangle" style="font-size: 2rem; color: var(--danger);"></i>
                <p class="mt-md">Failed to load workflows. Please try again.</p>
                <button class="btn btn-outline" onclick="loadWorkflows()">
                    <i class="fas fa-sync"></i> Retry
                </button>
            </div>
        `;
    }
}

// Render workflows in the container
function renderWorkflows(workflows) {
    const container = document.getElementById('workflowsContainer');
    
    if (workflows.length === 0) {
        container.innerHTML = `
            <div class="text-center" style="grid-column: 1 / -1; padding: var(--spacing-xl);">
                <i class="fas fa-project-diagram" style="font-size: 2rem; color: var(--gray-400);"></i>
                <p class="mt-md">No workflows yet. Create your first workflow to get started!</p>
                <a href="/builder.html" class="btn btn-primary mt-md">
                    <i class="fas fa-plus"></i> Create Workflow
                </a>
            </div>
        `;
        return;
    }
    
    container.innerHTML = workflows.map(workflow => `
        <div class="feature-card">
            <div class="d-flex justify-content-between align-items-start mb-md">
                <div>
                    <h3 class="mb-sm">${workflow.name}</h3>
                    <p class="mb-0" style="color: var(--gray-600); font-size: var(--text-sm);">
                        ${workflow.description || 'No description provided'}
                    </p>
                </div>
                <div class="status-badge ${workflow.is_active ? 'status-active' : 'status-inactive'}">
                    ${workflow.is_active ? 'Active' : 'Inactive'}
                </div>
            </div>
            
            <div class="d-flex justify-content-between align-items-center">
                <div class="workflow-meta">
                    <span style="color: var(--gray-500); font-size: var(--text-xs);">
                        <i class="fas fa-hashtag"></i> ID: ${workflow.id}
                    </span>
                    <span style="color: var(--gray-500); font-size: var(--text-xs);" class="ml-md">
                        <i class="fas fa-code"></i> n8n ID: ${workflow.n8n_workflow_id}
                    </span>
                </div>
                
                <div class="d-flex gap-sm">
                    <button class="btn btn-sm btn-outline" onclick="toggleWorkflow(${workflow.id}, ${workflow.is_active})">
                        <i class="fas fa-${workflow.is_active ? 'pause' : 'play'}"></i>
                    </button>
                    <a href="/builder.html?id=${workflow.id}" class="btn btn-sm btn-primary">
                        <i class="fas fa-edit"></i>
                    </a>
                    <button class="btn btn-sm btn-danger" onclick="deleteWorkflow(${workflow.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

// Toggle workflow active/inactive
async function toggleWorkflow(workflowId, currentlyActive) {
    const token = localStorage.getItem('access_token');
    const alert = document.getElementById('alert');
    
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/workflows/${workflowId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                is_active: !currentlyActive
            })
        });
        
        if (response.ok) {
            loadWorkflows(); // Reload workflows
            showAlert(`Workflow ${!currentlyActive ? 'activated' : 'paused'} successfully.`, 'success');
        } else if (response.status === 401) {
            // Token expired or invalid
            localStorage.removeItem('access_token');
            window.location.href = '/login.html';
        } else {
            throw new Error('Failed to toggle workflow');
        }
    } catch (error) {
        console.error('Error toggling workflow:', error);
        showAlert('Failed to toggle workflow. Please try again.', 'danger');
    }
}

// Delete workflow
async function deleteWorkflow(workflowId) {
    if (!confirm('Are you sure you want to delete this workflow? This action cannot be undone.')) {
        return;
    }
    
    const token = localStorage.getItem('access_token');
    const alert = document.getElementById('alert');
    
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/workflows/${workflowId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            loadWorkflows(); // Reload workflows
            showAlert('Workflow deleted successfully.', 'success');
        } else if (response.status === 401) {
            // Token expired or invalid
            localStorage.removeItem('access_token');
            window.location.href = '/login.html';
        } else {
            throw new Error('Failed to delete workflow');
        }
    } catch (error) {
        console.error('Error deleting workflow:', error);
        showAlert('Failed to delete workflow. Please try again.', 'danger');
    }
}

// Load stats from backend
async function loadStats() {
    const token = localStorage.getItem('access_token');
    
    try {
        // Fetch workflows to get stats
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/workflows/`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const workflows = await response.json();
            const totalWorkflows = workflows.length;
            const activeWorkflows = workflows.filter(w => w.is_active).length;
            
            // Update stats in the UI
            document.getElementById('totalWorkflows').textContent = totalWorkflows;
            document.getElementById('activeWorkflows').textContent = activeWorkflows;
            // For executions today, we would need to fetch logs and filter by date
            // This is a placeholder value for now
            document.getElementById('executionsToday').textContent = '0';
        }
    } catch (error) {
        console.error('Error loading stats:', error);
        // Keep default values of 0
    }
}

// Show alert
function showAlert(message, type) {
    const alert = document.getElementById('alert');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'}"></i> ${message}`;
    alert.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        alert.style.display = 'none';
    }, 5000);
}

// Logout functionality
document.getElementById('logoutBtn').addEventListener('click', function(e) {
    e.preventDefault();
    localStorage.removeItem('access_token');
    window.location.href = '/login.html';
});

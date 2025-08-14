// Configuration (replace with your actual API base URL)
const CONFIG = {
    API_BASE_URL: 'http://your-api-base-url' // e.g., 'http://localhost:8000'
};

// Check if user is authenticated via cookie
function isAuthenticated() {
    return document.cookie.split(';').some(function(cookie) {
        return cookie.trim().startsWith('access_token=');
    });
}

// Function to get token from cookie
function getAuthToken() {
    const cookie = document.cookie
        .split('; ')
        .find(row => row.startsWith('access_token='));
    return cookie ? cookie.split('=')[1].replace('Bearer ', '') : null;
}

// Function to load dashboard content
async function loadDashboardContent() {
    console.log('Loading dashboard content...');
    await loadWorkflows();
    await loadStats();
}

// Main initialization function
async function initializeDashboard() {
    console.log('=== Dashboard Loaded ===');
    console.log('Current URL:', window.location.href);
    console.log('Cookies:', document.cookie);

    // Check if we're already authenticated via access_token cookie
    if (isAuthenticated()) {
        console.log('User is authenticated via cookie');
        await loadDashboardContent();
        return;
    }

    // If not authenticated, check with the server
    await checkServerAuth();
}

// Check authentication with server
async function checkServerAuth() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('code')) {
        console.log('Detected OAuth callback with code parameter');
        // Exchange code for token
        const response = await fetch(`${CONFIG.API_BASE_URL}/auth/google/callback`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ code: urlParams.get('code') })
        });

        if (response.ok) {
            console.log('Token exchange successful:', await response.json());
            window.history.replaceState({}, document.title, window.location.pathname);
        } else {
            console.error('Token exchange failed:', await response.text());
            throw new Error('Token exchange failed');
        }
    }

    try {
        console.log('\n=== Checking Authentication ===');
        console.log('Making request to:', `${CONFIG.API_BASE_URL}/api/users/me`);

        const response = await fetch(`${CONFIG.API_BASE_URL}/api/users/me`, {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
        });

        console.log('\n=== Auth Response ===');
        console.log('Status:', response.status, response.statusText);
        console.log('Headers:', Object.fromEntries(response.headers.entries()));

        const contentType = response.headers.get('content-type');
        let responseData;

        if (contentType && contentType.includes('application/json')) {
            responseData = await response.json();
            console.log('Response data:', responseData);
        } else {
            responseData = await response.text();
            console.log('Non-JSON response:', responseData);
        }

        if (!response.ok) {
            console.error('Authentication failed:', {
                status: response.status,
                statusText: response.statusText,
                error: responseData
            });
            throw new Error('Authentication failed');
        }

        console.log('User authenticated:', responseData);
        await loadDashboardContent();
    } catch (error) {
        console.error('Authentication check failed:', error);
        sessionStorage.setItem('redirectAfterLogin', window.location.pathname);
        window.location.href = '/login.html';
    }
}

// Load workflows from backend
async function loadWorkflows() {
    const container = document.getElementById('workflowsContainer');

    try {
        const token = getAuthToken();
        const headers = {
            'Content-Type': 'application/json'
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${CONFIG.API_BASE_URL}/api/workflows/`, {
            credentials: 'include',
            headers: headers
        });

        if (response.ok) {
            const workflows = await response.json();
            renderWorkflows(workflows);
        } else if (response.status === 401) {
            console.log('401 received, attempting refresh...');
            const refreshResponse = await fetch(`${CONFIG.API_BASE_URL}/auth/refresh`, {
                credentials: 'include'
            });
            if (refreshResponse.ok) {
                console.log('Refresh successful, retrying workflows');
                await loadWorkflows(); // Retry after refresh
                return;
            }
            console.log('Refresh failed, redirecting to login:', await refreshResponse.text());
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

    if (!workflows || workflows.length === 0) {
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
                    <h3 class="mb-sm">${workflow.name || 'Unnamed Workflow'}</h3>
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
                        <i class="fas fa-hashtag"></i> ID: ${workflow.id || 'N/A'}
                    </span>
                    <span style="color: var(--gray-500); font-size: var(--text-xs);" class="ml-md">
                        <i class="fas fa-code"></i> n8n ID: ${workflow.n8n_workflow_id || 'N/A'}
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
    const alert = document.getElementById('alert');
    try {
        const token = getAuthToken();
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const response = await fetch(`${CONFIG.API_BASE_URL}/api/workflows/${workflowId}`, {
            method: 'PUT',
            credentials: 'include',
            headers: headers,
            body: JSON.stringify({ is_active: !currentlyActive })
        });

        if (response.ok) {
            await loadWorkflows();
            showAlert(`Workflow ${!currentlyActive ? 'activated' : 'paused'} successfully.`, 'success');
        } else if (response.status === 401) {
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
    if (!confirm('Are you sure you want to delete this workflow? This action cannot be undone.')) return;

    const alert = document.getElementById('alert');
    try {
        const token = getAuthToken();
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const response = await fetch(`${CONFIG.API_BASE_URL}/api/workflows/${workflowId}`, {
            method: 'DELETE',
            credentials: 'include',
            headers: headers
        });

        if (response.ok) {
            await loadWorkflows();
            showAlert('Workflow deleted successfully.', 'success');
        } else if (response.status === 401) {
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
    const statsContainer = document.getElementById('statsContainer');
    try {
        const token = getAuthToken();
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const response = await fetch(`${CONFIG.API_BASE_URL}/api/stats/`, {
            credentials: 'include',
            headers: headers
        });

        if (response.ok) {
            const workflows = await response.json();
            const totalWorkflows = workflows.length;
            const activeWorkflows = workflows.filter(w => w.is_active).length;
            document.getElementById('totalWorkflows').textContent = totalWorkflows;
            document.getElementById('activeWorkflows').textContent = activeWorkflows;
            document.getElementById('executionsToday').textContent = '0'; // Placeholder
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Show alert
function showAlert(message, type) {
    const alert = document.getElementById('alert');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'}"></i> ${message}`;
    alert.style.display = 'block';
    setTimeout(() => { alert.style.display = 'none'; }, 5000);
}

// Logout functionality
document.getElementById('logoutBtn').addEventListener('click', async function(e) {
    e.preventDefault();
    try {
        await fetch(`${CONFIG.API_BASE_URL}/auth/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        window.location.href = '/login.html';
    } catch (error) {
        console.error('Error during logout:', error);
    }
});

// Initialize on load
document.addEventListener('DOMContentLoaded', initializeDashboard);
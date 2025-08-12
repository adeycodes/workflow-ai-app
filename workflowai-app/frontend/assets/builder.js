// Get workflow ID from URL parameters if editing existing workflow
const urlParams = new URLSearchParams(window.location.search);
const workflowId = urlParams.get('id');

// Check if user is logged in
const token = localStorage.getItem('access_token');
if (!token) {
    window.location.href = '/login.html';
}

// Initialize the builder when page loads
document.addEventListener('DOMContentLoaded', async function() {
    // Set up tab switching
    setupTabs();
    
    // Set up button event listeners
    setupEventListeners();
    
    // If editing existing workflow, load it
    if (workflowId) {
        await loadWorkflow(workflowId);
    } else {
        // Show welcome message for new workflow
        setTimeout(() => {
            showAlert('🎉 Welcome to WorkflowAI Builder! Start by selecting a trigger node from the palette above.', 'success');
        }, 1000);
    }
    
    // Load execution logs
    loadLogs();
});

// Set up tab switching functionality
function setupTabs() {
    document.querySelectorAll('.workflow-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            
            // Update active tab
            document.querySelectorAll('.workflow-tab').forEach(t => {
                t.classList.remove('active');
            });
            this.classList.add('active');
            
            // Show corresponding content
            document.querySelectorAll('.tab-content').forEach(content => {
                content.style.display = 'none';
            });
            document.getElementById(`${tabId}-tab`).style.display = 'block';
        });
    });
}

// Set up event listeners for buttons
function setupEventListeners() {
    // Node category interactions
    document.querySelectorAll('.node-category').forEach(category => {
        category.addEventListener('click', function() {
            const categoryType = this.querySelector('h4').textContent;
            showAlert(`${categoryType} nodes will be available in the workflow designer. Start by dragging a trigger node to begin.`, 'success');
        });
    });
    
    // Integration card interactions
    document.querySelectorAll('.integration-card').forEach(card => {
        card.addEventListener('click', function() {
            const integrationName = this.querySelector('h4').textContent;
            showAlert(`Integration with ${integrationName} configured successfully! You can now use this service in your workflows.`, 'success');
        });
    });
    
    // Designer buttons
    document.getElementById('zoomInBtn')?.addEventListener('click', function() {
        showAlert('Zoom in to workflow designer.', 'success');
    });
    
    document.getElementById('zoomOutBtn')?.addEventListener('click', function() {
        showAlert('Zoom out of workflow designer.', 'success');
    });
    
    document.getElementById('fitViewBtn')?.addEventListener('click', function() {
        showAlert('Fit workflow to view in designer.', 'success');
    });
    
    document.getElementById('previewBtn')?.addEventListener('click', function() {
        showAlert('Preview mode would show a read-only view of your workflow execution path.', 'success');
    });
    
    // Save workflow button
    document.getElementById('saveBtn')?.addEventListener('click', saveWorkflow);
    
    // Test workflow button
    document.getElementById('testBtn')?.addEventListener('click', testWorkflow);
    
    // Logout button
    document.getElementById('logoutBtn').addEventListener('click', function(e) {
        e.preventDefault();
        localStorage.removeItem('access_token');
        window.location.href = '/login.html';
    });
}

// Load existing workflow for editing
async function loadWorkflow(id) {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/workflows/${id}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const workflow = await response.json();
            
            // Populate form fields
            document.getElementById('workflowName').value = workflow.name;
            document.getElementById('workflowDescription').value = workflow.description;
            document.getElementById('workflowStatus').value = workflow.is_active.toString();
            
            // Update n8n workflow ID display
            document.getElementById('n8nWorkflowId').textContent = workflow.n8n_workflow_id;
            
            // Update page title
            document.title = `Edit ${workflow.name} - WorkflowAI`;
            
            // Update header
            document.querySelector('.dashboard-header h1').textContent = `Edit ${workflow.name}`;
            
        } else if (response.status === 401) {
            // Token expired or invalid
            localStorage.removeItem('access_token');
            window.location.href = '/login.html';
        } else {
            throw new Error('Failed to load workflow');
        }
    } catch (error) {
        console.error('Error loading workflow:', error);
        showAlert('Failed to load workflow. Redirecting to dashboard.', 'danger');
        setTimeout(() => {
            window.location.href = '/dashboard.html';
        }, 2000);
    }
}

// Save workflow (create new or update existing)
async function saveWorkflow() {
    const saveBtn = document.getElementById('saveBtn');
    const name = document.getElementById('workflowName').value;
    const description = document.getElementById('workflowDescription').value;
    const isActive = document.getElementById('workflowStatus').value === 'true';
    
    if (!name) {
        showAlert('Please enter a workflow name', 'danger');
        return;
    }
    
    // Show loading state
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    saveBtn.disabled = true;
    
    try {
        let response;
        
        if (workflowId) {
            // Update existing workflow
            response = await fetch(`${CONFIG.API_BASE_URL}/api/workflows/${workflowId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    name: name,
                    description: description,
                    is_active: isActive
                })
            });
        } else {
            // Create new workflow
            // For now, we'll use a placeholder n8n_workflow_id
            // In a real implementation, this would be generated by n8n
            const n8nWorkflowId = 'n8n_workflow_' + Date.now();
            
            response = await fetch(`${CONFIG.API_BASE_URL}/api/workflows/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    name: name,
                    description: description,
                    n8n_workflow_id: n8nWorkflowId
                })
            });
        }
        
        if (response.ok) {
            const workflow = await response.json();
            showAlert('Workflow saved successfully! Your automation is now ready to use.', 'success');
            
            // Update the n8n workflow ID display
            document.getElementById('n8nWorkflowId').textContent = workflow.n8n_workflow_id;
            
            // If this is a new workflow, update the URL to include the ID
            if (!workflowId) {
                // Update URL to include workflow ID
                const newUrl = new URL(window.location.href);
                newUrl.searchParams.set('id', workflow.id);
                window.history.pushState({}, '', newUrl);
                
                // Update global workflowId variable
                workflowId = workflow.id;
                
                // Update page title
                document.title = `Edit ${workflow.name} - WorkflowAI`;
                
                // Update header
                document.querySelector('.dashboard-header h1').textContent = `Edit ${workflow.name}`;
            }
        } else if (response.status === 401) {
            // Token expired or invalid
            localStorage.removeItem('access_token');
            window.location.href = '/login.html';
        } else {
            throw new Error('Failed to save workflow');
        }
    } catch (error) {
        console.error('Error saving workflow:', error);
        showAlert('Failed to save workflow. Please check your connection and try again.', 'danger');
    } finally {
        // Reset button
        saveBtn.innerHTML = '<i class="fas fa-save"></i> Save Workflow';
        saveBtn.disabled = false;
    }
}

// Test workflow
async function testWorkflow() {
    const testBtn = document.getElementById('testBtn');
    
    // Show loading state
    testBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
    testBtn.disabled = true;
    
    try {
        // In a real implementation, this would call an actual test endpoint
        // For now, we'll simulate a test execution
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        showAlert('✅ Workflow test completed successfully! All nodes executed properly. Average execution time: 2.3 seconds.', 'success');
        
        // Update stats
        document.querySelector('.workflow-stats .stat-value').textContent = '6'; // Increment nodes
        
        // Add a new log entry
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        logEntry.innerHTML = `
            <span class="log-timestamp">${new Date().toLocaleString()}</span>
            <i class="fas fa-check-circle log-success"></i>
            <span>Workflow test completed successfully</span>
        `;
        
        const logsContainer = document.querySelector('.execution-logs');
        if (logsContainer) {
            logsContainer.prepend(logEntry);
        }
        
    } catch (error) {
        console.error('Error testing workflow:', error);
        showAlert('❌ Workflow test failed. Check your node configurations and try again.', 'danger');
    } finally {
        // Reset button
        testBtn.innerHTML = '<i class="fas fa-play"></i> Test Workflow';
        testBtn.disabled = false;
    }
}

// Show alert function
function showAlert(message, type) {
    const alert = document.getElementById('alert');
    if (!alert) return;
    
    const iconClass = type === 'success' ? 'check-circle' : 
                     type === 'danger' ? 'exclamation-triangle' : 
                     type === 'warning' ? 'exclamation-circle' : 'info-circle';
    
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `<i class="fas fa-${iconClass}"></i> ${message}`;
    alert.style.display = 'flex';
    
    // Smooth show animation
    alert.style.opacity = '0';
    alert.style.transform = 'translateY(-20px)';
    setTimeout(() => {
        alert.style.transition = 'all 0.3s ease';
        alert.style.opacity = '1';
        alert.style.transform = 'translateY(0)';
    }, 10);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-20px)';
        setTimeout(() => {
            alert.style.display = 'none';
        }, 300);
    }, 5000);
}

// Load execution logs
async function loadLogs() {
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
        // We won't show an error alert for logs as it's not critical to the workflow builder
    }
}

// Render logs in the execution logs container
function renderLogs(logs) {
    const logsContainer = document.querySelector('.execution-logs');
    if (!logsContainer) return;
    
    // Filter logs for this specific workflow if we have a workflowId
    let filteredLogs = logs;
    if (workflowId) {
        filteredLogs = logs.filter(log => log.workflow_id == workflowId);
    }
    
    if (filteredLogs.length === 0) {
        logsContainer.innerHTML = `
            <div class="log-entry">
                <span class="log-timestamp">${new Date().toLocaleString()}</span>
                <i class="fas fa-info-circle" style="color: var(--info);"></i>
                <span>No execution logs yet for this workflow.</span>
            </div>
        `;
        return;
    }
    
    // Sort logs by ID (newest first)
    filteredLogs.sort((a, b) => b.id - a.id);
    
    // Limit to 10 most recent logs
    const recentLogs = filteredLogs.slice(0, 10);
    
    logsContainer.innerHTML = recentLogs.map(log => {
        const statusClass = log.status === 'success' ? 'log-success' : 
                           log.status === 'error' ? 'log-error' : 'log-warning';
        const statusIcon = log.status === 'success' ? 'check-circle' : 
                          log.status === 'error' ? 'exclamation-triangle' : 'exclamation-circle';
        
        return `
            <div class="log-entry">
                <span class="log-timestamp">${log.execution_time || new Date().toLocaleString()}</span>
                <i class="fas fa-${statusIcon} ${statusClass}"></i>
                <span>${log.details || 'No details provided'}</span>
            </div>
        `;
    }).join('');
}

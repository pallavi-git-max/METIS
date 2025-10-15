// All Requests Page JavaScript

let currentPage = 1;
let currentFilters = {
    status: '',
    search: ''
};

// Load requests on page load
document.addEventListener('DOMContentLoaded', function() {
    loadAdminProfile().then(() => {
        loadRequests();
    });
});

function applyFilters() {
    currentFilters.status = document.getElementById('status-filter').value;
    currentFilters.search = document.getElementById('search-input').value;
    currentPage = 1;
    loadRequests();
}

async function loadRequests() {
    try {
        const params = new URLSearchParams();
        params.set('page', currentPage);
        params.set('per_page', '20');
        
        if (currentFilters.status) {
            params.set('status', currentFilters.status);
        }
        if (currentFilters.search) {
            params.set('search', currentFilters.search);
        }
        
        const response = await fetch(`/admin/requests/all?${params.toString()}`);
        const data = await response.json();
        
        if (data.success) {
            displayRequests(data.data.requests || []);
            displayPagination(data.data.pagination || {});
        } else {
            showToast(data.message || 'Failed to load requests');
        }
    } catch (error) {
        console.error('Error loading requests:', error);
        showToast('Failed to load requests');
    }
}

function displayRequests(requests) {
    const container = document.getElementById('requests-container');
    
    if (!requests || requests.length === 0) {
        container.innerHTML = `
            <div class="no-requests">
                <h3>No requests found</h3>
                <p>Try adjusting your filters or search criteria</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = requests.map(req => {
        const statusClass = req.status.replace('_', '-');
        const statusDisplay = req.status.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
        const submittedDate = new Date(req.submitted_at).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
        
        // Determine if close button should be shown
        const canClose = currentUserRole === 'admin' && req.status === 'approved';
        const isClosed = req.status === 'closed';
        
        const closedInfo = isClosed && req.closed_at ? `
            <div class="info-item">
                <span class="info-label">Closed:</span>
                <span class="info-value">${new Date(req.closed_at).toLocaleDateString()}</span>
            </div>
        ` : '';
        
        return `
            <div class="request-card status-${statusClass}">
                <div class="request-header">
                    <div>
                        <div class="request-title">${req.project_title}</div>
                        <div class="request-id">Request #${req.id} • ${req.user_name || 'Unknown User'}</div>
                    </div>
                    <div class="request-status ${statusClass}">${statusDisplay}</div>
                </div>
                
                <div class="request-info">
                    <div class="info-item">
                        <span class="info-label">Purpose:</span>
                        <span class="info-value">${req.purpose}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Submitted:</span>
                        <span class="info-value">${submittedDate}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Priority:</span>
                        <span class="info-value">${req.priority.toUpperCase()}</span>
                    </div>
                    ${closedInfo}
                </div>
                
                <div class="request-actions">
                    <button class="btn btn-view" onclick="viewRequestDetails(${req.id})">
                        👁️ View Details
                    </button>
                    ${canClose ? `
                        <button class="btn btn-close" onclick="closeRequest(${req.id})">
                            🔒 Close Request
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
    }).join('');
}

function displayPagination(pagination) {
    const container = document.getElementById('pagination');
    
    if (!pagination || pagination.total_pages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    const { current_page, total_pages } = pagination;
    let buttons = [];
    
    // Previous button
    buttons.push(`
        <button ${current_page === 1 ? 'disabled' : ''} onclick="changePage(${current_page - 1})">
            « Previous
        </button>
    `);
    
    // Page numbers
    for (let i = 1; i <= total_pages; i++) {
        if (i === 1 || i === total_pages || (i >= current_page - 2 && i <= current_page + 2)) {
            buttons.push(`
                <button class="${i === current_page ? 'active' : ''}" onclick="changePage(${i})">
                    ${i}
                </button>
            `);
        } else if (i === current_page - 3 || i === current_page + 3) {
            buttons.push('<button disabled>...</button>');
        }
    }
    
    // Next button
    buttons.push(`
        <button ${current_page === total_pages ? 'disabled' : ''} onclick="changePage(${current_page + 1})">
            Next »
        </button>
    `);
    
    container.innerHTML = buttons.join('');
}

function changePage(page) {
    currentPage = page;
    loadRequests();
    window.scrollTo(0, 0);
}

function viewRequestDetails(requestId) {
    window.location.href = `admin_workflow_dashboard.html?requestId=${requestId}`;
}

async function closeRequest(requestId) {
    if (currentUserRole !== 'admin') {
        showToast('Only administrators can close requests');
        return;
    }
    
    const confirmed = confirm(
        'Are you sure you want to close this request?\n\n' +
        'This marks the request as completed and closed. ' +
        'Closed requests indicate that the user has finished using the lab access.'
    );
    
    if (!confirmed) return;
    
    try {
        const response = await fetch(`/admin/requests/${requestId}/close`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Request closed successfully');
            loadRequests(); // Reload the list
        } else {
            showToast(data.message || 'Failed to close request');
        }
    } catch (error) {
        console.error('Error closing request:', error);
        showToast('Failed to close request');
    }
}

function showToast(message) {
    let toast = document.getElementById('toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast';
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 24px;
            background: rgba(30, 60, 114, 0.95);
            color: white;
            border-radius: 8px;
            font-weight: 600;
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;
        document.body.appendChild(toast);
    }
    
    toast.textContent = message;
    toast.style.display = 'block';
    toast.style.opacity = '1';
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => {
            toast.style.display = 'none';
        }, 300);
    }, 3000);
}

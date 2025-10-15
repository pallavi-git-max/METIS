// Admin Workflow Dashboard JavaScript
class WorkflowDashboard {
    constructor() {
        this.currentUser = null;
        this.currentRequest = null;
        this.refreshInterval = null;
        this.init();
    }

    async init() {
        await this.loadUserProfile();
        await this.loadDashboardData();
        this.setupEventListeners();
        this.startAutoRefresh();

        const params = new URLSearchParams(window.location.search);
        const reqId = params.get('requestId');
        if (reqId) {
            const role = (this.currentUser?.role || '').toLowerCase();
            this.viewRequest(parseInt(reqId, 10), role || 'admin');
        }
    }

    async loadUserProfile() {
        try {
            const response = await fetch('/admin/profile');
            if (response.ok) {
                const data = await response.json();
                this.currentUser = data?.admin || null;
                this.updateUserProfile();
            }
        } catch (error) {
            console.error('Error loading user profile:', error);
        }
    }

    updateUserProfile() {
        if (this.currentUser) {
            const fullName = this.currentUser.full_name || `${this.currentUser.first_name || ''} ${this.currentUser.last_name || ''}`.trim();
            const email = this.currentUser.email;
            const role = this.currentUser.designation || this.currentUser.role;
            const greetingEl = document.getElementById('admin-greeting');
            const nameEl = document.getElementById('admin-profile-dropdown-name');
            const emailEl = document.getElementById('admin-profile-dropdown-email');
            const roleEl = document.getElementById('admin-profile-dropdown-role');
            if (greetingEl) greetingEl.textContent = fullName || '';
            if (nameEl) nameEl.textContent = fullName || '';
            if (emailEl) emailEl.textContent = email || '';
            if (roleEl) roleEl.textContent = role || '';
        }
    }

    async loadDashboardData() {
        try {
            // Determine current user's role and only load that stage
            const role = (this.currentUser?.role || '').toLowerCase();
            let stages = [];
            if (role === 'project_guide') {
                stages = [{ role: 'project_guide', endpoint: '/approvals/guide/dashboard', container: 'guide-requests', count: 'guide-count' }];
                this.hideOtherStages(['guide-stage']);
            } else if (role === 'hod') {
                stages = [{ role: 'hod', endpoint: '/approvals/hod/dashboard', container: 'hod-requests', count: 'hod-count' }];
                this.hideOtherStages(['hod-stage']);
            } else if (role === 'it_services') {
                stages = [{ role: 'it_services', endpoint: '/approvals/it-services/dashboard', container: 'it-requests', count: 'it-count' }];
                this.hideOtherStages(['it-stage']);
            } else {
                // Fallback: admin sees final approvals only
                stages = [{ role: 'admin', endpoint: '/admin/requests?status=it_services_approved', container: 'final-requests', count: 'final-count' }];
                this.hideOtherStages(['final-stage']);
            }

            for (const stage of stages) {
                await this.loadStageData(stage);
            }

            // Update notification count for the visible stage only
            this.updateNotificationCount();
        } catch (error) {
            console.error('Error loading dashboard data:', error);
        }
    }

    hideOtherStages(visibleIds = []) {
        const ids = ['guide-stage', 'hod-stage', 'it-stage', 'final-stage'];
        ids.forEach(id => {
            const el = document.getElementById(id);
            if (!el) return;
            if (visibleIds.includes(id)) {
                el.style.display = '';
            } else {
                el.style.display = 'none';
            }
        });
    }

    async loadStageData(stage) {
        try {
            const response = await fetch(stage.endpoint);
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    // For the admin stage fallback, normalize shape
                    const pending = Array.isArray(data.data?.pending_requests)
                        ? data.data.pending_requests
                        : (Array.isArray(data.data?.requests) ? data.data.requests : []);

                    // Determine approved list key based on role
                    const approvedKeyMap = {
                        'project_guide': 'guide_approved',
                        'hod': 'hod_approved',
                        'it_services': 'it_services_approved',
                        'admin': null
                    };
                    const approvedKey = approvedKeyMap[stage.role] || null;
                    const approved = approvedKey && Array.isArray(data.data?.[approvedKey])
                        ? data.data[approvedKey]
                        : [];

                    this.renderStageRequests(stage.container, pending, stage.role, approved);
                    const countEl = document.getElementById(stage.count);
                    if (countEl) countEl.textContent = (pending || []).length;
                }
            }
        } catch (error) {
            console.error(`Error loading ${stage.role} data:`, error);
        }
    }

    renderStageRequests(containerId, requests, role, approvedRequests = []) {
        const container = document.getElementById(containerId);
        if (!container) return;
        const renderBlockPending = (list) => list.map(request => `
            <div class="request-item" data-request-id="${request.id}">
                <div class="request-title">${request.project_title}</div>
                <div class="request-meta">
                    <div><strong>Student:</strong> ${request.user_name}</div>
                    <div><strong>Submitted:</strong> ${new Date(request.submitted_at).toLocaleDateString()}</div>
                    <div><strong>Priority:</strong> <span class="priority-${request.priority}">${request.priority}</span></div>
                </div>
                <div class="request-actions">
                    <button class="btn-view" onclick="workflowDashboard.viewRequest(${request.id}, '${role}')">View Details</button>
                    <button class="btn-approve" onclick="workflowDashboard.approveRequest(${request.id}, '${role}')">Approve</button>
                    <button class="btn-reject" onclick="workflowDashboard.showRejectionForm(${request.id}, '${role}')">Reject</button>
                </div>
            </div>
        `).join('');
        const renderBlockApproved = (list) => list.map(request => `
            <div class="request-item" data-request-id="${request.id}">
                <div class="request-title">${request.project_title}</div>
                <div class="request-meta">
                    <div><strong>Student:</strong> ${request.user_name}</div>
                    <div><strong>Submitted:</strong> ${new Date(request.submitted_at).toLocaleDateString()}</div>
                    <div><strong>Priority:</strong> <span class="priority-${request.priority}">${request.priority}</span></div>
                </div>
                <div class="request-actions">
                    <button class="btn-view" onclick="workflowDashboard.viewRequest(${request.id}, '${role}')">View Details</button>
                </div>
            </div>
        `).join('');

        const hasPending = Array.isArray(requests) && requests.length > 0;
        const hasApproved = Array.isArray(approvedRequests) && approvedRequests.length > 0;
        if (!hasPending && !hasApproved) {
            container.innerHTML = '<div class="no-requests">No requests</div>';
            return;
        }

        let html = '';
        if (hasPending) {
            html += '<div class="stage-subtitle" style="font-weight:600;margin:8px 0;">Pending</div>';
            html += renderBlockPending(requests);
        } else {
            html += '<div class="no-requests">No pending requests</div>';
        }

        if (hasApproved) {
            html += '<div class="stage-subtitle" style="font-weight:600;margin:16px 0 8px;">Approved</div>';
            html += renderBlockApproved(approvedRequests);
        }

        container.innerHTML = html;
    }

    async viewRequest(requestId, role) {
        try {
            const response = await fetch(`/approvals/workflow/${requestId}`);
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    const req = data.data?.request || {};
                    const inferredRole = this.inferRoleFromStatus(req.status);
                    this.currentRequest = { id: requestId, role: role || inferredRole, status: req.status };
                    this.showRequestDetails(req, data.data?.workflow || []);
                }
            }
        } catch (error) {
            console.error('Error loading request details:', error);
        }
    }

    inferRoleFromStatus(status) {
        const map = {
            'pending': 'project_guide',
            'guide_approved': 'hod',
            'hod_approved': 'it_services',
            'it_services_approved': 'admin',
            'approved': 'admin',
            'rejected': 'admin'
        };
        return map[(status || '').toLowerCase()] || 'project_guide';
    }

    showRequestDetails(request, workflow) {
        const modal = document.getElementById('requestModal');
        const detailsContainer = document.getElementById('requestDetails');
        if (!modal || !detailsContainer) return;

        detailsContainer.innerHTML = `
            <div class="detail-row">
                <div class="detail-label">Project Title:</div>
                <div class="detail-value">${request.project_title || ''}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Student:</div>
                <div class="detail-value">${request.user_name || ''}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Description:</div>
                <div class="detail-value" style="white-space: pre-wrap; background: #f8f9fa; padding: 12px; border-radius: 6px; border-left: 4px solid #1e3c72;">${request.description || ''}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Purpose:</div>
                <div class="detail-value">${request.purpose || ''}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Expected Duration:</div>
                <div class="detail-value">${request.expected_duration || 'Not specified'}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Priority:</div>
                <div class="detail-value">${request.priority || ''}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Current Status:</div>
                <div class="detail-value">${request.status || ''}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Submitted:</div>
                <div class="detail-value">${request.submitted_at ? new Date(request.submitted_at).toLocaleString() : ''}</div>
            </div>
            ${request.rejection_reason ? `
            <div class="detail-row">
                <div class="detail-label">Rejection Reason:</div>
                <div class="detail-value" style="color: #dc3545;">${request.rejection_reason}</div>
            </div>
            ` : ''}
        `;

        this.updateWorkflowProgress(workflow || []);
        // Hide approve/reject buttons for view-only modal; show Close only
        const approveBtn = modal.querySelector('.btn-approve');
        if (approveBtn) approveBtn.style.display = 'none';
        const rejectBtn = modal.querySelector('.btn-reject');
        if (rejectBtn) rejectBtn.style.display = 'none';
        const viewBtn = modal.querySelector('.btn-view');
        if (viewBtn) {
            viewBtn.style.display = '';
            viewBtn.textContent = 'Close';
        }
        modal.style.display = 'block';
    }

    updateWorkflowProgress(workflow) {
        const steps = ['submitted', 'guide_approval', 'hod_approval', 'it_services_approval', 'final_approval'];

        steps.forEach((step) => {
            const idMap = {
                submitted: 'step-submitted',
                guide_approval: 'step-guide',
                hod_approval: 'step-hod',
                it_services_approval: 'step-it',
                final_approval: 'step-final'
            };
            const stepElement = document.getElementById(idMap[step]);
            const workflowStep = (workflow || []).find(w => w.step === step);
            if (stepElement && workflowStep) {
                stepElement.className = `step-circle ${workflowStep.status}`;
            }
        });

        const progressLine = document.getElementById('progress-line');
        if (progressLine) {
            const completedSteps = (workflow || []).filter(w => w.status === 'completed').length;
            progressLine.className = completedSteps > 0 ? 'progress-line completed' : 'progress-line';
        }
    }

    async approveRequest(requestId, role) {
        try {
            const effectiveRole = role || this.currentRequest?.role || this.inferRoleFromStatus(this.currentRequest?.status);
            const endpoint = this.getApprovalEndpoint(effectiveRole);
            const response = await fetch(`${endpoint}/${requestId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            const data = await response.json().catch(()=>({success:false}));
            if (response.ok && data.success) {
                this.removeRequestFromUI(requestId);
                this.showNotification('Request approved successfully!', 'success');
                await this.loadDashboardData();
                this.closeModal();
                try { localStorage.setItem('dashboardRefresh', String(Date.now())); } catch (_) {}
            } else {
                this.showNotification((data && data.message) || 'Failed to approve request', 'error');
            }
        } catch (error) {
            console.error('Error approving request:', error);
            this.showNotification('Error approving request', 'error');
        }
    }

    async rejectRequest(requestId, role, reason) {
        try {
            const effectiveRole = role || this.currentRequest?.role || this.inferRoleFromStatus(this.currentRequest?.status);
            let url;
            if (effectiveRole === 'admin') {
                url = `/admin/requests/${requestId}/reject`;
            } else {
                const endpoint = this.getRejectionEndpoint(effectiveRole);
                url = `${endpoint}/${requestId}`;
            }
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ reason })
            });

            const data = await response.json().catch(()=>({success:false}));
            if (response.ok && data.success) {
                this.removeRequestFromUI(requestId);
                this.showNotification('Request rejected and moved to Rejected.', 'success');
                await this.loadDashboardData();
                this.closeModal();
                try { localStorage.setItem('dashboardRefresh', String(Date.now())); } catch (_) {}
                // Also refresh rejected requests in admin dashboard
                try { localStorage.setItem('refreshRejectedRequests', String(Date.now())); } catch (_) {}
                // Redirect to the Rejected Requests page with cache-busting
                try { window.location.href = 'admin_rejected_requests.html?ts=' + Date.now(); } catch (_) {}
            } else {
                this.showNotification((data && data.message) || 'Failed to reject request', 'error');
            }
        } catch (error) {
            console.error('Error rejecting request:', error);
            this.showNotification('Error rejecting request', 'error');
        }
    }

    getApprovalEndpoint(role) {
        const endpoints = {
            'project_guide': '/approvals/guide/approve',
            'hod': '/approvals/hod/approve',
            'it_services': '/approvals/it-services/approve',
            'admin': '/approvals/admin/final-approve'
        };
        return endpoints[role] || '/approvals/guide/approve';
    }

    getRejectionEndpoint(role) {
        const endpoints = {
            'project_guide': '/approvals/guide/reject',
            'hod': '/approvals/hod/reject',
            'it_services': '/approvals/it-services/reject'
        };
        return endpoints[role] || '/approvals/guide/reject';
    }

    showRejectionForm(requestId, role) {
        const form = document.getElementById('rejectionForm');
        if (form) {
            // Ensure the modal is visible
            const modal = document.getElementById('requestModal');
            if (modal) modal.style.display = 'block';

            // Show rejection form
            form.style.display = 'block';

            // Store the request ID and role for later use
            this.currentRequest = this.currentRequest || {};
            if (requestId) {
                this.currentRequest.id = requestId;
            }
            if (role) {
                this.currentRequest.role = role;
            }
            // If we don't have a role, try to infer it from current request status
            if (!this.currentRequest.role && this.currentRequest.status) {
                this.currentRequest.role = this.inferRoleFromStatus(this.currentRequest.status);
            }

            // If details are not populated yet, load minimal details
            const details = document.getElementById('requestDetails');
            if (details && !details.innerHTML.trim()) {
                fetch(`/approvals/workflow/${requestId}`)
                  .then(r=>r.json())
                  .then(({success,data})=>{
                    if(!success||!data) return;
                    const req = data.data?.request || {};
                    details.innerHTML = `
                        <div class="detail-row"><div class="detail-label">Project Title:</div><div class="detail-value">${req.project_title||''}</div></div>
                        <div class="detail-row"><div class="detail-label">Student:</div><div class="detail-value">${req.user_name||''}</div></div>
                        <div class="detail-row"><div class="detail-label">Status:</div><div class="detail-value">${(req.status||'').replace('_',' ').replace(/\b\w/g,c=>c.toUpperCase())}</div></div>
                    `;
                  }).catch(()=>{});
            }
        } else {
            // Fallback: if form missing, do nothing visible
        }
    }

    async submitRejection() {
        const reasonInput = document.getElementById('rejectionReason');
        const reason = reasonInput ? reasonInput.value : '';
        if (!reason.trim()) {
            this.showNotification('Please provide a rejection reason', 'error');
            return;
        }

        const role = this.currentRequest?.role || 'admin';
        const requestId = this.currentRequest?.id;
        
        console.log('Submitting rejection:', { requestId, role, reason, currentRequest: this.currentRequest });
        
        if (!requestId) {
            this.showNotification('No request ID found', 'error');
            return;
        }

        await this.rejectRequest(requestId, role, reason.trim());
        const form = document.getElementById('rejectionForm');
        if (form) form.style.display = 'none';
        if (reasonInput) reasonInput.value = '';
    }

    closeModal() {
        const modal = document.getElementById('requestModal');
        const form = document.getElementById('rejectionForm');
        const reasonInput = document.getElementById('rejectionReason');
        if (modal) modal.style.display = 'none';
        if (form) form.style.display = 'none';
        if (reasonInput) reasonInput.value = '';
    }

    setupEventListeners() {
        // Modal close events
        const closeBtn = document.querySelector('.close');
        if (closeBtn) closeBtn.addEventListener('click', () => this.closeModal());
        window.addEventListener('click', (event) => {
            const modal = document.getElementById('requestModal');
            if (event.target === modal) {
                this.closeModal();
            }
        });

        // Logout button
        const logoutBtn = document.querySelector('.logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                if (confirm('Are you sure you want to logout?')) {
                    fetch('/auth/logout', { method: 'POST' })
                        .then(() => { window.location.href = '/college-login-system.html'; })
                        .catch(() => { window.location.href = '/college-login-system.html'; });
                }
            });
        }
    }

    startAutoRefresh() {
        // Refresh data every 30 seconds
        this.refreshInterval = setInterval(() => {
            this.loadDashboardData();
        }, 30000);
    }

    updateNotificationCount() {
        // Calculate total pending requests across all stages
        const counts = ['guide-count', 'hod-count', 'it-count', 'final-count'];
        let totalPending = 0;

        counts.forEach(countId => {
            const el = document.getElementById(countId);
            const count = el ? parseInt(el.textContent) : 0;
            totalPending += isNaN(count) ? 0 : count;
        });

        const badge = document.getElementById('notification-count');
        if (badge) badge.textContent = totalPending;
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 5px;
            color: white;
            font-weight: bold;
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;

        // Set background color based on type
        const colors = {
            success: '#28a745',
            error: '#dc3545',
            info: '#17a2b8',
            warning: '#ffc107'
        };
        notification.style.backgroundColor = colors[type] || colors.info;

        document.body.appendChild(notification);

        // Remove notification after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    removeRequestFromUI(requestId) {
        const card = document.querySelector(`[data-request-id="${requestId}"]`);
        if (card && card.parentNode) card.parentNode.removeChild(card);
    }
}

// Global functions for onclick handlers
function approveRequest() {
    if (workflowDashboard.currentRequest) {
        workflowDashboard.approveRequest(workflowDashboard.currentRequest.id, workflowDashboard.currentRequest.role);
    }
}

function rejectRequest() {
    workflowDashboard.submitRejection();
}

function showRejectionForm() {
    if (workflowDashboard.currentRequest) {
        workflowDashboard.showRejectionForm(workflowDashboard.currentRequest.id, workflowDashboard.currentRequest.role);
    }
}

function closeModal() {
    workflowDashboard.closeModal();
}

// Initialize dashboard when page loads
let workflowDashboard;
document.addEventListener('DOMContentLoaded', () => {
    workflowDashboard = new WorkflowDashboard();
});

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    .priority-low { color: #28a745; }
    .priority-medium { color: #ffc107; }
    .priority-high { color: #fd7e14; }
    .priority-urgent { color: #dc3545; }
`;
document.head.appendChild(style);

// Guide Dashboard JavaScript

// Profile dropdown functionality
function toggleGuideProfileDropdown() {
    const dropdown = document.getElementById('guide-profile-dropdown');
    if (dropdown) {
        dropdown.classList.toggle('show');
    }
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const dropdown = document.getElementById('guide-profile-dropdown');
    const avatar = document.getElementById('guide-avatar');
    
    if (dropdown && avatar && !avatar.contains(event.target) && !dropdown.contains(event.target)) {
        dropdown.classList.remove('show');
    }
});

// Load guide profile data
function loadGuideProfile() {
    fetch('/admin/profile')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.admin) {
                const admin = data.admin;
                
                // Update welcome message
                const greeting = document.getElementById('guide-greeting');
                if (greeting) {
                    greeting.textContent = admin.first_name || 'Guide';
                }
                
                // Update profile dropdown
                const name = document.getElementById('guide-profile-dropdown-name');
                const email = document.getElementById('guide-profile-dropdown-email');
                const role = document.getElementById('guide-profile-dropdown-role');
                const userId = document.getElementById('guide-profile-dropdown-user-id');
                const phone = document.getElementById('guide-profile-dropdown-phone');
                
                if (name) name.textContent = admin.full_name || `${admin.first_name} ${admin.last_name}`;
                if (email) email.textContent = admin.email;
                if (role) role.textContent = admin.designation || 'Guide';
                if (userId) userId.textContent = admin.student_id || admin.email;
                if (phone) phone.textContent = admin.phone || 'Not provided';
            }
        })
        .catch(error => {
            console.error('Error loading guide profile:', error);
        });
}

// Load guide dashboard data
function loadGuideDashboard() {
    fetch('/approvals/guide/dashboard')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update stats
                const stats = data.data.stats;
                document.getElementById('stat-pending').textContent = stats.pending_count || 0;
                document.getElementById('stat-total-approved').textContent = stats.approved_count || 0;
                document.getElementById('pending-count').textContent = `${stats.pending_count || 0} Pending`;
                document.getElementById('pending-badge').textContent = stats.pending_count || 0;
                
                // Update pending requests list
                const pendingList = document.getElementById('pending-requests-list');
                if (pendingList) {
                    pendingList.innerHTML = '';
                    data.data.pending_requests.forEach(req => {
                        const div = document.createElement('div');
                        div.className = 'approval-item';
                        div.innerHTML = `
                            <div class="approval-item-header">
                                <div>
                                    <div class="approval-item-title">Req #${req.id} - ${req.user_name || ''}</div>
                                    <div class="approval-item-meta">Title: ${req.project_title}</div>
                                    <div class="approval-item-meta">Priority: ${req.priority}</div>
                                    <div class="approval-item-meta">Submitted: ${new Date(req.submitted_at).toLocaleDateString()}</div>
                                </div>
                            </div>
                            <div class="approval-actions">
                                <button class="btn btn-success" onclick="approveRequest(${req.id})">✓ Approve</button>
                                <button class="btn btn-danger" onclick="rejectRequest(${req.id})">✗ Reject</button>
                                <button class="btn btn-primary" onclick="viewRequestDetails(${req.id})">👁️ Details</button>
                            </div>
                        `;
                        pendingList.appendChild(div);
                    });
                }
                
                // Update recent approvals
                const recentApprovals = document.getElementById('recent-approvals');
                if (recentApprovals) {
                    recentApprovals.innerHTML = '';
                    data.data.guide_approved.slice(0, 5).forEach(req => {
                        const div = document.createElement('div');
                        div.className = 'user-item';
                        div.innerHTML = `
                            <div class="user-info">
                                <div class="user-avatar">${req.user_name ? req.user_name.charAt(0).toUpperCase() : 'U'}</div>
                                <div class="user-details">
                                    <div class="user-name">${req.user_name || 'Unknown User'}</div>
                                    <div class="user-role">${req.project_title}</div>
                                </div>
                            </div>
                        `;
                        recentApprovals.appendChild(div);
                    });
                }
            }
        })
        .catch(error => {
            console.error('Error loading guide dashboard:', error);
        });
}

// Approve a specific request
function approveRequest(requestId) {
    if (confirm('Are you sure you want to approve this request?')) {
        fetch(`/approvals/guide/approve/${requestId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Request approved successfully!');
                loadGuideDashboard(); // Reload dashboard
            } else {
                showToast('Failed to approve request: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error approving request:', error);
            showToast('Error approving request');
        });
    }
}

// Reject a specific request
function rejectRequest(requestId) {
    const reason = prompt('Please enter the reason for rejection:');
    if (reason && reason.trim()) {
        fetch(`/approvals/guide/reject/${requestId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reason: reason.trim() })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Request rejected successfully!');
                loadGuideDashboard(); // Reload dashboard
                // Signal admin dashboard to refresh rejected requests
                try { localStorage.setItem('refreshRejectedRequests', String(Date.now())); } catch (_) {}
            } else {
                showToast('Failed to reject request: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error rejecting request:', error);
            showToast('Error rejecting request');
        });
    }
}

// View request details
function viewRequestDetails(requestId) {
    // This could open a modal or navigate to a details page
    showToast('Opening request details...');
    // For now, just show a toast. You can implement a modal later.
}

// Approve selected request (for bulk actions)
function approveSelected() {
    const firstRequest = document.querySelector('#pending-requests-list .approval-item');
    if (firstRequest) {
        const approveBtn = firstRequest.querySelector('.btn-success');
        if (approveBtn) {
            approveBtn.click();
        }
    } else {
        showToast('No requests available for approval');
    }
}

// Reject selected request (for bulk actions)
function rejectSelected() {
    const firstRequest = document.querySelector('#pending-requests-list .approval-item');
    if (firstRequest) {
        const rejectBtn = firstRequest.querySelector('.btn-danger');
        if (rejectBtn) {
            rejectBtn.click();
        }
    } else {
        showToast('No requests available for rejection');
    }
}

// Logout function
function logout() {
    if(confirm('Are you sure you want to logout?')){
        fetch('/auth/logout',{method:'POST',headers:{'Content-Type':'application/json'}})
            .then(r=>r.json()).then(d=>{ window.location.href = d?.redirect_url || '/college-login-system.html'; })
            .catch(()=>{ window.location.href='/college-login-system.html'; });
    }
}

// Toast helper
function showToast(message){
  let el=document.getElementById('toast');
  if(!el){
    el=document.createElement('div');
    el.id='toast';
    el.style.position='fixed';
    el.style.top='20px';
    el.style.right='20px';
    el.style.padding='12px 16px';
    el.style.background='rgba(30,60,114,0.95)';
    el.style.color='#fff';
    el.style.borderRadius='8px';
    el.style.zIndex='9999';
    el.style.fontWeight='600';
    document.body.appendChild(el);
  }
  el.textContent=message;
  el.style.opacity='1';
  setTimeout(()=>{el.style.opacity='0';},2200);
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    loadGuideProfile();
    loadGuideDashboard();
    
    // Refresh dashboard every 30 seconds
    setInterval(loadGuideDashboard, 30000);
});

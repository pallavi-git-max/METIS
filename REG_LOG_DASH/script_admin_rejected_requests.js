// Admin Rejected Requests JavaScript

// Profile dropdown functionality
function toggleAdminProfileDropdown() {
    const dropdown = document.getElementById('admin-profile-dropdown');
    if (dropdown) {
        dropdown.classList.toggle('show');
    }
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const dropdown = document.getElementById('admin-profile-dropdown');
    const avatar = document.getElementById('admin-avatar');
    
    if (dropdown && avatar && !avatar.contains(event.target) && !dropdown.contains(event.target)) {
        dropdown.classList.remove('show');
    }
});

// Load admin profile data
function loadAdminProfile() {
    fetch('/admin/profile')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.admin) {
                const admin = data.admin;
                
                // Update welcome message
                const greeting = document.getElementById('admin-greeting');
                if (greeting) {
                    greeting.textContent = admin.first_name || 'Admin';
                }
                
                // Update profile dropdown
                const name = document.getElementById('admin-profile-dropdown-name');
                const email = document.getElementById('admin-profile-dropdown-email');
                const role = document.getElementById('admin-profile-dropdown-role');
                const userId = document.getElementById('admin-profile-dropdown-user-id');
                const phone = document.getElementById('admin-profile-dropdown-phone');
                
                if (name) name.textContent = admin.full_name || `${admin.first_name} ${admin.last_name}`;
                if (email) email.textContent = admin.email;
                if (role) role.textContent = admin.role || 'Administrator';
                if (userId) userId.textContent = admin.student_id || admin.email;
                if (phone) phone.textContent = admin.phone || 'Not provided';
            }
        })
        .catch(error => {
            console.error('Error loading admin profile:', error);
        });
}

// Load rejected requests data
function loadRejectedRequests() {
    fetch('/admin/requests/rejected?per_page=50')
        .then(response => response.json())
        .then(data => {
            if (data && data.success) {
                const requests = (data.data && Array.isArray(data.data.requests)) ? data.data.requests : [];
                updateRejectedRequestsList(requests);
                updateStats(requests);
            } else {
                showToast('Failed to load rejected requests');
            }
        })
        .catch(error => {
            console.error('Error loading rejected requests:', error);
            showToast('Error loading rejected requests');
        });
}

// Update rejected requests list
function updateRejectedRequestsList(requests) {
    const list = document.getElementById('rejected-requests-list');
    const count = document.getElementById('rejected-count');
    
    if (!list) return;
    
    if (count) count.textContent = `${requests.length} Rejected`;
    
    if (requests.length === 0) {
        list.innerHTML = '<div class="no-requests">No rejected requests found</div>';
        return;
    }
    
    list.innerHTML = requests.map(req => {
        const rejectedBy = req.rejected_by_name || 'Unknown';
        const rejectedAt = req.rejected_at ? new Date(req.rejected_at).toLocaleString() : 'Unknown';
        const reason = req.rejection_reason || req.rejection_comment || 'No reason provided';
        
        return `
            <div class="approval-item rejected-item">
                <div class="approval-item-header">
                    <div>
                        <div class="approval-item-title">Req #${req.id} - ${req.user_name || 'Unknown User'}</div>
                        <div class="approval-item-meta">Title: ${req.project_title}</div>
                        <div class="approval-item-meta">Priority: ${req.priority}</div>
                        <div class="approval-item-meta">Submitted: ${new Date(req.submitted_at).toLocaleDateString()}</div>
                        <div class="approval-item-meta rejected-info">
                            <strong>Rejected by:</strong> ${rejectedBy} on ${rejectedAt}
                        </div>
                        <div class="approval-item-meta rejected-reason">
                            <strong>Reason:</strong> ${reason}
                        </div>
                    </div>
                </div>
                <div class="approval-actions">
                    <button class="btn btn-primary" onclick="viewRequestDetails(${req.id})">👁️ View Details</button>
                    <button class="btn btn-success" onclick="restoreRequest(${req.id})">🔄 Restore</button>
                </div>
            </div>
        `;
    }).join('');
}

// Update statistics
function updateStats(requests) {
    const totalRejected = requests.length;
    const recentRejected = requests.filter(req => {
        const rejectedDate = new Date(req.rejected_at);
        const weekAgo = new Date();
        weekAgo.setDate(weekAgo.getDate() - 7);
        return rejectedDate >= weekAgo;
    }).length;
    
    const guideRejected = requests.filter(req => 
        req.rejected_by_name && req.rejected_by_name.toLowerCase().includes('guide')
    ).length;
    
    const hodRejected = requests.filter(req => 
        req.rejected_by_name && req.rejected_by_name.toLowerCase().includes('hod')
    ).length;
    
    // Update stat elements
    const statTotal = document.getElementById('stat-total-rejected');
    const statRecent = document.getElementById('stat-recent-rejected');
    const statGuide = document.getElementById('stat-guide-rejected');
    const statHod = document.getElementById('stat-hod-rejected');
    
    if (statTotal) statTotal.textContent = totalRejected;
    if (statRecent) statRecent.textContent = recentRejected;
    if (statGuide) statGuide.textContent = guideRejected;
    if (statHod) statHod.textContent = hodRejected;
}

// Apply filters
function applyFilters() {
    const dateFilter = document.getElementById('dateFilter').value;
    const searchInput = document.getElementById('searchInput').value.toLowerCase();
    
    // Build query parameters
    const params = new URLSearchParams();
    params.append('per_page', '50');
    
    // date range and search only
    if (dateFilter) params.append('date_range', dateFilter);
    if (searchInput) params.append('search', searchInput);
    
    fetch(`/admin/requests/rejected?${params.toString()}`)
        .then(response => response.json())
        .then(data => {
            if (data && data.success) {
                let requests = (data.data && Array.isArray(data.data.requests)) ? data.data.requests : [];
                
                // Client-side search if not handled by backend
                if (searchInput && !params.has('search')) {
                    requests = requests.filter(req => 
                        req.project_title.toLowerCase().includes(searchInput) ||
                        (req.user_name && req.user_name.toLowerCase().includes(searchInput))
                    );
                }
                
                updateRejectedRequestsList(requests);
            }
        })
        .catch(error => {
            console.error('Error applying filters:', error);
        });
}

// Reset filters
function resetFilters() {
    document.getElementById('statusFilter').value = '';
    document.getElementById('dateFilter').value = '';
    document.getElementById('searchInput').value = '';
    loadRejectedRequests();
}

// View request details
function viewRequestDetails(requestId) {
    // Navigate to workflow dashboard with request ID
    window.location.href = `admin_workflow_dashboard.html?requestId=${requestId}`;
}

// Restore request (admin only action)
function restoreRequest(requestId) {
    if (confirm('Are you sure you want to restore this request? This will change its status back to pending.')) {
        fetch(`/admin/requests/${requestId}/restore`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Request restored successfully!');
                loadRejectedRequests(); // Reload the list
            } else {
                showToast('Failed to restore request: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error restoring request:', error);
            showToast('Error restoring request');
        });
    }
}

// Export rejected requests
function exportRejectedRequests() {
    window.location.href = '/admin/export/requests?format=csv&status=rejected';
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

// Initialize page when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    loadAdminProfile();
    loadRejectedRequests();
    
    // Refresh data every 30 seconds
    setInterval(loadRejectedRequests, 30000);
});

 // Admin User Management - fetch real data
let currentPage = 1;
let currentPerPage = 10;
let lastUsersResponse = null;
let currentAdminId = null;
let currentAdminRole = null;

async function fetchAdminProfile() {
  try {
    const res = await fetch('/admin/profile');
    if (!res.ok) return;
    const json = await res.json();
    if (json.success && json.admin) {
      currentAdminId = json.admin.id;
      currentAdminRole = json.admin.role;
    }
  } catch (e) {
    console.error('Failed to fetch admin profile', e);
  }
}

async function fetchDashboardStats() {
  try {
    const res = await fetch('/admin/dashboard');
    if (!res.ok) return;
    const json = await res.json();
    if (!json.success) return;
    const s = json.data.stats || {};
    const el = (id)=>document.getElementById(id);
    if (el('stat-total-users')) el('stat-total-users').textContent = s.total_users ?? 0;
    if (el('stat-active-users')) el('stat-active-users').textContent = s.active_users ?? 0;
    if (el('stat-students')) el('stat-students').textContent = s.students_count ?? 0;
    if (el('stat-faculty-external')) el('stat-faculty-external').textContent = s.faculty_external_count ?? 0;
  } catch (e) {
    console.error('Failed to fetch dashboard stats', e);
  }
}

function buildUsersQuery() {
  const params = new URLSearchParams();
  params.set('page', String(currentPage));
  params.set('per_page', String(currentPerPage));
  const role = document.getElementById('userTypeFilter')?.value;
  if (role) params.set('role', role);
  return `/admin/users?${params.toString()}`;
}

async function fetchUsers() {
  try {
    const res = await fetch(buildUsersQuery());
    if (!res.ok) throw new Error('Failed to load users');
    const json = await res.json();
    if (!json.success) throw new Error(json.message || 'Failed to load users');
    lastUsersResponse = json.data;
    renderUsersTable(json.data.users || []);
    renderPagination(json.data.pagination || null);
  } catch (e) {
    console.error(e);
    const tbody = document.getElementById('usersTableBody');
    if (tbody) tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#c00">Error loading users</td></tr>';
  }
}

function renderUsersTable(users) {
  const tbody = document.getElementById('usersTableBody');
  if (!tbody) return;
  if (!users || users.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#666">No users found</td></tr>';
    return;
  }
  tbody.innerHTML = users.map(u => {
    const initials = (u.first_name?.[0] || '?') + (u.last_name?.[0] || '');
    const roleClass = `role-${u.role}`;
    const statusClass = u.is_active ? 'status-active' : 'status-inactive';
    const deptLabel = u.department ? u.department.replace(/_/g,' ').replace(/\b\w/g, c=>c.toUpperCase()) : 'N/A';
    const lastActive = u.last_login ? new Date(u.last_login).toLocaleString() : '—';
    const userId = u.student_id || `USR${u.id}`;
    const roleLabel = u.role.replace(/_/g,' ').replace(/\b\w/g, c=>c.toUpperCase());
    
    // Check if this is the current admin user
    let actionBtn;
    if (currentAdminId && u.id === currentAdminId) {
      actionBtn = `<span class="user-self-badge" title="This is your account">👤 You</span>`;
    } else if (currentAdminRole === 'admin') {
      // Only admins can activate/deactivate users
      actionBtn = u.is_active 
        ? `<button class="action-btn btn-deactivate" onclick="toggleUserStatus(${u.id}, false)" title="Deactivate User">🚫 Deactivate</button>`
        : `<button class="action-btn btn-activate" onclick="toggleUserStatus(${u.id}, true)" title="Activate User">✅ Activate</button>`;
    } else {
      // Non-admin users just see the status
      actionBtn = u.is_active 
        ? `<span class="user-status-badge status-active">Active</span>`
        : `<span class="user-status-badge status-inactive">Inactive</span>`;
    }
    return `
      <tr>
        <td>
          <div class="user-info-cell">
            <div class="user-avatar">${initials}</div>
            <div class="user-details">
              <div class="user-name">${u.full_name}</div>
              <div class="user-email">${u.email}</div>
            </div>
          </div>
        </td>
        <td>${userId}</td>
        <td><span class="role-badge ${roleClass}">${roleLabel}</span></td>
        <td>${deptLabel}</td>
        <td><span class="status-badge ${statusClass}">${u.is_active ? 'Active' : 'Inactive'}</span></td>
        <td>${lastActive}</td>
        <td>${actionBtn}</td>
      </tr>`;
  }).join('');
}

function renderPagination(pg) {
  const info = document.querySelector('.pagination-info');
  const controls = document.querySelector('.pagination-controls');
  if (!pg || !info || !controls) return;
  const start = (pg.page - 1) * pg.per_page + 1;
  const end = Math.min(pg.page * pg.per_page, pg.total);
  info.textContent = `Showing ${start}-${end} of ${pg.total} users`;
  controls.innerHTML = '';
  const prev = document.createElement('button');
  prev.className = 'page-btn';
  prev.textContent = 'Previous';
  prev.disabled = !pg.has_prev;
  prev.onclick = () => { if (pg.has_prev) { currentPage -= 1; fetchUsers(); } };
  controls.appendChild(prev);
  for (let i = 1; i <= pg.pages; i++) {
    if (i === 1 || i === pg.pages || Math.abs(i - pg.page) <= 1) {
      const b = document.createElement('button');
      b.className = 'page-btn' + (i === pg.page ? ' active' : '');
      b.textContent = String(i);
      b.onclick = () => { currentPage = i; fetchUsers(); };
      controls.appendChild(b);
    } else if (i === 2 || i === pg.pages - 1) {
      const dots = document.createElement('button');
      dots.className = 'page-btn';
      dots.textContent = '...';
      dots.disabled = true;
      controls.appendChild(dots);
    }
  }
  const next = document.createElement('button');
  next.className = 'page-btn';
  next.textContent = 'Next';
  next.disabled = !pg.has_next;
  next.onclick = () => { if (pg.has_next) { currentPage += 1; fetchUsers(); } };
  controls.appendChild(next);
}

// Navigation function to redirect from admin dashboard
function navigateToUserManagement() {
  window.location.href = 'Admin_usr_manage.html';
}

// Filter functions
function applyFilters() {
  currentPage = 1;
  fetchUsers();
  fetchRejected();
}

function resetFilters() {
  const sel = document.getElementById('userTypeFilter');
  if (sel) sel.value = '';
  applyFilters();
}

// Custom Modal Functions
function showConfirmModal(title, message, onConfirm, isDanger = false) {
  const modal = document.getElementById('confirmModal');
  const modalTitle = document.getElementById('modalTitle');
  const modalMessage = document.getElementById('modalMessage');
  const confirmBtn = document.getElementById('modalConfirmBtn');
  
  modalTitle.textContent = title;
  modalMessage.textContent = message;
  
  // Reset classes
  confirmBtn.className = 'modal-btn modal-btn-confirm';
  
  // Add danger or success class
  if (isDanger) {
    confirmBtn.classList.add('danger');
  } else {
    confirmBtn.classList.add('success');
  }
  
  // Set up confirm button click handler
  confirmBtn.onclick = () => {
    closeConfirmModal();
    if (onConfirm) onConfirm();
  };
  
  // Show modal
  modal.classList.add('show');
}

function closeConfirmModal() {
  const modal = document.getElementById('confirmModal');
  modal.classList.remove('show');
}

function showToast(message, type = 'success') {
  const toast = document.getElementById('toastNotification');
  const toastIcon = document.getElementById('toastIcon');
  const toastMessage = document.getElementById('toastMessage');
  
  // Set icon based on type
  const icons = {
    success: '✅',
    error: '❌',
    info: 'ℹ️'
  };
  
  toastIcon.textContent = icons[type] || icons.info;
  toastMessage.textContent = message;
  
  // Reset classes
  toast.className = 'toast-notification';
  toast.classList.add(type, 'show');
  
  // Auto hide after 3 seconds
  setTimeout(() => {
    toast.classList.remove('show');
  }, 3000);
}

async function toggleUserStatus(userId, activate) {
  // Only admins can toggle user status
  if (currentAdminRole !== 'admin') {
    showToast('Only administrators can activate/deactivate users', 'error');
    return;
  }
  
  // Safety check: prevent deactivating own account
  if (currentAdminId && userId === currentAdminId && !activate) {
    showToast('Cannot deactivate your own account', 'error');
    return;
  }
  
  const action = activate ? 'activate' : 'deactivate';
  const title = activate ? 'Activate User Account' : 'Deactivate User Account';
  const message = activate 
    ? 'Are you sure you want to activate this user? They will be able to log in to the portal.'
    : 'Are you sure you want to deactivate this user? They will not be able to log in to the portal.';
  
  showConfirmModal(title, message, async () => {
    try {
      const res = await fetch(`/admin/users/${userId}/toggle-status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const json = await res.json();
      
      if (!res.ok || !json.success) {
        showToast(json.message || `Failed to ${action} user`, 'error');
        return;
      }
      
      // Show success message
      showToast(json.message || `User ${action}d successfully`, 'success');
      
      // Refresh the user list
      await fetchUsers();
      await fetchDashboardStats();
      
    } catch (e) {
      console.error(e);
      showToast(`Error: Failed to ${action} user`, 'error');
    }
  }, !activate); // isDanger = true for deactivate, false for activate
}

async function fetchRejected(){
  try{
    const res = await fetch('/admin/requests/rejected?per_page=10');
    if(!res.ok) return;
    const json = await res.json();
    if(!json.success) return;
    const wrap = document.getElementById('um-rejected-requests');
    if(!wrap) return;
    const items = json.data?.requests || [];
    wrap.innerHTML = '';
    if(items.length===0){ wrap.innerHTML = '<div class="no-requests">No rejected requests</div>'; return; }
    items.forEach(req=>{
      const div=document.createElement('div');
      div.className='user-item';
      const who = req.rejected_by_name || 'Unknown';
      const ts = req.rejected_at ? new Date(req.rejected_at).toLocaleString() : '';
      div.innerHTML = `<div class="user-info"><div class="user-avatar">✖</div><div class="user-details"><div class="user-name">Req #${req.id} - ${req.project_title}</div><div class="user-role">By ${who} • ${ts}</div><div class="user-role" style="color:#c33">${(req.rejection_reason||req.rejection_comment)||''}</div></div></div>`;
      wrap.appendChild(div);
    });
  }catch(_){}
}

// Logout helper
function logout(){
  if(!confirm('Are you sure you want to logout?')) return;
  fetch('/auth/logout',{method:'POST',headers:{'Content-Type':'application/json'}})
    .then(r=>r.json()).then(d=>{ window.location.href = d?.redirect_url || '/college-login-system.html'; })
    .catch(()=>{ window.location.href='/college-login-system.html'; });
}

// Initialize
document.addEventListener('DOMContentLoaded', async function() {
  await fetchAdminProfile();
  fetchDashboardStats();
  fetchUsers();
  fetchRejected();
  const searchInput = document.getElementById('searchInput');
  if (searchInput) {
    searchInput.addEventListener('input', function() {
      if (this.value.length > 2 || this.value.length === 0) {
        applyFilters();
      }
    });
  }
  const logoutLink = document.querySelector('.logout-btn');
  if (logoutLink) {
    logoutLink.addEventListener('click', function(e){
      e.preventDefault();
      logout();
    });
  }
  
  // Close modal when clicking outside
  const modal = document.getElementById('confirmModal');
  if (modal) {
    modal.addEventListener('click', function(e) {
      if (e.target === modal) {
        closeConfirmModal();
      }
    });
  }
});
        
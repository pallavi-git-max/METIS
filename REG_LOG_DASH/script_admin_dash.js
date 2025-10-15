// Basic active state for left menu; allow real navigation for real links
document.querySelectorAll('.menu-item').forEach((item)=>{
  item.addEventListener('click',function(e){
    const href = this.getAttribute('href');
    const isNavigable = href && href !== '#';
    // Toggle active state
    document.querySelectorAll('.menu-item').forEach(i=>i.classList.remove('active'));
    this.classList.add('active');
    // Only prevent default for non-navigable links
    if (!isNavigable) {
      e.preventDefault();
    }
  });
});

// Buttons actions
document.querySelectorAll('.btn').forEach((btn)=>{
  btn.addEventListener('click',function(){
    const action=this.textContent.trim();
    if(action.includes('Approve')) approveSelected();
    else if(action.includes('Reject')) rejectSelected();
    else if(action.includes('View Details')) showToast('Opening request details...');
    else if(action.includes('Export')) exportReport();
  });
});

      // Add click functionality to action buttons
      document.querySelectorAll(".action-btn").forEach((btn) => {
        btn.addEventListener("click", function () {
          const action = this.textContent.trim();
          console.log("Action button clicked:", action);

          if (action.includes("Export")) {
            showToast('Generating report...');
          } else if (action.includes("Approve")) {
            showToast('Opening approval queue...');
          } else if (action.includes("Reject")) {
            showToast('Opening rejection form...');
          }
        });
      });

// Notification click
const notifBtn=document.querySelector('.notification-btn');
if(notifBtn){ notifBtn.addEventListener('click',()=>showToast('You have new notifications')); }

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

        // Add click event to User Management menu item
document.addEventListener('DOMContentLoaded', function() {
  // No-op; navigation handled by anchor hrefs above
});


// Logout function
function logout() {
    showLogoutConfirmation();
}

function showLogoutConfirmation() {
  // Create modal overlay
  const modal = document.createElement('div');
  modal.id = 'logout-modal';
  modal.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
    animation: fadeIn 0.3s ease;
  `;

  // Create modal content
  const modalContent = document.createElement('div');
  modalContent.style.cssText = `
    background: white;
    border-radius: 12px;
    padding: 30px;
    max-width: 400px;
    width: 90%;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
    animation: slideIn 0.3s ease;
    text-align: center;
  `;

  modalContent.innerHTML = `
    <div style="font-size: 48px; margin-bottom: 20px;">🚪</div>
    <h3 style="margin: 0 0 10px 0; color: #1e3c72; font-size: 24px;">Logout Confirmation</h3>
    <p style="margin: 0 0 25px 0; color: #666; font-size: 16px;">Are you sure you want to logout?</p>
    <div style="display: flex; gap: 12px; justify-content: center;">
      <button id="logout-cancel" style="
        padding: 12px 24px;
        border: 2px solid #6c757d;
        background: white;
        color: #6c757d;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
        transition: all 0.3s ease;
      ">Cancel</button>
      <button id="logout-confirm" style="
        padding: 12px 24px;
        border: none;
        background: #dc3545;
        color: white;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
        transition: all 0.3s ease;
      ">Logout</button>
    </div>
  `;

  // Add animations
  const style = document.createElement('style');
  style.textContent = `
    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }
    @keyframes slideIn {
      from { opacity: 0; transform: translateY(-50px); }
      to { opacity: 1; transform: translateY(0); }
    }
    #logout-cancel:hover {
      background: #6c757d;
      color: white;
    }
    #logout-confirm:hover {
      background: #c82333;
    }
  `;
  document.head.appendChild(style);

  modal.appendChild(modalContent);
  document.body.appendChild(modal);

  // Event handlers
  const cancelBtn = document.getElementById('logout-cancel');
  const confirmBtn = document.getElementById('logout-confirm');

  const closeModal = () => {
    modal.remove();
    style.remove();
  };

  cancelBtn.addEventListener('click', closeModal);
  confirmBtn.addEventListener('click', () => {
    closeModal();
    showToast('Logging out...');
    fetch('/auth/logout',{method:'POST',headers:{'Content-Type':'application/json'}})
        .then(r=>r.json()).then(d=>{ window.location.href = d?.redirect_url || '/college-login-system.html'; })
        .catch(()=>{ window.location.href='/college-login-system.html'; });
  });

  // Close on overlay click
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      closeModal();
    }
  });

  // Close on Escape key
  const handleEscape = (e) => {
    if (e.key === 'Escape') {
      closeModal();
      document.removeEventListener('keydown', handleEscape);
    }
  };
  document.addEventListener('keydown', handleEscape);
}

// Logout
const logoutLink=document.querySelector('.logout-btn');
if(logoutLink){
  logoutLink.addEventListener('click',function(e){
    e.preventDefault();
    logout();
  });
}

// Inline view request details in modal on admin dashboard
function openAdminRequestDetails(requestId, status){
  const modal = document.getElementById('adminRequestModal');
  const title = document.getElementById('adminModalTitle');
  const content = document.getElementById('adminRequestDetails');
  const closeX = document.getElementById('adminModalClose');
  const closeBtn = document.getElementById('adminModalCloseBtn');
  if(!modal||!title||!content) return;
  title.textContent = `Request #REQ-${String(requestId).padStart(6,'0')}`;
  content.innerHTML = '<div style="text-align:center;padding:30px;color:#666;">Loading...</div>';
  modal.style.display = 'flex';

  const renderWorkflowChips = (workflow=[])=>{
    const stepMap = [
      {key:'submitted', label:'Submitted'},
      {key:'guide_approval', label:'Guide'},
      {key:'hod_approval', label:'HOD'},
      {key:'it_services_approval', label:'IT'},
      {key:'final_approval', label:'Final'}
    ];
    return `<div class="wf-inline">` + stepMap.map(s=>{
      const st=(workflow.find(w=>w.step===s.key)||{}).status||'pending';
      const cls = st==='completed'?'wf-completed':(st==='rejected'?'wf-rejected':(st==='pending'?'wf-current':'wf-pending'));
      return `<span class=\"wf-chip ${cls}\">${s.label}</span>`;
    }).join('') + `</div>`;
  };

  fetch(`/approvals/workflow/${requestId}`).then(r=>r.json()).then(({success,data})=>{
    if(!success||!data){ content.innerHTML = '<div style="padding:20px;color:#c33;">Failed to load details</div>'; return; }
    const req = data.data?.request || {};
    const wf = data.data?.workflow || [];
    const statusText = (req.status||'').replace('_',' ').replace(/\b\w/g,c=>c.toUpperCase());
    // Parse additional form fields from description (submitted form data)
    const formData = parseFormDataFromDescription(req.description||'');
    const formGrid = formData && Object.keys(formData).length ? (
      '<div class=\\"detail-row\\" style=\\"margin-top:10px;\\"><div class=\\"detail-label\\">Form Details:</div><div class=\\"detail-value\\">'
      + '<div style=\\"display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;\\">'
      + Object.entries(formData).map(([key,value])=>{
          const label = key.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase());
          const val = Array.isArray(value) ? value.join(', ') : value;
          return `<div style=\\"background:#f8f9fa;padding:10px;border-radius:6px;border-left:3px solid #1e3c72;\\"><div style=\\"font-weight:600;color:#1e3c72;margin-bottom:6px;\\">${label}</div><div style=\\"color:#555;\\">${val}</div></div>`;
        }).join('')
      + '</div></div></div>'
    ) : '';

    content.innerHTML = `
      <div class=\"detail-row\"><div class=\"detail-label\">Project Title:</div><div class=\"detail-value\">${req.project_title||''}</div></div>
      <div class=\"detail-row\"><div class=\"detail-label\">Student:</div><div class=\"detail-value\">${req.user_name||''}</div></div>
      <div class=\"detail-row\"><div class=\"detail-label\">Purpose:</div><div class=\"detail-value\">${req.purpose||''}</div></div>
      <div class=\"detail-row\"><div class=\"detail-label\">Expected Duration:</div><div class=\"detail-value\">${req.expected_duration||'Not specified'}</div></div>
      <div class=\"detail-row\"><div class=\"detail-label\">Priority:</div><div class=\"detail-value\">${(req.priority||'').toString().replace(/\b\w/g,c=>c.toUpperCase())}</div></div>
      <div class=\"detail-row\"><div class=\"detail-label\">Status:</div><div class=\"detail-value\">${statusText}</div></div>
      <div class=\"detail-row\"><div class=\"detail-label\">Submitted:</div><div class=\"detail-value\">${req.submitted_at?new Date(req.submitted_at).toLocaleString():''}</div></div>
      ${req.rejection_reason?`<div class=\\"detail-row\\"><div class=\\"detail-label\\">Rejection Reason:</div><div class=\\"detail-value\\" style=\\"color:#dc3545;\\">${req.rejection_reason}</div></div>`:''}
      <div class=\"detail-row\"><div class=\"detail-label\">Description:</div><div class=\"detail-value\" style=\"white-space: pre-wrap; background:#f8f9fa; padding:12px; border-radius:6px; border-left:4px solid #1e3c72;\">${req.description||''}</div></div>
      <div class=\"detail-row\"><div class=\"detail-label\">Workflow:</div><div class=\"detail-value\">${renderWorkflowChips(wf)}</div></div>
      ${formGrid}
    `;
  }).catch(()=>{ content.innerHTML = '<div style="padding:20px;color:#c33;">Failed to load details</div>'; });

  function close(){ modal.style.display='none'; }
  if(closeX){ closeX.onclick = close; }
  if(closeBtn){ closeBtn.onclick = close; }
  window.addEventListener('click', function onWin(e){ if(e.target===modal){ close(); window.removeEventListener('click', onWin); } });
}

// Parse additional information section from description into key/value map
function parseFormDataFromDescription(description){
  try{
    const match = String(description||'').match(/Additional Information:\n([\s\S]*)/);
    if(!match) return {};
    const lines = match[1].split('\n').map(l=>l.trim()).filter(Boolean);
    const data = {};
    lines.forEach(line=>{
      const idx = line.indexOf(':');
      if(idx===-1) return;
      const key = line.slice(0,idx).trim().toLowerCase().replace(/\s+/g,'_');
      const valRaw = line.slice(idx+1).trim();
      if(!valRaw || valRaw==='N/A') return;
      const val = valRaw.includes(',') ? valRaw.split(',').map(s=>s.trim()) : valRaw;
      data[key] = val;
    });
    return data;
  }catch(_){ return {}; }
}

// Display workflow process bar
function displayWorkflow(data) {
    const container = document.getElementById('workflow-container');
    const stepsContainer = document.getElementById('workflow-steps');
    
    if (!container || !stepsContainer) return;
    
    // Show the workflow container
    container.style.display = 'block';
    
    // Clear existing steps
    stepsContainer.innerHTML = '';
    
    // Define workflow steps
    const stepConfig = [
        { key: 'submitted', label: 'Submitted', icon: '📝' },
        { key: 'guide_approval', label: 'Guide Approval', icon: '👨‍🏫' },
        { key: 'hod_approval', label: 'HOD Approval', icon: '👨‍💼' },
        { key: 'final_approval', label: 'Final Approval', icon: '✅' }
    ];
    
    // Create workflow steps
    stepConfig.forEach((step, index) => {
        const stepElement = document.createElement('div');
        stepElement.className = 'workflow-step';
        
        const workflowStep = data.workflow.find(w => w.step === step.key);
        if (workflowStep) {
            if (workflowStep.status === 'completed') {
                stepElement.classList.add('completed');
            } else if (workflowStep.status === 'rejected') {
                stepElement.classList.add('rejected');
            } else if (workflowStep.status === 'pending' && index === 0) {
                stepElement.classList.add('current');
            } else if (workflowStep.status === 'pending' && data.workflow[index - 1]?.status === 'completed') {
                stepElement.classList.add('current');
            }
        }
        
        const icon = document.createElement('div');
        icon.className = 'workflow-step-icon';
        icon.textContent = step.icon;
        
        const label = document.createElement('div');
        label.className = 'workflow-step-label';
        label.textContent = step.label;
        
        const time = document.createElement('div');
        time.className = 'workflow-step-time';
        if (workflowStep && workflowStep.timestamp) {
            const date = new Date(workflowStep.timestamp);
            time.textContent = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
        }
        
        stepElement.appendChild(icon);
        stepElement.appendChild(label);
        stepElement.appendChild(time);
        stepsContainer.appendChild(stepElement);
    });
    
    // Scroll to workflow
    container.scrollIntoView({ behavior: 'smooth' });
}

// Utility actions
function getSelectedRequestId(){
  const firstBtn = document.querySelector('#approval-list .btn[data-id]');
  return firstBtn ? firstBtn.getAttribute('data-id') : null;
}
function approveSelected(){
  const id=getSelectedRequestId();
  if(!id){ showToast('No request selected'); return; }
  
  // Determine the correct approve endpoint based on user role
  let approveEndpoint = `/admin/requests/${id}/approve`;
  if (currentUserRole === 'project_guide') {
    approveEndpoint = `/approvals/guide/approve/${id}`;
  } else if (currentUserRole === 'hod') {
    approveEndpoint = `/approvals/hod/approve/${id}`;
  } else if (currentUserRole === 'it_services') {
    approveEndpoint = `/approvals/it-services/approve/${id}`;
  }
  
  fetch(approveEndpoint,{method:'POST',headers:{'Content-Type':'application/json'}})
    .then(r=>r.json()).then(d=>{
      if(d.success){ showToast('Approved'); reloadDashboard(); }
      else showToast(d.message||'Approve failed');
    }).catch(()=>showToast('Network error'));
}
function rejectSelected(){
  const id=getSelectedRequestId();
  if(!id){ showToast('No request selected'); return; }
  openRejectionModal(id);
}

function openRejectionModal(requestId){
  let modal = document.getElementById('admin-reject-modal');
  if(!modal){
    modal = document.createElement('div');
    modal.id = 'admin-reject-modal';
    modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:10000;';
    modal.innerHTML = `
      <div style="background:#fff;border-radius:12px;max-width:480px;width:90%;padding:20px;box-shadow:0 10px 30px rgba(0,0,0,0.2)">
        <div style="font-weight:700;font-size:18px;margin-bottom:10px;color:#1e3c72">Reject Request</div>
        <div style="color:#555;margin-bottom:8px">Provide a reason for rejection:</div>
        <textarea id="admin-reject-reason" style="width:100%;min-height:100px;padding:10px;border:1px solid #ddd;border-radius:8px;resize:vertical" placeholder="Enter rejection reason..."></textarea>
        <div style="display:flex;gap:10px;justify-content:flex-end;margin-top:14px">
          <button id="admin-reject-cancel" style="padding:8px 14px;border:none;border-radius:6px;background:#6c757d;color:#fff;cursor:pointer">Cancel</button>
          <button id="admin-reject-submit" style="padding:8px 14px;border:none;border-radius:6px;background:#dc3545;color:#fff;cursor:pointer">Submit Rejection</button>
        </div>
      </div>`;
    document.body.appendChild(modal);
  } else {
    modal.style.display = 'flex';
  }
  const reasonInput = modal.querySelector('#admin-reject-reason');
  const cancelBtn = modal.querySelector('#admin-reject-cancel');
  const submitBtn = modal.querySelector('#admin-reject-submit');
  if (reasonInput) reasonInput.value = '';
  const close = ()=>{ modal.style.display='none'; };
  if (cancelBtn) cancelBtn.onclick = close;
  if (submitBtn) submitBtn.onclick = ()=>{
    const reason = (reasonInput?.value||'').trim();
    if(!reason){ showToast('Please enter a reason'); return; }
    rejectSelectedWithReason(requestId, reason).then(close);
  };
}

async function rejectSelectedWithReason(id, reason){
  try{
    // Determine the correct reject endpoint based on user role
    let rejectEndpoint = `/admin/requests/${id}/reject`;
    if (currentUserRole === 'project_guide') {
      rejectEndpoint = `/approvals/guide/reject/${id}`;
    } else if (currentUserRole === 'hod') {
      rejectEndpoint = `/approvals/hod/reject/${id}`;
    } else if (currentUserRole === 'it_services') {
      rejectEndpoint = `/approvals/it-services/reject/${id}`;
    }
    
    const res = await fetch(rejectEndpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({reason})});
    const d = await res.json().catch(()=>({success:false}));
    if(res.ok && d.success){
      showToast('Request rejected and moved to Rejected');
      try { localStorage.setItem('refreshRejectedRequests', String(Date.now())); } catch(_) {}
      reloadDashboard();
    } else {
      showToast((d && d.message) || 'Reject failed');
    }
  }catch(_){ showToast('Network error'); }
}
function exportReport(){ window.location.href = '/admin/export/requests?format=csv'; }

// Store current user role
let currentUserRole = null;

function reloadDashboard(){
  // Signal other tabs and self to refresh
  try { localStorage.setItem('dashboardRefresh', String(Date.now())); } catch(_) {}
  
  // Try to recover role from session storage if not set
  if (!currentUserRole) {
    try {
      currentUserRole = sessionStorage.getItem('userRole');
      if (currentUserRole) {
        console.log('Role recovered from session storage:', currentUserRole);
      }
    } catch(e) {
      console.error('Could not recover role from session storage:', e);
    }
  }
  
  console.log('Reloading dashboard for role:', currentUserRole);
  
  // Determine the correct endpoint based on user role
  let dashboardEndpoint = '/admin/dashboard';
  let pendingRequestsKey = 'pending_approvals';
  
  if (currentUserRole === 'project_guide') {
    dashboardEndpoint = '/approvals/guide/dashboard';
    pendingRequestsKey = 'pending_requests';
    console.log('Using Project Guide dashboard endpoint');
  } else if (currentUserRole === 'hod') {
    dashboardEndpoint = '/approvals/hod/dashboard';
    pendingRequestsKey = 'pending_requests';
    console.log('Using HOD dashboard endpoint');
  } else if (currentUserRole === 'it_services') {
    dashboardEndpoint = '/approvals/it-services/dashboard';
    pendingRequestsKey = 'pending_requests';
    console.log('Using IT Services dashboard endpoint');
  } else {
    console.log('Using default Admin dashboard endpoint');
  }
  
  console.log('Fetching from:', dashboardEndpoint);
  
  // Re-fetch dashboard data
  fetch(dashboardEndpoint).then(r=>r.json()).then(({success,data})=>{
    console.log('Dashboard data received:', {success, dataKeys: Object.keys(data || {})});
    console.log('Stats object:', data?.stats);
    if(!success||!data) return;
    const s=data.stats||{};
    const el=(id)=>document.getElementById(id);
    
    console.log('Setting students count:', s.students_count);
    console.log('Setting total requests:', s.total_requests);
    console.log('Setting pending requests:', s.pending_requests);
    console.log('Setting approved requests:', s.approved_requests);
    
    if(el('stat-admin-students')) {
      el('stat-admin-students').textContent = s.students_count ?? 0;
      console.log('Students element updated to:', s.students_count);
    }
    if(el('stat-admin-requests')) {
      el('stat-admin-requests').textContent = s.total_requests ?? 0;
      console.log('Requests element updated to:', s.total_requests);
    }
    if(el('stat-admin-pending')) {
      el('stat-admin-pending').textContent = s.pending_requests ?? s.pending_count ?? 0;
      console.log('Pending element updated to:', s.pending_requests);
    }
    if(el('stat-admin-approved')) {
      el('stat-admin-approved').textContent = s.approved_requests ?? s.approved_count ?? 0;
      console.log('Approved element updated to:', s.approved_requests);
    }
    const list=document.getElementById('approval-list');
    const badge=document.getElementById('pending-count');
    const items=(data[pendingRequestsKey]||[]);
    if(badge) badge.textContent = items.length ? `${items.length} Pending` : '';
    if(list){
      list.innerHTML='';
      items.forEach(req=>{
        const div=document.createElement('div');
        div.className='approval-item';
        div.innerHTML=`<div class=\"approval-item-header\"><div><div class=\"approval-item-title\">Req #${req.id} - ${req.user_name||''}</div><div class=\"approval-item-meta\">Title: ${req.project_title}</div><div class=\"approval-item-meta\">Status: ${req.status}</div></div></div><div class=\"approval-actions\"><button class=\"btn btn-primary\" data-id=\"${req.id}\" onclick=\"viewRequestWorkflow(${req.id})\">👁️ View Details</button></div>`;
        list.appendChild(div);
      });
    }
  });
  
  // Also refresh rejected requests
  refreshRejectedRequests();
}

function refreshRejectedRequests(){
  fetch('/admin/requests/rejected?per_page=5').then(r=>r.json()).then(({success,data})=>{
    if(!success||!data) return;
    const list=document.getElementById('rejected-requests');
    if(!list) return;
    list.innerHTML = '';
    const items = data.requests || [];
    if(items.length===0){ list.innerHTML = '<div class="no-requests">No rejections</div>'; return; }
    items.forEach(req=>{
      const div=document.createElement('div');
      div.className='user-item';
      const who = req.rejected_by_name || 'Unknown';
      const ts = req.rejected_at ? new Date(req.rejected_at).toLocaleString() : '';
      div.innerHTML = `<div class="user-info"><div class="user-avatar">✖</div><div class="user-details"><div class="user-name">Req #${req.id} - ${req.project_title}</div><div class="user-role">By ${who} • ${ts}</div><div class="user-role" style="color:#c33">${(req.rejection_reason||req.rejection_comment)||''}</div></div></div>`;
      list.appendChild(div);
    });
  }).catch(()=>{});
}

// Listen for refresh signal
window.addEventListener('storage', (e)=>{
  if (e.key === 'dashboardRefresh') {
    reloadDashboard();
  } else if (e.key === 'refreshRejectedRequests') {
    refreshRejectedRequests();
  }
});

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

// Navigate to approval workflow details page for a specific request
function viewRequestWorkflow(requestId){
  try{
    const url = new URL(window.location.origin + '/admin_workflow_dashboard.html');
    url.searchParams.set('requestId', String(requestId));
    window.location.href = url.toString();
  }catch(_){
    window.location.href = 'admin_workflow_dashboard.html?requestId=' + encodeURIComponent(String(requestId));
  }
}

// Close request (admin only)
function closeRequest(requestId) {
  if (currentUserRole !== 'admin') {
    showToast('Only administrators can close requests', 'error');
    return;
  }
  
  if (!confirm('Are you sure you want to close this request? This action marks the request as completed and closed.')) {
    return;
  }
  
  fetch(`/admin/requests/${requestId}/close`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'}
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      showToast('Request closed successfully');
      reloadDashboard();
    } else {
      showToast(data.message || 'Failed to close request');
    }
  })
  .catch(() => showToast('Network error'));
}

// Load admin profile data
function loadAdminProfile() {
    console.log('Loading admin profile...');
    return fetch('/admin/profile')
        .then(response => {
            console.log('Profile response status:', response.status, response.statusText);
            return response.json();
        })
        .then(data => {
            console.log('Profile data received:', data);
            console.log('data.success:', data.success);
            console.log('data.admin:', data.admin);
            if (data.success && data.admin) {
                const admin = data.admin;
                console.log('admin object:', admin);
                console.log('admin.role:', admin.role);
                
                // Store the user's role globally
                currentUserRole = admin.role;
                console.log('Current user role set to:', currentUserRole);
                
                // Store in session storage for persistence
                try {
                    sessionStorage.setItem('userRole', admin.role);
                    console.log('Role saved to session storage');
                } catch(e) {
                    console.warn('Could not save role to session storage:', e);
                }
                
                // Update dashboard title based on role
                const approvalTitle = document.querySelector('.approval-title');
                if (approvalTitle) {
                    const titles = {
                        'project_guide': 'Pending Project Guide Approval',
                        'hod': 'Pending HOD Approval',
                        'it_services': 'Pending IT Services Approval',
                        'admin': 'Pending Faculty Approval'
                    };
                    approvalTitle.textContent = titles[admin.role] || 'Pending Approvals';
                    console.log('Dashboard title updated to:', approvalTitle.textContent);
                }
                
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
            return data;
        })
        .catch(error => {
            console.error('❌ Error loading admin profile:', error);
            console.error('Error stack:', error.stack);
            throw error;
        });
}

// Fallback if role is not detected
function ensureRoleIsSet() {
    if (!currentUserRole) {
        console.warn('⚠️ User role not set! Attempting to detect from URL or defaulting to admin...');
        // Try to get from session storage as fallback
        try {
            const stored = sessionStorage.getItem('userRole');
            if (stored) {
                currentUserRole = stored;
                console.log('Role recovered from session storage:', currentUserRole);
            }
        } catch(e) {
            console.error('Could not access session storage:', e);
        }
    }
}

// Bind admin dashboard data and lists
document.addEventListener('DOMContentLoaded',function(){
  // Load admin profile first, then reload dashboard
  loadAdminProfile().then(() => {
    reloadDashboard();
  }).catch(() => {
    reloadDashboard(); // Load anyway even if profile fails
  });

  // Active users
  fetch('/admin/users?per_page=5').then(r=>r.json()).then(({success,data})=>{
    if(!success||!data) return;
    const wrap=document.getElementById('active-users');
    if(!wrap) return;
    wrap.innerHTML='';
    (data.users||[]).forEach(u=>{
      const item=document.createElement('div');
      item.className='user-item';
      const initials=(u.first_name?.[0]||'')+(u.last_name?.[0]||'');
      item.innerHTML=`<div class="user-info"><div class="user-avatar">${initials}</div><div class="user-details"><div class="user-name">${u.full_name||u.first_name}</div><div class="user-role">${u.role}</div></div></div>`;
      wrap.appendChild(item);
    });
  }).catch(()=>{});

  // Rejected requests
  fetch('/admin/requests/rejected?per_page=5').then(r=>r.json()).then(({success,data})=>{
    if(!success||!data) return;
    const list=document.getElementById('rejected-requests');
    if(!list) return;
    list.innerHTML = '';
    const items = data.requests || [];
    if(items.length===0){ list.innerHTML = '<div class="no-requests">No rejections</div>'; return; }
    items.forEach(req=>{
      const div=document.createElement('div');
      div.className='user-item';
      const who = req.rejected_by_name || 'Unknown';
      const ts = req.rejected_at ? new Date(req.rejected_at).toLocaleString() : '';
      div.innerHTML = `<div class="user-info"><div class="user-avatar">✖</div><div class="user-details"><div class="user-name">Req #${req.id} - ${req.project_title}</div><div class="user-role">By ${who} • ${ts}</div><div class="user-role" style="color:#c33">${(req.rejection_reason||req.rejection_comment)||''}</div></div></div>`;
      list.appendChild(div);
    });
  }).catch(()=>{});
});
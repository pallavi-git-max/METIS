// JavaScript for interactivity
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
    fetch('/auth/logout', { method: 'POST', headers: { 'Content-Type': 'application/json' }})
      .then(r=>r.json())
      .then((data)=>{
        window.location.href = data?.redirect_url || '/college-login-system.html';
      })
      .catch(()=>{ window.location.href = '/college-login-system.html'; });
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

function navigateToPage(page) {
  const menuItem = document.querySelector(`[data-page="${page}"]`);
  if (menuItem) {
    menuItem.click();
  }
}

function markAllRead() {
  const unreadNotifications = document.querySelectorAll('.activity-item[style*="border-left"]');
  unreadNotifications.forEach(notification => {
    notification.style.borderLeft = 'none';
    notification.style.background = 'var(--gray-50)';
  });
  alert('All notifications marked as read');
}

function loadUserDashboard() {
  // Populate from backend
  fetch('/user/dashboard', { credentials: 'include' })
    .then(async (r)=>{
      if (r.status === 401 || r.status === 302) {
        const next = encodeURIComponent('/user_dash.html');
        window.location.href = `/college-login-system.html?next=${next}`;
        return Promise.reject('unauth');
      }
      return r.json();
    })
    .then(({success,data})=>{
      if(!success||!data) {
        console.error('Failed to load user data:', data);
        return;
      }
      
      console.log('User data loaded:', data.user);
      console.log('User role:', data.user.role);
      console.log('Statistics:', data.statistics);
      
      const u=data.user||{};
      const userName = (u.full_name && u.full_name.trim())
        ? u.full_name.trim()
        : ((u.first_name||'').trim() || (u.email ? u.email.split('@')[0] : '') || (u.student_id||'User'));
      const userInitials = ((data.user.first_name||'')[0]||'') + ((data.user.last_name||'')[0]||'');
      
      console.log('Computed userName:', userName);
      console.log('Computed userInitials:', userInitials);

      // Update welcome message
      const userGreeting = document.getElementById('user-greeting');
      if (userGreeting) { userGreeting.textContent = userName; }

      const welcomeUsername = document.getElementById('welcome-username');
      if (welcomeUsername) {
        const fallbackFirst = (u.first_name || '').trim() || (userName.split(' ')[0]||'').trim() || (u.email||'').split('@')[0] || (u.student_id||'User');
        welcomeUsername.textContent = fallbackFirst;
      }

      const welcomeSubtitle = document.getElementById('welcome-subtitle');
      if (welcomeSubtitle) {
        const pending = (data.statistics && data.statistics.pending_requests) || 0;
        welcomeSubtitle.textContent = `Here's what's happening with your requests today. You have ${pending} pending item${pending===1?'':'s'} that need your attention.`;
      }

      // Update avatar with profile photo if available
      const userAvatar = document.getElementById('user-avatar');
      if (userAvatar) {
        if (u.profile_photo) {
          // Replace icon with profile photo
          userAvatar.innerHTML = `<img src="/auth/profile-photo/${u.profile_photo}" alt="Profile" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;">`;
        } else {
          // Keep the icon if no photo
          console.log('No profile photo, keeping icon');
        }
      }

      const profileAvatar = document.getElementById('profile-avatar');
      if (profileAvatar) {
        if (u.profile_photo) {
          profileAvatar.innerHTML = `<img src="/auth/profile-photo/${u.profile_photo}" alt="Profile" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">`;
        } else {
          profileAvatar.textContent = userInitials;
        }
      }

      // Update profile dropdown avatar with profile photo
      const profileDropdownAvatar = document.getElementById('profile-dropdown-avatar');
      if (profileDropdownAvatar) {
        if (u.profile_photo) {
          profileDropdownAvatar.innerHTML = `<img src="/auth/profile-photo/${u.profile_photo}" alt="Profile" style="width: 50px; height: 50px; border-radius: 50%; object-fit: cover;">`;
        } else {
          // Keep the icon if no photo
          console.log('Profile dropdown: no photo, keeping icon');
        }
      }

      const profileDropdownName = document.getElementById('profile-dropdown-name');
      if (profileDropdownName) profileDropdownName.textContent = userName;

      const profileDropdownEmail = document.getElementById('profile-dropdown-email');
      if (profileDropdownEmail) profileDropdownEmail.textContent = data.user.email || '';

      const profileDropdownRole = document.getElementById('profile-dropdown-role');
      if (profileDropdownRole) profileDropdownRole.textContent = (data.user.role||'').replace('_',' ').replace(/\b\w/g,c=>c.toUpperCase());

      const profileDropdownStudentId = document.getElementById('profile-dropdown-student-id');
      if (profileDropdownStudentId) {
        // Use student_id as the login ID
        profileDropdownStudentId.textContent = data.user.student_id || data.user.email || '—';
        console.log('Updated User ID:', data.user.student_id || data.user.email);
      }

      const profileDropdownPhone = document.getElementById('profile-dropdown-phone');
      if (profileDropdownPhone) {
        profileDropdownPhone.textContent = data.user.phone || '—';
        console.log('Updated Phone:', data.user.phone);
      }

      const profileName = document.getElementById('profile-name');
      if (profileName) profileName.textContent = userName;

      const profileRole = document.getElementById('profile-role');
      if (profileRole) profileRole.textContent = (data.user.role||'').replace('_',' ').replace(/\b\w/g,c=>c.toUpperCase());

      const detailEmail = document.getElementById('detail-email');
      if (detailEmail) detailEmail.textContent = data.user.email || '';

      const detailPhone = document.getElementById('detail-phone');
      if (detailPhone) detailPhone.textContent = data.user.phone || '—';

      const detailDepartment = document.getElementById('detail-department');
      if (detailDepartment) {
        console.log('Department value:', data.user.department, 'Type:', typeof data.user.department);
        detailDepartment.textContent = data.user.department ? data.user.department.replace('_',' ').toUpperCase() : '—';
      }

      const detailStudentId = document.getElementById('detail-student-id');
      if (detailStudentId) detailStudentId.textContent = data.user.student_id || '—';

      const detailJoinDate = document.getElementById('detail-join-date');
      if (detailJoinDate) detailJoinDate.textContent = (data.user.created_at || '').split('T')[0] || '—';

      const detailStatus = document.getElementById('detail-status');
      if (detailStatus) detailStatus.textContent = (data.user.is_active ? 'Active' : 'Inactive');

      // Handle external user specific fields
      const userRole = data.user.role;
      const isExternalUser = userRole === 'external';
      
      // Show/hide external user fields
      const externalFields = ['campus-group', 'aadhar-group', 'profession-group', 'institution-group', 'address-group', 'location-group'];
      externalFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
          field.style.display = isExternalUser ? 'block' : 'none';
        }
      });

      // Populate external user fields
      if (isExternalUser) {
        const detailCampus = document.getElementById('detail-campus');
        if (detailCampus) detailCampus.textContent = data.user.campus || '—';

        const detailAadhar = document.getElementById('detail-aadhar');
        if (detailAadhar) {
          const aadhar = data.user.aadhar_card || '';
          // Mask Aadhar number for privacy (show only last 4 digits)
          const maskedAadhar = aadhar ? '****-****-' + aadhar.slice(-4) : '—';
          detailAadhar.textContent = maskedAadhar;
        }

        const detailProfession = document.getElementById('detail-profession');
        if (detailProfession) detailProfession.textContent = data.user.profession || '—';

        const detailInstitution = document.getElementById('detail-institution');
        if (detailInstitution) detailInstitution.textContent = data.user.institution || '—';

        const detailAddress = document.getElementById('detail-address');
        if (detailAddress) detailAddress.textContent = data.user.address || '—';

        const detailLocation = document.getElementById('detail-location');
        if (detailLocation) {
          const city = data.user.city || '';
          const state = data.user.state || '';
          const pincode = data.user.pincode || '';
          const location = [city, state, pincode].filter(Boolean).join(', ') || '—';
          detailLocation.textContent = location;
        }
      }

      // Stats
      const s = data.statistics || {};
      const total = document.getElementById('stat-total-requests');
      if (total) total.textContent = s.total_requests ?? 0;
      const pending = document.getElementById('stat-pending');
      if (pending) pending.textContent = s.pending_requests ?? 0;
      const approved = document.getElementById('stat-approved');
      if (approved) approved.textContent = s.approved_requests ?? 0;
      const rejected = document.getElementById('stat-rejected');
      if (rejected) rejected.textContent = s.rejected_requests ?? 0;

      // Recent requests table/list if present
      const recent = data.recent_requests || [];
      const recentContainer = document.getElementById('recent-requests');
      if (recentContainer) {
        recentContainer.innerHTML = '';
        recent.forEach(rq => {
          const li = document.createElement('li');
          li.textContent = `${rq.project_title} - ${rq.status}`;
          recentContainer.appendChild(li);
        });
      }

      // Load requests table
      loadRequestsTable();
    })
    .catch((error) => {
      console.error('Error loading dashboard data:', error);
    });
}

// Load dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  loadUserDashboard();
  
  // Check if editing a request (do this BEFORE cleaning query params)
  const urlParams = new URLSearchParams(window.location.search);
  const editRequestId = urlParams.get('edit');
  if (editRequestId) {
    console.log('Edit mode detected for request:', editRequestId);
    // Navigate to Submit Request page first
    setTimeout(() => {
      console.log('Navigating to submit page');
      navigateToPage('submit');
    }, 100);
    // Then load request data and populate form
    setTimeout(() => {
      console.log('Loading request data');
      loadRequestForEdit(editRequestId);
    }, 300);
  }
  
  // Clean query params like ?type=external&userId=... but KEEP ?edit=...
  if ((window.location.search.includes('type=') || window.location.search.includes('userId=')) && !window.location.search.includes('edit=')) {
    const url = new URL(window.location);
    url.search = '';
    window.history.replaceState({}, '', url);
  }
  
  loadRequestsTable();
  loadActivities();
  
  // Navigation functionality
  const menuItems = Array.from(document.querySelectorAll('.menu-item'));
  const pages = Array.from(document.querySelectorAll('.page-content'));
  const pageTitle = document.getElementById('page-title');

  const pageTitles = {
    'dashboard': 'Dashboard',
    'profile': 'My Profile',
    'requests': 'My Requests',
    'submit': 'Submit Request',
    'activities': 'Activities',
    'notifications': 'Notifications'
  };

  menuItems.forEach(item => {
    item.addEventListener('click', function(e) {
      e.preventDefault();
      const targetPage = this.getAttribute('data-page');

      if (targetPage) {
        // Remove active class from all menu items
        menuItems.forEach(mi => mi.classList.remove('active'));

        // Add active class to clicked item
        this.classList.add('active');

        // Hide all pages
        pages.forEach(page => page.classList.remove('active'));

        // Show target page
        const targetPageElement = document.getElementById(targetPage + '-page');
        if (targetPageElement) {
          targetPageElement.classList.add('active');
          if (pageTitle) pageTitle.textContent = pageTitles[targetPage] || 'Page';
          
          // Load specific page data
          if (targetPage === 'activities') {
            loadActivities();
          } else if (targetPage === 'requests') {
            loadRequestsTable();
          }
        }

        // Special handling for profile submenu
        if (['requests', 'submit', 'analytics'].includes(targetPage)) {
          const profileItem = document.querySelector('[data-page="profile"]');
          if (profileItem && !profileItem.classList.contains('active')) {
            profileItem.classList.add('active');
          }
        }
      }
    });
  });

  // Profile edit functionality
  window.editProfile = function() {
    alert('Edit profile functionality would be implemented here');
  };

  // Toggle "Other" specification fields
  window.toggleOther = function(targetId) {
    const targetElement = document.getElementById(targetId);
    if (targetElement) {
      const isVisible = targetElement.classList.toggle('visible');
      targetElement.style.display = isVisible ? 'block' : 'none';
    }
  };

  // Form submission handler (defensive: only attach if form exists)
  const form = document.getElementById('metisRequisitionForm');
  if (form) {
    form.addEventListener('submit', function(e) {
      e.preventDefault();

      // Basic form validation
      const requiredFields = Array.from(form.querySelectorAll('[required]'));
      let allValid = true;

      requiredFields.forEach(field => {
        // Skip validation for fields that are not visible
        if (field.offsetParent === null) {
          // hidden via display:none -> skip
          return;
        }

        const type = field.type;
        let isValid = true;

        if (type === 'checkbox' || type === 'radio') {
          const name = field.name;
          const checkedInputs = form.querySelectorAll(`[name="${name}"]:checked`);
          isValid = checkedInputs.length > 0;
        } else {
          isValid = String(field.value || '').trim() !== '';
        }

        const questionSection = field.closest('.question-section');

        if (!isValid) {
          allValid = false;
          try { field.style.borderColor = 'var(--danger)'; } catch (err) {}
          if (questionSection) questionSection.style.borderLeftColor = 'var(--danger)';
        } else {
          try { field.style.borderColor = 'var(--gray-300)'; } catch (err) {}
          if (questionSection) questionSection.style.borderLeftColor = 'var(--primary)';
        }
      });

      if (allValid) {
        // Collect form data
        const formData = new FormData(form);
        const entries = {};
        for (let [key, value] of formData.entries()) {
          if (entries[key]) {
            if (Array.isArray(entries[key])) entries[key].push(value); else entries[key] = [entries[key], value];
          } else {
            entries[key] = value;
          }
        }

        // Build minimal backend payload
        const fields = Array.from(form.querySelectorAll('input[name="fields"]:checked')).map(i=>i.value);
        const types = Array.from(form.querySelectorAll('input[name="data-type"]:checked')).map(i=>i.value);
        const pkg = (form.querySelector('input[name="package"]:checked')||{}).value || null;
        const datasetStatus = (form.querySelector('input[name="dataset-status"]:checked')||{}).value || null;
        const datasetSize = (form.querySelector('input[name="dataset-size"]:checked')||{}).value || null;
        const cores = (form.querySelector('input[name="cores"]:checked')||{}).value || null;

        const project_title = `METIS Access Request - ${new Date().toISOString().slice(0,10)}`;
        const purpose = 'Access to METIS Lab resources as per requisition form';
        const guideEmail = form.querySelector('#guide-email')?.value || '';
        const description = [
          `Fields: ${fields.join(', ') || 'N/A'}`,
          `Package: ${pkg || 'N/A'}`,
          `Dataset: ${datasetStatus || 'N/A'}`,
          `Size: ${datasetSize || 'N/A'}`,
          `Data Types: ${types.join(', ') || 'N/A'}`,
          `Cores: ${cores || 'N/A'}`,
          `Guide Email: ${guideEmail || 'N/A'}`
        ].join('\n');

        const payload = { project_title, description, purpose, guide_email: guideEmail,
          fields, package: pkg, dataset_status: datasetStatus, dataset_size: datasetSize, data_type: types, cores,
          agree: form.querySelector('#agree')?.checked || false
        };

        // Check if we're editing or creating
        const isEditing = window.editingRequestId;
        
        if (isEditing) {
          // Show review modal for update
          showReviewModal(payload, fields, types, pkg, datasetStatus, datasetSize, cores, true, window.editingRequestId);
        } else {
          // Show review modal for new submission
          showReviewModal(payload, fields, types, pkg, datasetStatus, datasetSize, cores, false);
        }
      } else {
        alert('Please fill in all required fields before submitting.');
      }
    });
  }

  // Add hover effects to cards (defensive)
  document.querySelectorAll('.stat-card, .card').forEach(card => {
    card.addEventListener('mouseenter', function() {
      this.style.transform = 'translateY(-5px)';
    });
    card.addEventListener('mouseleave', function() {
      this.style.transform = 'translateY(0)';
    });
  });
  
  // Also try to load dashboard after a short delay as fallback
  setTimeout(loadUserDashboard, 1000);
  
  // Listen for admin-side approval updates to refresh user view
  window.addEventListener('storage', function(e){
    if(e && e.key === 'dashboardRefresh'){
      try { loadRequestsTable(); } catch(_) {}
      // Refresh workflow timeline if a modal is open for a specific request
      if (window.currentModalRequestId) {
        try { refreshWorkflowTimeline(window.currentModalRequestId); } catch(_) {}
      }
    }
  });
});

function toggleProfileDropdown() {
  const dropdown = document.getElementById('profile-dropdown');
  if (dropdown) {
    dropdown.classList.toggle('show');
  }
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
  const dropdown = document.getElementById('profile-dropdown');
  const profileBtn = document.getElementById('user-avatar');
  if (dropdown && profileBtn && !profileBtn.contains(event.target) && !dropdown.contains(event.target)) {
    dropdown.classList.remove('show');
  }
});

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
function handleReturn() {
  window.location.href = "college-dashboard.html#project-forms";
}

function loadRequestsTable() {
  const tbody = document.getElementById('requests-table-body');
  if (!tbody) return;

  fetch('/user/requests', { credentials: 'include' })
    .then(async r=>{
      if (r.status === 401 || r.status === 302) {
        const next = encodeURIComponent('/user_dash.html');
        window.location.href = `/college-login-system.html?next=${next}`;
        return Promise.reject('unauth');
      }
      return r;
    })
    .then(r => r.json())
    .then(({success, data}) => {
      if (!success || !data) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: #666;">No requests found</td></tr>';
        return;
      }

      const requests = data.requests || [];
      if (requests.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: #666;">No requests found</td></tr>';
        return;
      }

      tbody.innerHTML = '';
      requests.forEach(req => {
        const row = document.createElement('tr');
        const statusClass = req.status.toLowerCase().replace('_', '-');
        const statusText = req.status.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase());
        const submittedDate = new Date(req.submitted_at).toLocaleDateString();
        
        row.innerHTML = `
          <td><strong>#REQ-${req.id.toString().padStart(6, '0')}</strong></td>
          <td>${req.project_title}</td>
          <td>${submittedDate}</td>
          <td><span class="status-badge ${statusClass}">${statusText}</span></td>
          <td>${req.priority.charAt(0).toUpperCase() + req.priority.slice(1)}</td>
          <td>
            <div style="display:flex;gap:8px;flex-wrap:wrap;">
              <button class="action-button" onclick="viewRequestDetails(${req.id})" title="View request details">Details</button>
              ${req.status === 'pending' ? `
                <button class="action-button" style="background:#007bff;" onclick="editRequest(${req.id})" title="Edit request">Edit</button>
                <button class="action-button" style="background:#dc3545;" onclick="deleteRequest(${req.id})" title="Cancel request">Delete</button>
              ` : ''}
            </div>
          </td>
        `;
        tbody.appendChild(row);
      });
    })
    .catch(err => {
      console.error('Error loading requests:', err);
      tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: #666;">Error loading requests</td></tr>';
    });
}

function viewRequestDetails(requestId) {
  // Show loading state
  const modal = document.getElementById('requestDetailsModal');
  const content = document.getElementById('requestDetailsContent');
  const title = document.getElementById('modalRequestTitle');
  
  title.textContent = 'Loading Request Details...';
  content.innerHTML = '<div style="text-align: center; padding: 40px;"><div style="display: inline-block; width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid #1e3c72; border-radius: 50%; animation: spin 1s linear infinite;"></div><p style="margin-top: 20px; color: #666;">Loading request details...</p></div>';
  modal.style.display = 'flex';
  
  // Add spin animation
  const style = document.createElement('style');
  style.textContent = '@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }';
  document.head.appendChild(style);
  
  // Fetch request details
  fetch(`/user/requests/${requestId}`)
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        displayRequestDetails(data.data.request);
        // Track current modal request and start live workflow refresh
        window.currentModalRequestId = requestId;
        startWorkflowAutoRefresh(requestId);
      } else {
        content.innerHTML = '<div style="text-align: center; padding: 40px; color: #e74c3c;"><h3>Error Loading Details</h3><p>' + (data.message || 'Failed to load request details') + '</p></div>';
      }
    })
    .catch(error => {
      console.error('Error fetching request details:', error);
      content.innerHTML = '<div style="text-align: center; padding: 40px; color: #e74c3c;"><h3>Error Loading Details</h3><p>Failed to load request details. Please try again.</p></div>';
    });
}

function displayRequestDetails(request) {
  const title = document.getElementById('modalRequestTitle');
  const content = document.getElementById('requestDetailsContent');
  
  title.textContent = `Request #REQ-${request.id.toString().padStart(6, '0')}`;
  
  // Parse form data from description
  const formData = parseFormDataFromDescription(request.description);
  
  // Format dates
  const submittedDate = new Date(request.submitted_at).toLocaleString();
  const approvedDate = request.approved_at ? new Date(request.approved_at).toLocaleString() : 'N/A';
  const rejectedDate = request.rejected_at ? new Date(request.rejected_at).toLocaleString() : 'N/A';
  
  // Get status badge class
  const statusClass = request.status.toLowerCase().replace('_', '-');
  const statusText = request.status.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase());
  
  content.innerHTML = `
    <div class="request-detail-section">
      <h3>Basic Information</h3>
      <div class="detail-row">
        <div class="detail-label">Request ID:</div>
        <div class="detail-value">#REQ-${request.id.toString().padStart(6, '0')}</div>
      </div>
      <div class="detail-row">
        <div class="detail-label">Project Title:</div>
        <div class="detail-value">${request.project_title}</div>
      </div>
      <div class="detail-row">
        <div class="detail-label">Purpose:</div>
        <div class="detail-value">${request.purpose}</div>
      </div>
      <div class="detail-row">
        <div class="detail-label">Priority:</div>
        <div class="detail-value">${request.priority.charAt(0).toUpperCase() + request.priority.slice(1)}</div>
      </div>
      <div class="detail-row">
        <div class="detail-label">Status:</div>
        <div class="detail-value"><span class="status-badge status-${statusClass}">${statusText}</span></div>
      </div>
      <div class="detail-row">
        <div class="detail-label">Submitted:</div>
        <div class="detail-value">${submittedDate}</div>
      </div>
      ${request.approved_at ? `
      <div class="detail-row">
        <div class="detail-label">Approved:</div>
        <div class="detail-value">${approvedDate}</div>
      </div>
      ` : ''}
      ${request.rejected_at ? `
      <div class="detail-row">
        <div class="detail-label">Rejected:</div>
        <div class="detail-value">${rejectedDate}</div>
      </div>
      ` : ''}
      ${request.rejection_reason ? `
      <div class="detail-row">
        <div class="detail-label">Rejection Reason:</div>
        <div class="detail-value">${request.rejection_reason}</div>
      </div>
      ` : ''}
    </div>
    
    <div class="request-detail-section">
      <h3>Project Description</h3>
      <div class="detail-row">
        <div class="detail-value" style="white-space: pre-wrap; background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #1e3c72;">${request.description}</div>
      </div>
    </div>
    
    <div class="request-detail-section" id="workflowSection">
      <h3>Workflow Progress</h3>
      <div id="workflowSteps" style="display:flex;align-items:center;gap:14px;position:relative;flex-wrap:wrap;">
        <!-- Workflow steps will be dynamically generated based on user role -->
        <div style="padding:20px;color:#999;">Loading workflow...</div>
      </div>
      <div id="workflowMeta" style="margin-top:10px;color:#666;font-size:12px;"></div>
    </div>
    
    ${formData && Object.keys(formData).length > 0 ? `
    <div class="request-detail-section">
      <h3>Form Submission Details</h3>
      <div class="form-data-grid">
        ${Object.entries(formData).map(([key, value]) => `
          <div class="form-data-item">
            <h4>${key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</h4>
            <p>${Array.isArray(value) ? value.join(', ') : value}</p>
          </div>
        `).join('')}
      </div>
    </div>
    ` : ''}
  `;

  // Minimal styles for workflow
  (function ensureWorkflowStyles(){
    if(document.getElementById('wf-styles')) return;
    const s=document.createElement('style');
    s.id='wf-styles';
    s.textContent = `
      .wf-step{display:flex;flex-direction:column;align-items:center;min-width:90px;text-align:center}
      .wf-badge{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;background:#6c757d}
      .wf-label{margin-top:6px;font-size:12px;color:#555}
      .wf-line{width:40px;height:2px;background:#e1e5e9}
      .wf-completed .wf-badge{background:#28a745}
      .wf-current .wf-badge{background:#007bff}
      .wf-rejected .wf-badge{background:#dc3545}
    `;
    document.head.appendChild(s);
  })();

  // Fetch workflow and update steps
  refreshWorkflowTimeline(request.id);
}

// Update workflow steps in the modal based on backend workflow data
function refreshWorkflowTimeline(requestId){
  fetch(`/approvals/workflow/${requestId}`)
    .then(r=>r.json())
    .then(({success,data})=>{
      if(!success||!data) return;
      const steps = data.workflow || [];
      const container = document.getElementById('workflowSteps');
      if(!container) return;
      
      // Step labels mapping
      const stepLabels = {
        'submitted': 'Submitted',
        'guide_approval': 'Project Guide',
        'hod_approval': 'HOD',
        'it_services_approval': 'IT Services',
        'final_approval': 'Final Approval'
      };
      
      // Build workflow dynamically based on backend data
      container.innerHTML = '';
      steps.forEach((step, index) => {
        // Add step
        const stepDiv = document.createElement('div');
        stepDiv.className = 'wf-step';
        stepDiv.setAttribute('data-step', step.step);
        
        // Determine status class
        let statusClass = 'wf-pending';
        if(step.status === 'completed') statusClass = 'wf-completed';
        else if(step.status === 'pending') statusClass = 'wf-current';
        else if(step.status === 'rejected') statusClass = 'wf-rejected';
        stepDiv.classList.add(statusClass);
        
        // Build step HTML
        stepDiv.innerHTML = `
          <span class="wf-badge">${index + 1}</span>
          <div class="wf-label">${stepLabels[step.step] || step.step}</div>
        `;
        
        container.appendChild(stepDiv);
        
        // Add connector line (except after last step)
        if(index < steps.length - 1) {
          const line = document.createElement('div');
          line.className = 'wf-line';
          container.appendChild(line);
        }
      });
      
      const meta=document.getElementById('workflowMeta');
      if(meta){ meta.textContent = `Current status: ${data.current_status}`; }
    })
    .catch(()=>{
      // On error, show error message
      const container = document.getElementById('workflowSteps');
      if(container) {
        container.innerHTML = '<div style="padding:20px;color:#c33;">Failed to load workflow</div>';
      }
    });
}

// Auto-refresh workflow periodically while modal is open
let workflowRefreshTimer = null;
function startWorkflowAutoRefresh(requestId){
  try { stopWorkflowAutoRefresh(); } catch(_) {}
  workflowRefreshTimer = setInterval(function(){
    refreshWorkflowTimeline(requestId);
  }, 15000); // refresh every 15s
}
function stopWorkflowAutoRefresh(){
  if (workflowRefreshTimer) {
    clearInterval(workflowRefreshTimer);
    workflowRefreshTimer = null;
  }
}

function parseFormDataFromDescription(description) {
  // Parse the additional information from the description
  const formData = {};
  
  // Look for the "Additional Information:" section
  const additionalInfoMatch = description.match(/Additional Information:\n(.*)/s);
  if (additionalInfoMatch) {
    const additionalInfo = additionalInfoMatch[1];
    
    // Parse each line
    const lines = additionalInfo.split('\n').filter(line => line.trim());
    
    lines.forEach(line => {
      if (line.includes(':')) {
        const [key, value] = line.split(':', 2);
        const cleanKey = key.trim().toLowerCase().replace(/\s+/g, '_');
        const cleanValue = value.trim();
        
        if (cleanValue && cleanValue !== 'N/A') {
          // Handle array values (comma-separated)
          if (cleanValue.includes(',')) {
            formData[cleanKey] = cleanValue.split(',').map(item => item.trim());
          } else {
            formData[cleanKey] = cleanValue;
          }
        }
      }
    });
  }
  
  return formData;
}

function closeRequestDetailsModal() {
  document.getElementById('requestDetailsModal').style.display = 'none';
  // Clear workflow refresh state
  stopWorkflowAutoRefresh();
  window.currentModalRequestId = null;
}

// Edit request functionality (make it globally accessible)
window.editRequest = function(requestId) {
  console.log('Edit button clicked for request:', requestId);
  
  if (!requestId) {
    console.error('No request ID provided');
    alert('Error: No request ID');
    return;
  }
  
  console.log('Navigating to:', `/dashboard?edit=${requestId}`);
  
  // Navigate to dashboard with edit parameter
  window.location.href = `/dashboard?edit=${requestId}`;
};

// Load request data for editing
function loadRequestForEdit(requestId) {
  console.log('Loading request for edit:', requestId);
  
  // Store editing state
  window.editingRequestId = requestId;
  
  // Show loading message
  showToast('Loading request data...', 'info');
  
  // Fetch request data
  fetch(`/projects/${requestId}`)
    .then(r => {
      console.log('Fetch response status:', r.status);
      if (!r.ok) {
        throw new Error(`HTTP ${r.status}: ${r.statusText}`);
      }
      return r.json();
    })
    .then(({success, data}) => {
      console.log('Response data:', {success, data});
      
      if (!success || !data) {
        showToast('Failed to load request data', 'error');
        return;
      }
      
      console.log('Request data loaded successfully:', data);
      
      // Parse form data from description
      const formData = parseFormDataFromDescription(data.description || '');
      console.log('Parsed form data:', formData);
      
      // Wait for form to be available, then populate
      const waitForForm = setInterval(() => {
        const form = document.getElementById('metisRequisitionForm');
        if (form) {
          clearInterval(waitForForm);
          console.log('Form found, populating...');
          
          populateFormWithData(data, formData);
          
          // Show notification
          showToast('Editing request #REQ-' + requestId.toString().padStart(6, '0'), 'success');
          
          // Update submit button text
          const submitBtn = form.querySelector('button[type="submit"]');
          if (submitBtn) {
            submitBtn.textContent = 'Update Request';
            submitBtn.style.background = 'linear-gradient(135deg, #f39c12 0%, #e67e22 100%)';
          }
        }
      }, 100);
      
      // Timeout after 5 seconds
      setTimeout(() => {
        clearInterval(waitForForm);
        const form = document.getElementById('metisRequisitionForm');
        if (!form) {
          console.error('Form not found after 5 seconds');
          showToast('Form not found. Please try again.', 'error');
        }
      }, 5000);
    })
    .catch(err => {
      console.error('Error loading request:', err);
      showToast('Error: ' + err.message, 'error');
    });
}

// Populate form with existing data
function populateFormWithData(requestData, formData) {
  const form = document.getElementById('metisRequisitionForm');
  if (!form) {
    console.error('❌ Form not found with ID: metisRequisitionForm');
    return;
  }
  
  console.log('✅ Form found, starting population...');
  console.log('Form data to populate:', formData);
  console.log('Request data:', requestData);
  
  // Populate checkboxes for fields of interest
  console.log('Populating fields of interest:', formData.fields_of_interest);
  if (formData.fields_of_interest) {
    const fields = Array.isArray(formData.fields_of_interest) 
      ? formData.fields_of_interest 
      : formData.fields_of_interest.split(',').map(f => f.trim());
    
    console.log('Fields array:', fields);
    fields.forEach(field => {
      const checkbox = form.querySelector(`input[name="fields"][value="${field}"]`);
      console.log(`Looking for field "${field}":`, checkbox ? '✅ Found' : '❌ Not found');
      if (checkbox) {
        checkbox.checked = true;
        console.log(`Checked field: ${field}`);
      }
    });
  }
  
  // Populate package preference
  console.log('Populating package preference:', formData.package_preference);
  if (formData.package_preference) {
    const packageRadio = form.querySelector(`input[name="package"][value="${formData.package_preference}"]`);
    console.log('Package radio found:', packageRadio ? '✅' : '❌');
    if (packageRadio) {
      packageRadio.checked = true;
      console.log('Checked package:', formData.package_preference);
    }
  }
  
  // Populate dataset status
  console.log('Populating dataset status:', formData.dataset_status);
  if (formData.dataset_status) {
    const datasetRadio = form.querySelector(`input[name="dataset-status"][value="${formData.dataset_status}"]`);
    console.log('Dataset status radio found:', datasetRadio ? '✅' : '❌');
    if (datasetRadio) {
      datasetRadio.checked = true;
      console.log('Checked dataset status:', formData.dataset_status);
    }
  }
  
  // Populate dataset size
  console.log('Populating dataset size:', formData.dataset_size);
  if (formData.dataset_size) {
    const sizeRadio = form.querySelector(`input[name="dataset-size"][value="${formData.dataset_size}"]`);
    console.log('Dataset size radio found:', sizeRadio ? '✅' : '❌');
    if (sizeRadio) {
      sizeRadio.checked = true;
      console.log('Checked dataset size:', formData.dataset_size);
    }
  }
  
  // Populate data types
  console.log('Populating data types:', formData.data_types);
  if (formData.data_types) {
    const types = Array.isArray(formData.data_types) 
      ? formData.data_types 
      : formData.data_types.split(',').map(t => t.trim());
    
    console.log('Types array:', types);
    types.forEach(type => {
      const checkbox = form.querySelector(`input[name="data-type"][value="${type}"]`);
      console.log(`Looking for type "${type}":`, checkbox ? '✅ Found' : '❌ Not found');
      if (checkbox) {
        checkbox.checked = true;
        console.log(`Checked type: ${type}`);
      }
    });
  }
  
  // Populate computational requirements
  console.log('Populating computational requirements:', formData.computational_requirements);
  if (formData.computational_requirements) {
    const coresRadio = form.querySelector(`input[name="cores"][value="${formData.computational_requirements}"]`);
    console.log('Cores radio found:', coresRadio ? '✅' : '❌');
    if (coresRadio) {
      coresRadio.checked = true;
      console.log('Checked cores:', formData.computational_requirements);
    }
  }
  
  console.log('✅ Form population completed!');
  
  // Scroll to form
  form.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Delete request functionality (make it globally accessible)
window.deleteRequest = function(requestId) {
  // Show confirmation dialog
  const confirmModal = document.createElement('div');
  confirmModal.id = 'delete-confirm-modal';
  confirmModal.style.cssText = `
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
  
  const confirmContent = document.createElement('div');
  confirmContent.style.cssText = `
    background: white;
    border-radius: 12px;
    padding: 30px;
    max-width: 400px;
    width: 90%;
    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    animation: slideIn 0.3s ease;
  `;
  
  confirmContent.innerHTML = `
    <h2 style="margin: 0 0 15px 0; color: #1e3c72; font-size: 24px;">Confirm Deletion</h2>
    <p style="margin: 0 0 25px 0; color: #666; line-height: 1.6;">
      Are you sure you want to cancel this request? This action cannot be undone.
    </p>
    <div style="display: flex; gap: 10px; justify-content: flex-end;">
      <button id="cancel-delete" style="
        padding: 10px 24px;
        background: #6c757d;
        color: white;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 600;
        transition: all 0.2s;
      ">Cancel</button>
      <button id="confirm-delete" style="
        padding: 10px 24px;
        background: #dc3545;
        color: white;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 600;
        transition: all 0.2s;
      ">Delete Request</button>
    </div>
  `;
  
  confirmModal.appendChild(confirmContent);
  document.body.appendChild(confirmModal);
  
  // Add hover effects
  const cancelBtn = confirmContent.querySelector('#cancel-delete');
  const deleteBtn = confirmContent.querySelector('#confirm-delete');
  
  cancelBtn.addEventListener('mouseenter', () => {
    cancelBtn.style.background = '#5a6268';
  });
  cancelBtn.addEventListener('mouseleave', () => {
    cancelBtn.style.background = '#6c757d';
  });
  
  deleteBtn.addEventListener('mouseenter', () => {
    deleteBtn.style.background = '#c82333';
  });
  deleteBtn.addEventListener('mouseleave', () => {
    deleteBtn.style.background = '#dc3545';
  });
  
  // Handle cancel
  cancelBtn.onclick = () => {
    confirmModal.remove();
  };
  
  // Handle delete
  deleteBtn.onclick = async () => {
    deleteBtn.disabled = true;
    deleteBtn.textContent = 'Deleting...';
    
    try {
      const response = await fetch(`/projects/${requestId}/cancel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();
      
      if (response.ok && data.success) {
        showToast('Request cancelled successfully', 'success');
        confirmModal.remove();
        // Refresh the requests table
        loadRequestsTable();
      } else {
        showToast(data.message || 'Failed to cancel request', 'error');
        deleteBtn.disabled = false;
        deleteBtn.textContent = 'Delete Request';
      }
    } catch (error) {
      console.error('Error cancelling request:', error);
      showToast('Error cancelling request', 'error');
      deleteBtn.disabled = false;
      deleteBtn.textContent = 'Delete Request';
    }
  };
};

// Review before submit modal
function showReviewModal(payload, fields, types, pkg, datasetStatus, datasetSize, cores, isEditing = false, requestId = null) {
  const reviewModal = document.createElement('div');
  reviewModal.id = 'review-modal';
  reviewModal.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
    animation: fadeIn 0.3s ease;
    overflow-y: auto;
  `;
  
  const reviewContent = document.createElement('div');
  reviewContent.style.cssText = `
    background: white;
    border-radius: 16px;
    padding: 40px;
    max-width: 700px;
    width: 90%;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    animation: slideIn 0.3s ease;
  `;
  
  reviewContent.innerHTML = `
    <div style="text-align: center; margin-bottom: 30px;">
      <div style="
        width: 80px;
        height: 80px;
        margin: 0 auto 20px;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 36px;
        color: white;
      ">📋</div>
      <h2 style="margin: 0 0 10px 0; color: #1e3c72; font-size: 28px; font-weight: 700;">${isEditing ? 'Review Your Changes' : 'Review Your Request'}</h2>
      <p style="margin: 0; color: #666; font-size: 14px;">${isEditing ? 'Please review your changes before updating' : 'Please review all the details before submitting'}</p>
    </div>
    
    <div style="background: #f8f9fa; border-radius: 12px; padding: 25px; margin-bottom: 25px;">
      <h3 style="margin: 0 0 20px 0; color: #1e3c72; font-size: 18px; font-weight: 600; display: flex; align-items: center; gap: 10px;">
        <span>📝</span> Request Details
      </h3>
      
      <div style="display: grid; gap: 15px;">
        <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #1e3c72;">
          <div style="font-size: 12px; color: #666; font-weight: 600; margin-bottom: 5px;">TITLE</div>
          <div style="color: #333; font-weight: 500;">${payload.project_title}</div>
        </div>
        
        <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #2a5298;">
          <div style="font-size: 12px; color: #666; font-weight: 600; margin-bottom: 5px;">FIELDS OF INTEREST</div>
          <div style="color: #333; font-weight: 500;">${fields.length > 0 ? fields.join(', ') : 'Not specified'}</div>
        </div>
        
        <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #3a6db8;">
          <div style="font-size: 12px; color: #666; font-weight: 600; margin-bottom: 5px;">PACKAGE PREFERENCE</div>
          <div style="color: #333; font-weight: 500;">${pkg || 'Not specified'}</div>
        </div>
        
        <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #4a7dc8;">
          <div style="font-size: 12px; color: #666; font-weight: 600; margin-bottom: 5px;">DATASET STATUS</div>
          <div style="color: #333; font-weight: 500;">${datasetStatus || 'Not specified'}</div>
        </div>
        
        <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #5a8dd8;">
          <div style="font-size: 12px; color: #666; font-weight: 600; margin-bottom: 5px;">DATASET SIZE</div>
          <div style="color: #333; font-weight: 500;">${datasetSize || 'Not specified'}</div>
        </div>
        
        <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #6a9de8;">
          <div style="font-size: 12px; color: #666; font-weight: 600; margin-bottom: 5px;">DATA TYPES</div>
          <div style="color: #333; font-weight: 500;">${types.length > 0 ? types.join(', ') : 'Not specified'}</div>
        </div>
        
        <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #7aadf8;">
          <div style="font-size: 12px; color: #666; font-weight: 600; margin-bottom: 5px;">COMPUTATIONAL REQUIREMENTS</div>
          <div style="color: #333; font-weight: 500;">${cores || 'Not specified'}</div>
        </div>
      </div>
    </div>
    
    <div style="background: #fff3cd; border: 2px solid #ffc107; border-radius: 8px; padding: 15px; margin-bottom: 25px; display: flex; align-items: start; gap: 12px;">
      <span style="font-size: 24px;">⚠️</span>
      <div>
        <div style="font-weight: 600; color: #856404; margin-bottom: 5px;">Important</div>
        <div style="color: #856404; font-size: 14px; line-height: 1.5;">
          Once submitted, your request will enter the approval workflow. Make sure all information is accurate.
        </div>
      </div>
    </div>
    
    <div style="display: flex; gap: 12px; justify-content: flex-end;">
      <button id="cancel-review" style="
        padding: 12px 28px;
        background: #6c757d;
        color: white;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
        font-size: 15px;
        transition: all 0.2s;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      ">Go Back & Edit</button>
      <button id="confirm-review" style="
        padding: 12px 28px;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
        font-size: 15px;
        transition: all 0.2s;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
      ">${isEditing ? 'Update Request' : 'Confirm & Submit'}</button>
    </div>
  `;
  
  reviewModal.appendChild(reviewContent);
  document.body.appendChild(reviewModal);
  
  // Add hover effects
  const cancelBtn = reviewContent.querySelector('#cancel-review');
  const confirmBtn = reviewContent.querySelector('#confirm-review');
  
  cancelBtn.addEventListener('mouseenter', () => {
    cancelBtn.style.background = '#5a6268';
    cancelBtn.style.transform = 'translateY(-2px)';
  });
  cancelBtn.addEventListener('mouseleave', () => {
    cancelBtn.style.background = '#6c757d';
    cancelBtn.style.transform = 'translateY(0)';
  });
  
  confirmBtn.addEventListener('mouseenter', () => {
    confirmBtn.style.transform = 'translateY(-2px)';
    confirmBtn.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)';
  });
  confirmBtn.addEventListener('mouseleave', () => {
    confirmBtn.style.transform = 'translateY(0)';
    confirmBtn.style.boxShadow = '0 2px 8px rgba(0,0,0,0.2)';
  });
  
  // Handle cancel
  cancelBtn.onclick = () => {
    reviewModal.remove();
  };
  
  // Handle confirm and submit
  confirmBtn.onclick = async () => {
    confirmBtn.disabled = true;
    confirmBtn.innerHTML = `<span style="display:inline-block;width:16px;height:16px;border:2px solid white;border-top-color:transparent;border-radius:50%;animation:spin 0.6s linear infinite;"></span> ${isEditing ? 'Updating...' : 'Submitting...'}`;
    
    try {
      // Determine URL and method based on edit mode
      const url = isEditing ? `/projects/${requestId}/update` : '/projects/submit';
      const method = isEditing ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      const data = await response.json().catch(()=>({}));
      
      if (response.ok && data.success) {
        reviewModal.remove();
        showToast(isEditing ? 'Request updated successfully!' : 'Request submitted successfully!', 'success');
        
        // Clear editing state
        if (isEditing) {
          window.editingRequestId = null;
          // Clear URL parameter
          const url = new URL(window.location);
          url.searchParams.delete('edit');
          window.history.replaceState({}, '', url);
        }
        
        // Reset form
        document.getElementById('metisRequisitionForm')?.reset();
        
        // Reset submit button
        const form = document.getElementById('metisRequisitionForm');
        const submitBtn = form?.querySelector('button[type="submit"]');
        if (submitBtn) {
          submitBtn.textContent = 'Submit Request';
          submitBtn.style.background = 'linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)';
        }
        
        // Navigate to requests page
        setTimeout(() => navigateToPage('requests'), 1000);
      } else {
        showToast(data.message || (isEditing ? 'Update failed' : 'Submission failed'), 'error');
        confirmBtn.disabled = false;
        confirmBtn.textContent = isEditing ? 'Update Request' : 'Confirm & Submit';
      }
    } catch (error) {
      console.error('Error submitting request:', error);
      showToast('Network error', 'error');
      confirmBtn.disabled = false;
      confirmBtn.textContent = isEditing ? 'Update Request' : 'Confirm & Submit';
    }
  };
  
  // Add spinning animation
  if (!document.getElementById('spin-animation')) {
    const style = document.createElement('style');
    style.id = 'spin-animation';
    style.textContent = `
      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
    `;
    document.head.appendChild(style);
  }
}

// Activities functionality
function loadActivities() {
  const activitiesContainer = document.getElementById('all-activities');
  if (!activitiesContainer) return;
  
  // Show loading state
  activitiesContainer.innerHTML = `
    <div class="loading-activities" style="text-align: center; padding: 40px;">
      <div style="display: inline-block; width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid #1e3c72; border-radius: 50%; animation: spin 1s linear infinite;"></div>
      <p style="margin-top: 20px; color: #666;">Loading activities...</p>
    </div>
  `;
  
  // Add spin animation
  const style = document.createElement('style');
  style.textContent = '@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }';
  document.head.appendChild(style);
  
  // Fetch activities
  fetch('/user/activities', { credentials: 'include' })
    .then(async r=>{
      if (r.status === 401 || r.status === 302) {
        const next = encodeURIComponent('/user_dash.html');
        window.location.href = `/college-login-system.html?next=${next}`;
        return Promise.reject('unauth');
      }
      return r;
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        displayActivities(data.data.activities);
      } else {
        activitiesContainer.innerHTML = `
          <div style="text-align: center; padding: 40px; color: #e74c3c;">
            <h3>Error Loading Activities</h3>
            <p>${data.message || 'Failed to load activities'}</p>
          </div>
        `;
      }
    })
    .catch(error => {
      console.error('Error fetching activities:', error);
      activitiesContainer.innerHTML = `
        <div style="text-align: center; padding: 40px; color: #e74c3c;">
          <h3>Error Loading Activities</h3>
          <p>Failed to load activities. Please try again.</p>
        </div>
      `;
    });
}

function displayActivities(activities) {
  const activitiesContainer = document.getElementById('all-activities');
  if (!activitiesContainer) return;
  
  if (activities.length === 0) {
    activitiesContainer.innerHTML = `
      <div style="text-align: center; padding: 40px; color: #666;">
        <div style="font-size: 48px; margin-bottom: 20px;">📋</div>
        <h3>No Activities Yet</h3>
        <p>You haven't submitted any requests yet. Start by submitting your first request!</p>
        <button class="btn btn-primary" onclick="navigateToPage('submit')" style="margin-top: 20px;">Submit Request</button>
      </div>
    `;
    return;
  }
  
  // Group activities by date
  const groupedActivities = groupActivitiesByDate(activities);
  
  let html = '';
  Object.keys(groupedActivities).forEach(date => {
    const dayActivities = groupedActivities[date];
    html += `
      <div class="activity-date-group">
        <div class="activity-date-header">${date}</div>
        <div class="activity-date-list">
          ${dayActivities.map(activity => createActivityItem(activity)).join('')}
        </div>
      </div>
    `;
  });
  
  activitiesContainer.innerHTML = html;
}

function groupActivitiesByDate(activities) {
  const grouped = {};
  
  activities.forEach(activity => {
    const date = new Date(activity.timestamp);
    const dateStr = date.toLocaleDateString('en-US', { 
      weekday: 'long', 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
    
    if (!grouped[dateStr]) {
      grouped[dateStr] = [];
    }
    grouped[dateStr].push(activity);
  });
  
  return grouped;
}

function createActivityItem(activity) {
  const time = new Date(activity.timestamp).toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit' 
  });
  
  const colorClass = getActivityColorClass(activity.color);
  const borderColor = getActivityBorderColor(activity.color);
  
  return `
    <div class="activity-item ${colorClass}" style="border-left: 3px solid ${borderColor}; background: ${getActivityBackgroundColor(activity.color)};" onclick="viewActivityDetails('${activity.type}', ${activity.request_id})">
      <div class="activity-icon ${colorClass}">${activity.icon}</div>
      <div class="activity-details">
        <div class="activity-title">${activity.title}</div>
        <div class="activity-description">${activity.description}</div>
        <div class="activity-time">${time}</div>
      </div>
      <div class="activity-status">
        <span class="status-badge status-${activity.status.replace('_', '-')}">${activity.status.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}</span>
      </div>
    </div>
  `;
}

function getActivityColorClass(color) {
  const colorMap = {
    'blue': 'info',
    'green': 'success',
    'red': 'error',
    'yellow': 'warning',
    'purple': 'primary'
  };
  return colorMap[color] || 'info';
}

function getActivityBorderColor(color) {
  const colorMap = {
    'blue': '#3b82f6',
    'green': '#10b981',
    'red': '#ef4444',
    'yellow': '#f59e0b',
    'purple': '#8b5cf6'
  };
  return colorMap[color] || '#3b82f6';
}

function getActivityBackgroundColor(color) {
  const colorMap = {
    'blue': 'rgba(59, 130, 246, 0.05)',
    'green': 'rgba(16, 185, 129, 0.05)',
    'red': 'rgba(239, 68, 68, 0.05)',
    'yellow': 'rgba(245, 158, 11, 0.05)',
    'purple': 'rgba(139, 92, 246, 0.05)'
  };
  return colorMap[color] || 'rgba(59, 130, 246, 0.05)';
}

// IMMEDIATELY hide modal and block opening - runs as soon as script loads
(function() {
  // Hide modal immediately if it exists
  setTimeout(() => {
    const modal = document.getElementById('password-modal');
    if (modal) {
      modal.style.display = 'none !important';
      modal.classList.remove('show');
      console.log('Modal force hidden immediately');
    }
  }, 1);
})();

// PERMANENTLY block any modal opening
function openPasswordModal() {
  console.log('openPasswordModal called - PERMANENTLY BLOCKED');
  return false;
}

// Override any existing openPasswordModal function immediately
window.openPasswordModal = function() {
  console.log('Window openPasswordModal called - PERMANENTLY BLOCKED');
  return false;
};

// Real function to open modal
function realOpenPasswordModal() {
  console.log('Manual password modal opening');
  const modal = document.getElementById('password-modal');
  modal.classList.add('show');
  modal.style.display = 'flex !important';
  modal.style.setProperty('display', 'flex', 'important');
  
  // Clear form fields
  document.getElementById('change-password-form').reset();
}

// Close password change modal
function closePasswordModal() {
  const modal = document.getElementById('password-modal');
  modal.classList.remove('show');
  setTimeout(() => {
    modal.style.display = 'none';
  }, 300);
  
  // Clear form
  document.getElementById('change-password-form').reset();
}

// Close modal when clicking outside
window.onclick = function(event) {
  const modal = document.getElementById('password-modal');
  if (event.target === modal) {
    closePasswordModal();
  }
}

// Handle password change
async function handleChangePassword(event) {
  event.preventDefault();
  
  const currentPassword = document.getElementById('current-password').value;
  const newPassword = document.getElementById('new-password').value;
  const confirmPassword = document.getElementById('confirm-password').value;
  
  // Validate new password
  if (newPassword.length < 8) {
    showToast('New password must be at least 8 characters long', 'error');
    return;
  }
  
  // Check if password has uppercase, lowercase, and numbers
  const hasUppercase = /[A-Z]/.test(newPassword);
  const hasLowercase = /[a-z]/.test(newPassword);
  const hasNumber = /[0-9]/.test(newPassword);
  
  if (!hasUppercase) {
    showToast('Password must contain at least one uppercase letter', 'error');
    return;
  }
  
  if (!hasLowercase) {
    showToast('Password must contain at least one lowercase letter', 'error');
    return;
  }
  
  if (!hasNumber) {
    showToast('Password must contain at least one digit', 'error');
    return;
  }
  
  // Check if passwords match
  if (newPassword !== confirmPassword) {
    showToast('New passwords do not match', 'error');
    return;
  }
  
  // Check if new password is different from current
  if (currentPassword === newPassword) {
    showToast('New password must be different from current password', 'error');
    return;
  }
  
  try {
    const response = await fetch('/auth/change-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword
      })
    });
    
    const data = await response.json();
    
    if (response.ok && data.success) {
      showToast('Password changed successfully! Redirecting to login...', 'success');
      
      // Close modal
      closePasswordModal();
      
      // Logout and redirect to login page after 2 seconds
      setTimeout(() => {
        fetch('/auth/logout', { method: 'POST' })
          .then(() => {
            window.location.href = '/college-login-system.html';
          })
          .catch(() => {
            // Fallback if logout fails
            window.location.href = '/college-login-system.html';
          });
      }, 2000);
    } else {
      showToast(data.message || 'Failed to change password', 'error');
    }
  } catch (error) {
    console.error('Error:', error);
    showToast('Network error. Please try again.', 'error');
  }
}

// Toast notification function
function showToast(message, type = 'info') {
  // Create toast element
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
    color: white;
    padding: 15px 20px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 10000;
    animation: slideIn 0.3s ease;
    max-width: 400px;
  `;
  toast.textContent = message;
  
  document.body.appendChild(toast);
  
  // Remove after 4 seconds
  setTimeout(() => {
    toast.style.animation = 'slideOut 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function viewActivityDetails(activityType, requestId) {
  // Navigate to request details
  viewRequestDetails(requestId);
}

function refreshActivities() {
  loadActivities();
}

function downloadNDA() {
  // Implement PDF download functionality
  alert("Downloading NDA Form...");
  // In a real implementation, this would trigger a PDF download
}

// Check if user has temporary password and show prompt
async function checkTempPassword() {
  try {
    const response = await fetch('/user/profile');
    const result = await response.json();
    
    console.log('Password check response:', result);
    console.log('is_temp_password value:', result.data?.is_temp_password);
    console.log('Type:', typeof result.data?.is_temp_password);
    
    if (result.success && result.data && result.data.is_temp_password === true) {
      console.log('User has temporary password - showing reminder banner...');
      // Show notification banner for users with temporary passwords
      setTimeout(() => {
        showPasswordChangeReminder();
      }, 1500);
    } else {
      console.log('User has permanent password - no banner needed');
    }
  } catch (error) {
    console.error('Error checking password status:', error);
  }
}

// Show password change reminder notification
function showPasswordChangeReminder() {
  const reminder = document.createElement('div');
  reminder.id = 'password-reminder';
  reminder.style.cssText = `
    position: fixed;
    top: 80px;
    right: 20px;
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
    color: white;
    padding: 20px 24px;
    border-radius: 12px;
    box-shadow: 0 10px 40px rgba(99, 102, 241, 0.4);
    z-index: 9999;
    max-width: 400px;
    animation: slideIn 0.5s ease;
  `;
  
  reminder.innerHTML = `
    <div style="display: flex; align-items: start; gap: 12px;">
      <span style="font-size: 24px;">🔐</span>
      <div style="flex: 1;">
        <h3 style="margin: 0 0 8px 0; font-size: 16px; font-weight: 600;">Update Your Password</h3>
        <p style="margin: 0 0 12px 0; font-size: 14px; opacity: 0.95;">
          For enhanced security, please change your temporary password to a personalized one.
        </p>
        <div style="display: flex; gap: 10px;">
          <button onclick="realOpenPasswordModal(); document.getElementById('password-reminder').remove();" 
                  style="background: white; color: #4f46e5; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 600; cursor: pointer; font-size: 13px;">
            Change Now
          </button>
          <button onclick="document.getElementById('password-reminder').remove();" 
                  style="background: rgba(255,255,255,0.2); color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 600; cursor: pointer; font-size: 13px;">
            Later
          </button>
        </div>
      </div>
      <button onclick="document.getElementById('password-reminder').remove();" 
              style="background: none; border: none; color: white; font-size: 20px; cursor: pointer; opacity: 0.8; padding: 0; line-height: 1;">
        &times;
      </button>
    </div>
  `;
  
  document.body.appendChild(reminder);
  
  // Auto-dismiss after 15 seconds
  setTimeout(() => {
    const elem = document.getElementById('password-reminder');
    if (elem) {
      elem.style.animation = 'slideOut 0.3s ease';
      setTimeout(() => elem.remove(), 300);
    }
  }, 15000);
}

// Call checkTempPassword when dashboard loads
setTimeout(() => checkTempPassword(), 1000);

// Force close any modal on page load
setTimeout(() => {
  const modal = document.getElementById('password-modal');
  if (modal) {
    modal.style.display = 'none';
    modal.classList.remove('show');
    console.log('Forced modal closed on page load');
  }
  
  const forgotModal = document.getElementById('forgot-password-modal');
  if (forgotModal) {
    forgotModal.style.display = 'none';
    forgotModal.classList.remove('show');
  }
  
  const editModal = document.getElementById('edit-profile-modal');
  if (editModal) {
    editModal.style.display = 'none';
    editModal.classList.remove('show');
  }
}, 100);

// Edit Profile Modal Functions
function openEditProfileModal() {
  console.log('Opening edit profile modal');
  const modal = document.getElementById('edit-profile-modal');
  modal.classList.add('show');
  modal.style.setProperty('display', 'flex', 'important');
  
  // Load current user data into form
  loadCurrentProfileData();
  
}

function closeEditProfileModal() {
  const modal = document.getElementById('edit-profile-modal');
  modal.classList.remove('show');
  setTimeout(() => {
    modal.style.display = 'none';
  }, 300);
}

// Load current profile data into edit form
async function loadCurrentProfileData() {
  try {
    const response = await fetch('/user/profile');
    const result = await response.json();
    
    if (result.success && result.data) {
      const user = result.data;
      
      // Populate form fields
      document.getElementById('edit-first-name').value = user.first_name || '';
      document.getElementById('edit-last-name').value = user.last_name || '';
      document.getElementById('edit-phone').value = user.phone || '';
      // Set department to existing value if present in options; otherwise default to 'Others'
      const deptSelect = document.getElementById('edit-department');
      const userDept = (user.department || '').trim();
      if (deptSelect) {
        const hasOption = Array.from(deptSelect.options).some(opt => opt.value === userDept);
        deptSelect.value = hasOption ? userDept : (userDept ? 'Others' : '');
      }
      
      // External user fields
      if (user.role === 'external') {
        document.getElementById('external-fields').style.display = 'block';
        document.getElementById('edit-profession').value = user.profession || '';
        document.getElementById('edit-institution').value = user.institution || '';
        document.getElementById('edit-address').value = user.address || '';
        document.getElementById('edit-city').value = user.city || '';
        document.getElementById('edit-state').value = user.state || '';
        document.getElementById('edit-pincode').value = user.pincode || '';
      } else {
        document.getElementById('external-fields').style.display = 'none';
      }
      
      // Load profile photo
      loadProfilePhotoPreview(user);
      
    }
  } catch (error) {
    console.error('Error loading profile data:', error);
    showToast('Failed to load profile data', 'error');
  }
}

// Load profile photo preview
function loadProfilePhotoPreview(user) {
  const photoImg = document.getElementById('current-photo-img');
  const photoPlaceholder = document.getElementById('photo-placeholder');
  const photoInitials = document.getElementById('photo-initials');
  const removeBtn = document.getElementById('remove-photo-btn');
  
  if (user.profile_photo) {
    // Show existing photo
    photoImg.src = `/auth/profile-photo/${user.profile_photo}`;
    photoImg.style.display = 'block';
    photoPlaceholder.style.display = 'none';
    removeBtn.style.display = 'inline-block';
  } else {
    // Show initials placeholder
    const initials = ((user.first_name || '')[0] || '') + ((user.last_name || '')[0] || '');
    photoInitials.textContent = initials || 'U';
    photoImg.style.display = 'none';
    photoPlaceholder.style.display = 'flex';
    removeBtn.style.display = 'none';
  }
}

// Preview selected photo
function previewPhoto(event) {
  const file = event.target.files[0];
  if (!file) return;
  
  // Validate file size (5MB max)
  if (file.size > 5 * 1024 * 1024) {
    showToast('Photo size must be less than 5MB', 'error');
    event.target.value = '';
    return;
  }
  
  // Validate file type
  if (!file.type.startsWith('image/')) {
    showToast('Please select a valid image file', 'error');
    event.target.value = '';
    return;
  }
  
  // Preview the image
  const reader = new FileReader();
  reader.onload = function(e) {
    const photoImg = document.getElementById('current-photo-img');
    const photoPlaceholder = document.getElementById('photo-placeholder');
    const removeBtn = document.getElementById('remove-photo-btn');
    
    photoImg.src = e.target.result;
    photoImg.style.display = 'block';
    photoPlaceholder.style.display = 'none';
    removeBtn.style.display = 'inline-block';
  };
  reader.readAsDataURL(file);
}

// Remove photo
function removePhoto() {
  const photoInput = document.getElementById('profile-photo-input');
  const photoImg = document.getElementById('current-photo-img');
  const photoPlaceholder = document.getElementById('photo-placeholder');
  const removeBtn = document.getElementById('remove-photo-btn');
  
  photoInput.value = '';
  photoImg.style.display = 'none';
  photoPlaceholder.style.display = 'flex';
  removeBtn.style.display = 'none';
}

// Simple save function called directly by button click
async function saveProfileChanges() {
  console.log('Save profile changes called');
  
  // Get and disable the save button
  const saveBtn = document.getElementById('save-profile-btn');
  const originalText = saveBtn.innerHTML;
  saveBtn.disabled = true;
  saveBtn.innerHTML = '⏳ Saving...';
  
  try {
    // First test if the route exists
    console.log('Testing route availability...');
    const testResponse = await fetch('/auth/test-route');
    console.log('Test route response:', testResponse.status);
    
    const formData = new FormData();
  
    // Add text fields
    formData.append('first_name', document.getElementById('edit-first-name').value.trim());
    formData.append('last_name', document.getElementById('edit-last-name').value.trim());
    formData.append('phone', document.getElementById('edit-phone').value.trim());
    formData.append('department', document.getElementById('edit-department').value);
  
    // Add external user fields if visible
    const externalFields = document.getElementById('external-fields');
    if (externalFields.style.display !== 'none') {
      formData.append('profession', document.getElementById('edit-profession').value.trim());
      formData.append('institution', document.getElementById('edit-institution').value.trim());
      formData.append('address', document.getElementById('edit-address').value.trim());
      formData.append('city', document.getElementById('edit-city').value.trim());
      formData.append('state', document.getElementById('edit-state').value.trim());
      formData.append('pincode', document.getElementById('edit-pincode').value.trim());
    }
    
    // Add profile photo if selected
    const photoInput = document.getElementById('profile-photo-input');
    if (photoInput.files[0]) {
      formData.append('profile_photo', photoInput.files[0]);
    }
    
    console.log('Sending request to /auth/update-profile');
    console.log('FormData contents:');
    for (let [key, value] of formData.entries()) {
      console.log(key, value);
    }
    
    const response = await fetch('/auth/update-profile', {
      method: 'POST',
      body: formData
    });
    
    console.log('Response status:', response.status);
    const data = await response.json();
    console.log('Response data:', data);
    
    if (response.ok && data.success) {
      showToast('Profile updated successfully!', 'success');
      closeEditProfileModal();
      
      // Reload dashboard to reflect changes
      setTimeout(() => {
        loadUserDashboard();
      }, 1000);
    } else {
      showToast(data.message || 'Failed to update profile', 'error');
    }
  } catch (error) {
    console.error('Error:', error);
    showToast('Network error. Please try again.', 'error');
  } finally {
    // Re-enable save button
    saveBtn.disabled = false;
    saveBtn.innerHTML = originalText;
  }
}

// Forgot Password Modal Functions
function openForgotPasswordModal() {
  console.log('Opening forgot password modal');
  const modal = document.getElementById('forgot-password-modal');
  modal.classList.add('show');
  modal.style.setProperty('display', 'flex', 'important');
  
  // Reset to step 1
  showForgotStep(1);
  
  // Clear all forms
  document.getElementById('forgot-email-form').reset();
  document.getElementById('forgot-otp-form').reset();
  document.getElementById('forgot-reset-form').reset();
}

function closeForgotPasswordModal() {
  const modal = document.getElementById('forgot-password-modal');
  modal.classList.remove('show');
  setTimeout(() => {
    modal.style.display = 'none';
  }, 300);
  
  // Clear timer if running
  if (window.otpTimer) {
    clearInterval(window.otpTimer);
  }
}

function showForgotStep(step) {
  // Hide all steps
  document.getElementById('forgot-step-1').style.display = 'none';
  document.getElementById('forgot-step-2').style.display = 'none';
  document.getElementById('forgot-step-3').style.display = 'none';
  
  // Show current step
  document.getElementById(`forgot-step-${step}`).style.display = 'block';
}

// Handle Send OTP
async function handleSendOTP(event) {
  event.preventDefault();
  
  const email = document.getElementById('forgot-email').value.trim();
  
  if (!email) {
    showToast('Please enter your email address', 'error');
    return;
  }
  
  try {
    const response = await fetch('/auth/forgot-password/send-otp', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email: email })
    });
    
    const data = await response.json();
    
    if (response.ok && data.success) {
      showToast(data.message, 'success');
      showForgotStep(2);
      startOTPTimer();
    } else {
      showToast(data.message || 'Failed to send verification code', 'error');
    }
  } catch (error) {
    console.error('Error:', error);
    showToast('Network error. Please try again.', 'error');
  }
}

// Handle Verify OTP
async function handleVerifyOTP(event) {
  event.preventDefault();
  
  const otp = document.getElementById('forgot-otp').value.trim();
  
  if (!otp || otp.length !== 6) {
    showToast('Please enter the 6-digit verification code', 'error');
    return;
  }
  
  try {
    const response = await fetch('/auth/forgot-password/verify-otp', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ otp: otp })
    });
    
    const data = await response.json();
    
    if (response.ok && data.success) {
      showToast(data.message, 'success');
      showForgotStep(3);
      
      // Clear timer
      if (window.otpTimer) {
        clearInterval(window.otpTimer);
      }
    } else {
      showToast(data.message || 'Invalid verification code', 'error');
    }
  } catch (error) {
    console.error('Error:', error);
    showToast('Network error. Please try again.', 'error');
  }
}

// Handle Reset Password
async function handleResetPassword(event) {
  event.preventDefault();
  
  const newPassword = document.getElementById('forgot-new-password').value;
  const confirmPassword = document.getElementById('forgot-confirm-password').value;
  
  // Validate new password
  if (newPassword.length < 8) {
    showToast('New password must be at least 8 characters long', 'error');
    return;
  }
  
  // Check if password has uppercase, lowercase, and numbers
  const hasUppercase = /[A-Z]/.test(newPassword);
  const hasLowercase = /[a-z]/.test(newPassword);
  const hasNumber = /[0-9]/.test(newPassword);
  
  if (!hasUppercase) {
    showToast('Password must contain at least one uppercase letter', 'error');
    return;
  }
  
  if (!hasLowercase) {
    showToast('Password must contain at least one lowercase letter', 'error');
    return;
  }
  
  if (!hasNumber) {
    showToast('Password must contain at least one digit', 'error');
    return;
  }
  
  // Check if passwords match
  if (newPassword !== confirmPassword) {
    showToast('Passwords do not match', 'error');
    return;
  }
  
  try {
    const response = await fetch('/auth/forgot-password/reset', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ new_password: newPassword })
    });
    
    const data = await response.json();
    
    if (response.ok && data.success) {
      showToast('Password reset successfully! Please login with your new password.', 'success');
      
      // Close modal
      closeForgotPasswordModal();
      
      // Redirect to login after 2 seconds
      setTimeout(() => {
        window.location.href = '/college-login-system.html';
      }, 2000);
    } else {
      showToast(data.message || 'Failed to reset password', 'error');
    }
  } catch (error) {
    console.error('Error:', error);
    showToast('Network error. Please try again.', 'error');
  }
}

// Resend OTP
async function resendOTP() {
  const email = document.getElementById('forgot-email').value.trim();
  
  try {
    const response = await fetch('/auth/forgot-password/send-otp', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email: email })
    });
    
    const data = await response.json();
    
    if (response.ok && data.success) {
      showToast('New verification code sent to your email', 'success');
      startOTPTimer();
      document.getElementById('forgot-otp').value = '';
    } else {
      showToast(data.message || 'Failed to resend code', 'error');
    }
  } catch (error) {
    console.error('Error:', error);
    showToast('Network error. Please try again.', 'error');
  }
}

// Start OTP Timer
function startOTPTimer() {
  let timeLeft = 300; // 5 minutes in seconds
  const timerElement = document.getElementById('otp-timer');
  
  // Clear existing timer
  if (window.otpTimer) {
    clearInterval(window.otpTimer);
  }
  
  window.otpTimer = setInterval(() => {
    const minutes = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;
    timerElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    
    if (timeLeft <= 0) {
      clearInterval(window.otpTimer);
      timerElement.textContent = 'Expired';
      timerElement.style.color = '#ef4444';
    }
    
    timeLeft--;
  }, 1000);
}
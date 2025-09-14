// JavaScript for interactivity
function logout() {
  if (confirm('Are you sure you want to logout?')) {
    alert('Logging out...');
    // Add logout logic here
  }
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

document.addEventListener('DOMContentLoaded', function() {
  // Simulate user data
  const userName = 'John Doe';
  const userInitials = userName.split(' ').map(n => n[0]).join('');

  const userGreeting = document.getElementById('user-greeting');
  if (userGreeting) userGreeting.textContent = userName;

  const welcomeUsername = document.getElementById('welcome-username');
  if (welcomeUsername) welcomeUsername.textContent = userName.split(' ')[0];

  const userAvatar = document.getElementById('user-avatar');
  if (userAvatar) userAvatar.textContent = userInitials;

  const profileAvatar = document.getElementById('profile-avatar');
  if (profileAvatar) profileAvatar.textContent = userInitials;

  const profileName = document.getElementById('profile-name');
  if (profileName) profileName.textContent = userName;

  // Navigation functionality
  const menuItems = Array.from(document.querySelectorAll('.menu-item'));
  const pages = Array.from(document.querySelectorAll('.page-content'));
  const pageTitle = document.getElementById('page-title');

  const pageTitles = {
    'dashboard': 'Dashboard',
    'profile': 'My Profile',
    'requests': 'My Requests',
    'submit': 'Submit Request',
    'analytics': 'Analytics',
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
        const data = {};

        for (let [key, value] of formData.entries()) {
          if (data[key]) {
            if (Array.isArray(data[key])) {
              data[key].push(value);
            } else {
              data[key] = [data[key], value];
            }
          } else {
            data[key] = value;
          }
        }

        console.log('Form submitted with data:', data);
        alert('Requisition form submitted successfully! You will receive a confirmation email shortly.');

        // Generate a fake request ID and redirect to requests page
        const fakeId = '#REQ-' + new Date().getFullYear() + '-' + Math.floor(Math.random() * 900 + 100);
        console.log('Generated Request ID:', fakeId);

        setTimeout(() => {
          navigateToPage('requests');
        }, 1500);
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
});
function handleReturn() {
  window.location.href = "college-dashboard.html#project-forms";
}

function downloadNDA() {
  // Implement PDF download functionality
  alert("Downloading NDA Form...");
  // In a real implementation, this would trigger a PDF download
}
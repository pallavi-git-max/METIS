// Navigation Functions
// Lightweight toast (global)
function showToast(message) {
  let el = document.getElementById('toast');
  if (!el) {
    el = document.createElement('div');
    el.id = 'toast';
    el.style.position = 'fixed';
    el.style.top = '20px';
    el.style.right = '20px';
    el.style.padding = '12px 16px';
    el.style.background = 'rgba(30,60,114,0.95)';
    el.style.color = '#fff';
    el.style.borderRadius = '8px';
    el.style.boxShadow = '0 6px 20px rgba(0,0,0,0.2)';
    el.style.zIndex = '9999';
    el.style.fontWeight = '600';
    document.body.appendChild(el);
  }
  el.textContent = message;
  el.style.opacity = '1';
  setTimeout(() => { el.style.opacity = '0'; }, 2200);
}
function showMainPage() {
  document.querySelectorAll(".form-section").forEach((section) => {
    section.classList.remove("active");
  });
  document.getElementById("main-page").classList.add("active");
}

function showUserSection(userType) {
  document.querySelectorAll(".form-section").forEach((section) => {
    section.classList.remove("active");
  });

  if (userType === "student") {
    document.getElementById("student-section").classList.add("active");
  } else if (userType === "admin") {
    document.getElementById("admin-section").classList.add("active");
  } else {
    document.getElementById("external-section").classList.add("active");
  }
}

// Student/Faculty Selection
function selectUserType(type, formType) {
  const section = formType === 'login' ? 'login' : 'register';
  
  // Update button states
  const buttons = document.querySelectorAll(`#student-${section} .user-select-btn`);
  buttons.forEach(btn => btn.classList.remove('active'));
  event.target.classList.add('active');
  
  // Update registration form fields if in registration mode
  if (formType === 'register') {
    const regNumberGroup = document.getElementById('reg-number-group');
    const regNumberLabel = document.getElementById('reg-number-label');
    const regNumberInput = document.getElementById('student-reg-number');
    const classProgramGroup = document.getElementById('class-program-group');
    const classInput = document.getElementById('student-reg-class');
    if (type === 'faculty') {
      regNumberLabel.textContent = 'Employee ID';
      regNumberInput.placeholder = 'Enter your employee ID';
      if (classProgramGroup) classProgramGroup.style.display = 'none';
      if (classInput) classInput.required = false;
    } else {
      regNumberLabel.textContent = 'Registration Number';
      regNumberInput.placeholder = 'Enter your registration number';
      if (classProgramGroup) classProgramGroup.style.display = 'none';
      if (classInput) classInput.required = false;
    }
  }
}

function showStudentForm(formType) {
  // Update tab states
  document
    .querySelectorAll("#student-section .auth-tab")
    .forEach((tab) => {
      tab.classList.remove("active");
    });
  event.target.classList.add("active");

  // Show appropriate form
  document
    .querySelectorAll("#student-section .form-content")
    .forEach((content) => {
      content.classList.remove("active");
    });

  if (formType === "login") {
    document.getElementById("student-login").classList.add("active");
  } else {
    document.getElementById("student-register").classList.add("active");
    // Reset to student selection by default
    const studentBtn = document.querySelector('#student-register .user-select-btn');
    if (studentBtn) {
      studentBtn.click();
    }
  }
}

function showAdminForm(formType) {
  // Update tab states
  document
    .querySelectorAll("#admin-section .auth-tab")
    .forEach((tab) => {
      tab.classList.remove("active");
    });
  event.target.classList.add("active");

  // Show appropriate form
  document
    .querySelectorAll("#admin-section .form-content")
    .forEach((content) => {
      content.classList.remove("active");
    });

  if (formType === "login") {
    document.getElementById("admin-login").classList.add("active");
  }
}

function showExternalForm(formType) {
  // Update tab states
  document
    .querySelectorAll("#external-section .auth-tab")
    .forEach((tab) => {
      tab.classList.remove("active");
    });
  event.target.classList.add("active");

  // Show appropriate form
  document
    .querySelectorAll("#external-section .form-content")
    .forEach((content) => {
      content.classList.remove("active");
    });

  if (formType === "login") {
    document.getElementById("external-login").classList.add("active");
  } else {
    document.getElementById("external-register").classList.add("active");
  }
}

// Form Handlers
function handleStudentLogin(event) {
  event.preventDefault();

  // Get form data
  const userId = document.getElementById("student-login-id").value;
  const password = document.getElementById("student-login-password").value;
  
  // Check if Student or Faculty is selected
  const userType = document.querySelector('#student-login .user-select-btn.active').textContent.trim().toLowerCase();

  if (!userId || !password) return;

  // Basic validations
  if (userId.includes('@')) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
    if (!emailRegex.test(userId)) { showToast('Enter a valid email'); return; }
  }
  if (password.length < 8) { showToast('Password must be at least 8 characters'); return; }

  // Treat userId as email for backend auth
  fetch('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: userId, password, user_type: userType })
  }).then(async (res) => {
    const data = await res.json().catch(() => ({}));
    if (res.ok && data.success) {
      showToast('Login successful');
      document.getElementById("student-login-success").style.display = "block";
      const redirect = (data.data && data.data.redirect_url) || '/dashboard';
      setTimeout(() => { window.location.href = redirect; }, 800);
    } else {
      showToast(data.message || 'Login failed');
    }
  }).catch(() => showToast('Network error'));
}

function handleAdminLogin(event) {
  event.preventDefault();

  // Get form data
  const userId = document.getElementById("admin-login-id").value;
  const password = document.getElementById("admin-login-password").value;
  if (!userId || !password) return;

  if (userId.includes('@')) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
    if (!emailRegex.test(userId)) { showToast('Enter a valid email'); return; }
  }
  if (password.length < 8) { showToast('Password must be at least 8 characters'); return; }

  fetch('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: userId, password, user_type: 'admin' })
  }).then(async (res) => {
    const data = await res.json().catch(() => ({}));
    if (res.ok && data.success) {
      showToast('Admin login successful');
      document.getElementById("admin-login-success").style.display = "block";
      const redirect = (data.data && data.data.redirect_url) || '/admin/dashboard';
      setTimeout(() => { window.location.href = redirect; }, 800);
    } else {
      showToast(data.message || 'Login failed');
    }
  }).catch(() => showToast('Network error'));
}

function handleStudentRegistration(event) {
  event.preventDefault();

  const fname = document.getElementById("student-reg-fname").value;
  const lname = document.getElementById("student-reg-lname").value;
  const regNumber = document.getElementById("student-reg-number").value;
  const email = document.getElementById("student-reg-email").value;
  const phone = document.getElementById("student-reg-phone").value;
  const department = document.getElementById("student-reg-dep").value;
  const campus = document.getElementById("student-reg-camp").value;
  const photoInput = document.getElementById("student-reg-photo");
  
  // Check if Student or Faculty
  const userType = document.querySelector('#student-register .user-select-btn.active').textContent.trim().toLowerCase();
  
  let isValid = false;
  
  if (userType === 'student') {
    isValid = fname && lname && regNumber && email && phone && department && campus && photoInput.files[0];
  } else {
    isValid = fname && lname && regNumber && email && phone && department && campus && photoInput.files[0];
  }

  if (!isValid) { showToast('Please complete all required fields including department and photo'); return; }
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
  if (!emailRegex.test(email)) { showToast('Enter a valid email'); return; }
  const phoneRegex = /^\d{7,15}$/;
  if (phone && !phoneRegex.test(phone)) { showToast('Enter a valid phone number'); return; }
  
  // Validate photo
  const photo = photoInput.files[0];
  if (photo.size > 2 * 1024 * 1024) {
    showToast('Photo size must be less than 2MB');
    return;
  }

  // Use FormData to send multipart data
  const formData = new FormData();
  formData.append('first_name', fname);
  formData.append('last_name', lname);
  formData.append('email', email);
  formData.append('role', userType === 'faculty' ? 'faculty' : 'student');
  formData.append('department', department);
  formData.append('designation', userType === 'faculty' ? 'Faculty' : '');
  formData.append('student_id', userType === 'student' ? regNumber : '');
  formData.append('phone', phone || '');
  formData.append('campus', campus || '');
  formData.append('profile_photo', photo);

  fetch('/auth/register', {
    method: 'POST',
    body: formData
  }).then(async (res) => {
    const data = await res.json().catch(() => ({}));
    if (res.ok && data.success) {
      // Show popup message
      alert("Registration successful! Please check your email for login credentials. You will be redirected to the login page.");
      
      // Clear the form
      document.getElementById("student-reg-form").reset();
      document.getElementById('photo-preview').style.display = 'none';
      
      // Switch to login form
      showStudentForm('login');
      
      // Hide success message
      document.getElementById("student-register-success").style.display = "none";
    } else {
      showToast(data.message || 'Registration failed');
    }
  }).catch(() => showToast('Network error'));
}

async function handleExternalLogin(event) {
  event.preventDefault();

  const userId = document.getElementById("external-login-id").value.trim();
  const password = document.getElementById("external-login-password").value;
  if (!userId || !password) { showToast('Enter User ID and password'); return; }
  if (userId.includes('@')) { showToast('Please use your User ID (e.g., EXT000001), not email'); return; }

  try {
    // Use the same login flow as student/faculty
    const res = await fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include', // set session cookie
      // Backend expects the identifier in 'email' key; passing the User ID here is accepted server-side as student_id.
      body: JSON.stringify({ email: userId, password, user_type: 'external' })
    });
    const data = await res.json().catch(()=>({success:false}));
    if (res.ok && data.success) {
      document.getElementById("external-login-success").style.display = "block";
      const redirect = (data.data && data.data.redirect_url) || '/dashboard';
      setTimeout(()=>{ window.location.href = redirect; }, 800);
    } else {
      showToast(data.message || 'Login failed');
    }
  } catch (_) {
    showToast('Network error');
  }
}

function handleExternalRegistration(event) {
  event.preventDefault();

  const aadhar = document.getElementById("external-reg-aadhar").value;
  const fname = document.getElementById("external-reg-fname").value;
  const lname = document.getElementById("external-reg-lname").value;
  const phone = document.getElementById("external-reg-phone").value;
  const photoInput = document.getElementById("external-reg-photo");
  const profession = document.getElementById("external-reg-profession").value;
  const institution = document.getElementById("external-reg-institution").value;
  const address = document.getElementById("external-reg-address").value;
  const pincode = document.getElementById("external-reg-pincode").value;
  const city = document.getElementById("external-reg-city").value;
  const state = document.getElementById("external-reg-state").value;
  const email = document.getElementById("external-reg-email").value;

  // Basic validation
  if (!aadhar || !fname || !lname || !phone || !photoInput.files[0] || !profession || !institution || !address || !pincode || !city || !state || !email) {
    alert("Please fill in all required fields including photo.");
    return;
  }

  // Validate Aadhar card (12 digits)
  if (!/^\d{12}$/.test(aadhar.replace(/\s/g, ''))) {
    alert("Aadhar card number must be exactly 12 digits.");
    return;
  }

  // Validate email format
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    alert("Please enter a valid email address.");
    return;
  }

  // Validate phone number (10 digits)
  if (!/^\d{10}$/.test(phone.replace(/\s/g, ''))) {
    alert("Phone number must be exactly 10 digits.");
    return;
  }

  // Validate pincode (6 digits)
  if (!/^\d{6}$/.test(pincode.replace(/\s/g, ''))) {
    alert("Pincode must be exactly 6 digits.");
    return;
  }
  
  // Validate photo
  const photo = photoInput.files[0];
  if (photo.size > 2 * 1024 * 1024) {
    alert('Photo size must be less than 2MB');
    return;
  }

  // Use FormData to send multipart data
  const formData = new FormData();
  formData.append('email', email);
  formData.append('first_name', fname);
  formData.append('last_name', lname);
  formData.append('aadhar_card', aadhar);
  formData.append('phone', phone);
  formData.append('profession', profession);
  formData.append('institution', institution);
  formData.append('address', address);
  formData.append('pincode', pincode);
  formData.append('city', city);
  formData.append('state', state);
  formData.append('profile_photo', photo);

  fetch('/auth/register-external', {
    method: 'POST',
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      // Show popup message
      alert("Registration successful! Please check your email for login credentials. You will be redirected to the login page.");
      
      // Clear the form
      event.target.reset();
      document.getElementById('external-photo-preview').style.display = 'none';
      
      // Switch to login form
      showExternalForm('login');
      
      // Hide any success messages
      document.getElementById("external-register-success").style.display = "none";
    } else {
      alert("Registration failed: " + data.message);
    }
  })
  .catch(error => {
    console.error('Error:', error);
    alert("Registration failed. Please try again.");
  });
}

// Photo upload preview and validation
function handlePhotoPreview(inputId, previewId, previewImgId) {
  const input = document.getElementById(inputId);
  const preview = document.getElementById(previewId);
  const previewImg = document.getElementById(previewImgId);
  
  if (input.files && input.files[0]) {
    const file = input.files[0];
    
    // Validate file size (2MB = 2 * 1024 * 1024 bytes)
    if (file.size > 2 * 1024 * 1024) {
      showToast('File size must be less than 2MB');
      input.value = '';
      preview.style.display = 'none';
      return false;
    }
    
    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png'];
    if (!allowedTypes.includes(file.type)) {
      showToast('Only JPG, JPEG, and PNG files are allowed');
      input.value = '';
      preview.style.display = 'none';
      return false;
    }
    
    // Show preview
    const reader = new FileReader();
    reader.onload = function(e) {
      previewImg.src = e.target.result;
      preview.style.display = 'block';
    };
    reader.readAsDataURL(file);
    return true;
  }
  return false;
}

// Add smooth animations and interactions
document.addEventListener("DOMContentLoaded", function () {
  // Setup photo upload listeners
  const studentPhotoInput = document.getElementById('student-reg-photo');
  if (studentPhotoInput) {
    studentPhotoInput.addEventListener('change', function() {
      handlePhotoPreview('student-reg-photo', 'photo-preview', 'preview-image');
    });
  }
  
  const externalPhotoInput = document.getElementById('external-reg-photo');
  if (externalPhotoInput) {
    externalPhotoInput.addEventListener('change', function() {
      handlePhotoPreview('external-reg-photo', 'external-photo-preview', 'external-preview-image');
    });
  }
  
  // Add hover effects to buttons
  const buttons = document.querySelectorAll(".user-type-btn, .submit-btn");
  buttons.forEach((button) => {
    button.addEventListener("mouseenter", function () {
      this.style.transform = "translateY(-2px)";
    });

    button.addEventListener("mouseleave", function () {
      this.style.transform = "translateY(0)";
    });
  });
});

// ===== FORGOT PASSWORD FUNCTIONALITY =====

let otpTimerInterval = null;

function openForgotPasswordModal() {
  const modal = document.getElementById('forgot-password-modal');
  modal.style.display = 'flex';
  
  // Reset to step 1
  showForgotStep(1);
  
  // Clear all forms
  document.getElementById('forgot-email-form').reset();
  document.getElementById('forgot-otp-form').reset();
  document.getElementById('forgot-reset-form').reset();
}

function closeForgotPasswordModal() {
  const modal = document.getElementById('forgot-password-modal');
  modal.style.display = 'none';
  
  // Clear timer if exists
  if (otpTimerInterval) {
    clearInterval(otpTimerInterval);
    otpTimerInterval = null;
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
    showToast('Please enter your email address');
    return;
  }
  
  try {
    const response = await fetch('/auth/forgot-password/send-otp', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email })
    });
    
    const data = await response.json();
    
    if (response.ok && data.success) {
      showToast(data.message || 'Verification code sent!');
      showForgotStep(2);
      startOTPTimer();
    } else {
      showToast(data.message || 'Failed to send verification code');
    }
  } catch (error) {
    console.error('Send OTP error:', error);
    showToast('An error occurred. Please try again.');
  }
}

// Handle Verify OTP
async function handleVerifyOTP(event) {
  event.preventDefault();
  
  const otp = document.getElementById('forgot-otp').value.trim();
  
  if (!otp || otp.length !== 6) {
    showToast('Please enter the 6-digit verification code');
    return;
  }
  
  try {
    const response = await fetch('/auth/forgot-password/verify-otp', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ otp })
    });
    
    const data = await response.json();
    
    if (response.ok && data.success) {
      showToast(data.message || 'Code verified!');
      showForgotStep(3);
      
      // Clear timer
      if (otpTimerInterval) {
        clearInterval(otpTimerInterval);
        otpTimerInterval = null;
      }
    } else {
      showToast(data.message || 'Invalid verification code');
    }
  } catch (error) {
    console.error('Verify OTP error:', error);
    showToast('An error occurred. Please try again.');
  }
}

// Handle Reset Password
async function handleResetPassword(event) {
  event.preventDefault();
  
  const newPassword = document.getElementById('forgot-new-password').value;
  const confirmPassword = document.getElementById('forgot-confirm-password').value;
  
  // Validate passwords match
  if (newPassword !== confirmPassword) {
    showToast('Passwords do not match');
    return;
  }
  
  // Validate password strength
  if (newPassword.length < 8) {
    showToast('Password must be at least 8 characters');
    return;
  }
  
  const hasUpperCase = /[A-Z]/.test(newPassword);
  const hasLowerCase = /[a-z]/.test(newPassword);
  const hasDigit = /[0-9]/.test(newPassword);
  
  if (!hasUpperCase || !hasLowerCase || !hasDigit) {
    showToast('Password must include uppercase, lowercase, and digit');
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
      showToast('Password reset successfully! Redirecting to login...');
      
      // Close modal
      closeForgotPasswordModal();
      
      // Redirect to main page after 2 seconds
      setTimeout(() => {
        showMainPage();
      }, 2000);
    } else {
      showToast(data.message || 'Failed to reset password');
    }
  } catch (error) {
    console.error('Reset password error:', error);
    showToast('An error occurred. Please try again.');
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
      body: JSON.stringify({ email })
    });
    
    const data = await response.json();
    
    if (response.ok && data.success) {
      showToast('New verification code sent!');
      startOTPTimer();
    } else {
      showToast(data.message || 'Failed to resend code');
    }
  } catch (error) {
    console.error('Resend OTP error:', error);
    showToast('An error occurred. Please try again.');
  }
}

// Start OTP Timer (5 minutes)
function startOTPTimer() {
  let timeLeft = 300; // 5 minutes in seconds
  const timerDisplay = document.getElementById('otp-timer');
  
  // Clear any existing timer
  if (otpTimerInterval) {
    clearInterval(otpTimerInterval);
  }
  
  otpTimerInterval = setInterval(() => {
    const minutes = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;
    timerDisplay.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    
    if (timeLeft <= 0) {
      clearInterval(otpTimerInterval);
      otpTimerInterval = null;
      timerDisplay.textContent = 'Expired';
      showToast('Verification code expired. Please request a new one.');
    }
    
    timeLeft--;
  }, 1000);
}
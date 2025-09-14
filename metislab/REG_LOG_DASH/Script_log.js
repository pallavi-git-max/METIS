// Navigation Functions
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
      // Change to Employee ID for faculty
      regNumberLabel.textContent = 'Employee ID';
      regNumberInput.placeholder = 'Enter your employee ID';
      
      // Hide Class/Program field for faculty
      classProgramGroup.style.display = 'none';
      classInput.required = false;
    } else {
      // Change back to Registration Number for student
      regNumberLabel.textContent = 'Registration Number';
      regNumberInput.placeholder = 'Enter your registration number';
      
      // Show Class/Program field for student
      classProgramGroup.style.display = 'block';
      classInput.required = true;
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

  // Simple validation
  if (userId && password) {
    document.getElementById("student-login-success").style.display = "block";

    // Redirect to dashboard with user info
    setTimeout(() => {
      const params = new URLSearchParams({
        type: userType,
        userId: userId,
      });
      window.location.href = `user_dash.html?${params.toString()}`;
    }, 2000);
  }
}

function handleAdminLogin(event) {
  event.preventDefault();

  // Get form data
  const userId = document.getElementById("admin-login-id").value;
  const password = document.getElementById("admin-login-password").value;

  // Simple validation
  if (userId && password) {
    document.getElementById("admin-login-success").style.display = "block";

    // Redirect to admin dashboard with user info
    setTimeout(() => {
      const params = new URLSearchParams({
        type: "admin",
        userId: userId,
      });
      window.location.href = `Admin_dash.html?${params.toString()}`;
    }, 2000);
  }
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
  
  // Check if Student or Faculty
  const userType = document.querySelector('#student-register .user-select-btn.active').textContent.trim().toLowerCase();
  
  let isValid = false;
  
  if (userType === 'student') {
    const classProgram = document.getElementById("student-reg-class").value;
    isValid = fname && lname && regNumber && email && phone && classProgram && department && campus;
  } else {
    // Faculty doesn't need class/program
    isValid = fname && lname && regNumber && email && phone && department && campus;
  }

  if (isValid) {
    document.getElementById("student-register-success").style.display = "block";

    setTimeout(() => {
      alert(`${userType === 'faculty' ? 'Faculty' : 'Student'} account created! You can now login.`);
      event.target.reset();
      document.getElementById("student-register-success").style.display = "none";
      showStudentForm("login");
    }, 2000);
  }
}

function handleExternalLogin(event) {
  event.preventDefault();

  const userId = document.getElementById("external-login-id").value;
  const password = document.getElementById("external-login-password").value;

  if (userId && password) {
    document.getElementById("external-login-success").style.display = "block";

    setTimeout(() => {
      const params = new URLSearchParams({
        type: "external",
        userId: userId,
      });
      window.location.href = `user_dash.html?${params.toString()}`;
    }, 2000);
  }
}

function handleExternalRegistration(event) {
  event.preventDefault();

  const aadhar = document.getElementById("external-reg-aadhar").value;
  const fname = document.getElementById("external-reg-fname").value;
  const lname = document.getElementById("external-reg-lname").value;
  const phone = document.getElementById("external-reg-phone").value;
  const profession = document.getElementById("external-reg-profession").value;
  const institution = document.getElementById("external-reg-institution").value;
  const address = document.getElementById("external-reg-address").value;
  const pincode = document.getElementById("external-reg-pincode").value;
  const city = document.getElementById("external-reg-city").value;
  const state = document.getElementById("external-reg-state").value;

  if (aadhar && fname && lname && phone && profession && institution && address && pincode && city && state) {
    document.getElementById("external-register-success").style.display = "block";

    setTimeout(() => {
      alert("Registration submitted successfully!");
      event.target.reset();
      document.getElementById("external-register-success").style.display = "none";
    }, 3000);
  }
}

// Add smooth animations and interactions
document.addEventListener("DOMContentLoaded", function () {
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
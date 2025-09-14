// Add click functionality to menu items
      document.querySelectorAll(".menu-item").forEach((item) => {
        item.addEventListener("click", function (e) {
          e.preventDefault();
          document
            .querySelectorAll(".menu-item")
            .forEach((i) => i.classList.remove("active"));
          this.classList.add("active");
        });
      });

      // Add click functionality to buttons
      document.querySelectorAll(".btn").forEach((btn) => {
        btn.addEventListener("click", function () {
          const action = this.textContent.trim();
          console.log("Button clicked:", action);

          // Show alert for different actions
          if (action.includes("Approve")) {
            alert("Request approved and forwarded successfully!");
          } else if (action.includes("Reject")) {
            if (confirm("Are you sure you want to reject this request?")) {
              alert("Request rejected.");
            }
          } else if (action.includes("View Details")) {
            alert("Opening request details...");
          }
        });
      });

      // Add click functionality to action buttons
      document.querySelectorAll(".action-btn").forEach((btn) => {
        btn.addEventListener("click", function () {
          const action = this.textContent.trim();
          console.log("Action button clicked:", action);

          if (action.includes("Export")) {
            alert("Generating report...");
          } else if (action.includes("Approve")) {
            alert("Opening approval queue...");
          } else if (action.includes("Reject")) {
            alert("Opening rejection form...");
          }
        });
      });

      // Add notification click
      document
        .querySelector(".notification-btn")
        .addEventListener("click", function () {
          alert("You have 3 new notifications");
        });

      // Add profile click
      document
        .querySelector(".profile-btn")
        .addEventListener("click", function () {
          alert("Opening profile settings...");
        });

        // Add click event to User Management menu item
      document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.menu-item').forEach(link => {
        if (link.textContent.includes('User Management')) {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                window.location.href = 'Admin_usr_manage.html';
            });
        }
    });
});


      // Add logout functionality
      document
        .querySelector(".logout-btn")
        .addEventListener("click", function (e) {
          e.preventDefault();
          if (confirm("Are you sure you want to logout?")) {
            alert("Logging out...");
            // In real app, would redirect to login page
            window.location.href = "college-login-system.html";
          }
        });

      // Simulate real-time updates
      setInterval(() => {
        // Update random stat
        const stats = document.querySelectorAll(".stat-value");
        const randomStat = stats[Math.floor(Math.random() * stats.length)];
        const currentValue = parseInt(randomStat.textContent);
        const change = Math.random() > 0.5 ? 1 : -1;
        randomStat.textContent = Math.max(0, currentValue + change);
      }, 10000); // Update every 10 seconds
      
      const updateAdminDashboard = `
            document.querySelector('a[href="#"].menu-item:has(.menu-icon:contains("👥"))').addEventListener('click', function(e) {
                e.preventDefault();
                window.location.href = 'Admin_usr_manage.html';
            });
        `;
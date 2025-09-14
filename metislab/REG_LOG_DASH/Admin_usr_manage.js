 const usersData = [
            { id: 'STU2024001', name: 'John Doe', email: 'john.doe@university.edu', role: 'student', dept: 'Computer Science', status: 'active', lastActive: '2 hours ago' },
            { id: 'FAC2023015', name: 'Sarah Smith', email: 'sarah.smith@university.edu', role: 'faculty', dept: 'Computer Science', status: 'active', lastActive: '1 day ago' },
            { id: 'EXT2024003', name: 'Mike Johnson', email: 'mike.j@external.com', role: 'external', dept: 'N/A', status: 'inactive', lastActive: '1 week ago' },
            { id: 'STU2024045', name: 'Emily Chen', email: 'emily.chen@university.edu', role: 'student', dept: 'Electronics', status: 'active', lastActive: '3 hours ago' },
            { id: 'ADM2022001', name: 'Robert Wilson', email: 'r.wilson@university.edu', role: 'admin', dept: 'Administration', status: 'active', lastActive: 'Just now' }
        ];

        // Navigation function to redirect from admin dashboard
        function navigateToUserManagement() {
            window.location.href = 'Admin_usr_manage.html';
        }

        // Filter functions
        function applyFilters() {
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const userType = document.getElementById('userTypeFilter').value;
            const status = document.getElementById('statusFilter').value;
            const dept = document.getElementById('deptFilter').value;

            // Filter logic would go here
            console.log('Applying filters:', { searchTerm, userType, status, dept });
            
            // Show filtered results
            filterTable(searchTerm, userType, status, dept);
        }

        function resetFilters() {
            document.getElementById('searchInput').value = '';
            document.getElementById('userTypeFilter').value = '';
            document.getElementById('statusFilter').value = '';
            document.getElementById('deptFilter').value = '';
            
            // Reset table to show all users
            applyFilters();
        }

        function filterTable(searchTerm, userType, status, dept) {
            const tbody = document.getElementById('usersTableBody');
            const rows = tbody.getElementsByTagName('tr');
            
            for (let row of rows) {
                let showRow = true;
                const rowText = row.textContent.toLowerCase();
                
                // Search filter
                if (searchTerm && !rowText.includes(searchTerm)) {
                    showRow = false;
                }
                
                // User type filter
                if (userType) {
                    const roleElement = row.querySelector('.role-badge');
                    if (roleElement && !roleElement.classList.contains(`role-${userType}`)) {
                        showRow = false;
                    }
                }
                
                // Status filter
                if (status) {
                    const statusElement = row.querySelector('.status-badge');
                    if (statusElement && !statusElement.classList.contains(`status-${status}`)) {
                        showRow = false;
                    }
                }
                
                // Department filter
                if (dept) {
                    const deptCell = row.cells[3];
                    if (deptCell && !deptCell.textContent.toLowerCase().includes(dept)) {
                        showRow = false;
                    }
                }
                
                row.style.display = showRow ? '' : 'none';
            }
        }

        // Action button functions
        function viewUser(userId) {
            console.log('Viewing user:', userId);
            // Implement view user details modal or redirect
        }

        function editUser(userId) {
            console.log('Editing user:', userId);
            // Implement edit user modal or redirect
        }

        function deleteUser(userId) {
            if (confirm('Are you sure you want to delete this user?')) {
                console.log('Deleting user:', userId);
                // Implement delete user functionality
            }
        }

        function addNewUser() {
            console.log('Adding new user');
            // Implement add new user modal or redirect
        }

        // Export functionality
        document.querySelector('.export-btn').addEventListener('click', function() {
            console.log('Exporting user data to Excel...');
            // Implement export functionality
            alert('User data export initiated. The file will be downloaded shortly.');
        });

        // Add event listeners to all action buttons
        document.addEventListener('DOMContentLoaded', function() {
            // View buttons
            document.querySelectorAll('.btn-view').forEach(btn => {
                btn.addEventListener('click', function() {
                    const row = this.closest('tr');
                    const userId = row.cells[1].textContent;
                    viewUser(userId);
                });
            });

            // Edit buttons
            document.querySelectorAll('.btn-edit').forEach(btn => {
                btn.addEventListener('click', function() {
                    const row = this.closest('tr');
                    const userId = row.cells[1].textContent;
                    editUser(userId);
                });
            });

            // Delete buttons
            document.querySelectorAll('.btn-delete').forEach(btn => {
                btn.addEventListener('click', function() {
                    const row = this.closest('tr');
                    const userId = row.cells[1].textContent;
                    deleteUser(userId);
                });
            });

            // Pagination buttons
            document.querySelectorAll('.page-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    if (!this.disabled) {
                        // Remove active class from all buttons
                        document.querySelectorAll('.page-btn').forEach(b => b.classList.remove('active'));
                        
                        // Add active class to clicked button (if it's a number)
                        if (!isNaN(this.textContent)) {
                            this.classList.add('active');
                        }
                        
                        console.log('Navigate to page:', this.textContent);
                        // Implement pagination logic
                    }
                });
            });

            // Real-time search
            document.getElementById('searchInput').addEventListener('input', function() {
                if (this.value.length > 2 || this.value.length === 0) {
                    applyFilters();
                }
            });
        });
        
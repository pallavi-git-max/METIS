document.addEventListener('DOMContentLoaded', function() {
    const projectRequestsList = document.getElementById('projectRequestsList');
    const pendingApprovalsList = document.getElementById('pendingApprovalsList');
    const openRequestFormBtn = document.getElementById('openRequestFormBtn');
    const requestModal = document.getElementById('requestModal');
    const closeRequestModal = document.getElementById('closeRequestModal');
    const projectRequestForm = document.getElementById('projectRequestForm');
    const requestFormMessage = document.getElementById('requestFormMessage');
    const ndaUploadForm = document.getElementById('ndaUploadForm');
    const ndaUploadMessage = document.getElementById('ndaUploadMessage');

    // Fetch and display user's project requests
    const loadProjectRequests = async () => {
        projectRequestsList.innerHTML = 'Loading...';
        try {
            const res = await fetch('/projects/');
            if (!res.ok) throw new Error('Failed to fetch project requests');
            const requests = await res.json();
            if (requests.length === 0) {
                projectRequestsList.innerHTML = '<li>No project requests found.</li>';
                return;
            }
            projectRequestsList.innerHTML = '';
            requests.forEach(req => {
                const li = document.createElement('li');
                li.textContent = `${req.project_title} - Status: ${req.status}`;
                projectRequestsList.appendChild(li);
            });
        } catch (err) {
            projectRequestsList.innerHTML = '<li>Error loading project requests.</li>';
            console.error(err);
        }
    };

    // Fetch and display pending approvals if admin
    const loadPendingApprovals = async () => {
        if (!pendingApprovalsList) return;
        pendingApprovalsList.innerHTML = 'Loading...';
        try {
            const res = await fetch('/approvals/pending');
            if (!res.ok) {
                pendingApprovalsList.innerHTML = '<li>Not authorized or no pending approvals.</li>';
                return;
            }
            const approvals = await res.json();
            if (approvals.length === 0) {
                pendingApprovalsList.innerHTML = '<li>No pending approvals.</li>';
                return;
            }
            pendingApprovalsList.innerHTML = '';
            approvals.forEach(appr => {
                const li = document.createElement('li');
                li.textContent = `Request #${appr.id} from User ID ${appr.user_id}: ${appr.project_title}`;
                // Approve button
                const approveBtn = document.createElement('button');
                approveBtn.textContent = 'Approve';
                approveBtn.onclick = () => handleApproval(appr.id, true);
                // Reject button
                const rejectBtn = document.createElement('button');
                rejectBtn.textContent = 'Reject';
                rejectBtn.onclick = () => handleApproval(appr.id, false);
                li.appendChild(approveBtn);
                li.appendChild(rejectBtn);
                pendingApprovalsList.appendChild(li);
            });
        } catch (err) {
            pendingApprovalsList.innerHTML = '<li>Error loading approvals.</li>';
            console.error(err);
        }
    };

    // Handle approval or rejection
    const handleApproval = async (id, approve) => {
        try {
            const url = `/approvals/${id}/${approve ? 'approve' : 'reject'}`;
            const res = await fetch(url, { method: 'POST' });
            const result = await res.json();
            if (res.ok && result.success) {
                alert(result.message);
                loadPendingApprovals();
                loadProjectRequests();
            } else {
                alert(result.message || 'Action failed.');
            }
        } catch (err) {
            alert('Error processing request.');
            console.error(err);
        }
    };

    // Open and close modal
    openRequestFormBtn.addEventListener('click', () => {
        requestModal.style.display = 'block';
        requestFormMessage.textContent = '';
        projectRequestForm.reset();
    });

    closeRequestModal.addEventListener('click', () => {
        requestModal.style.display = 'none';
    });

    window.onclick = function(event) {
        if (event.target === requestModal) {
            requestModal.style.display = 'none';
        }
    };

    // Submit project request form
    projectRequestForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        requestFormMessage.textContent = '';
        const project_title = projectRequestForm.project_title.value.trim();
        const description = projectRequestForm.description.value.trim();

        if (!project_title || !description) {
            requestFormMessage.textContent = 'All fields are required.';
            return;
        }

        try {
            const res = await fetch('/projects/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ project_title, description })
            });
            const result = await res.json();
            if (res.ok && result.success) {
                requestFormMessage.style.color = 'green';
                requestFormMessage.textContent = 'Project request submitted.';
                projectRequestForm.reset();
                loadProjectRequests();
                // Close modal after short delay
                setTimeout(() => {
                    requestModal.style.display = 'none';
                }, 1500);
            } else {
                requestFormMessage.style.color = 'red';
                requestFormMessage.textContent = result.message || 'Submission failed.';
            }
        } catch (err) {
            requestFormMessage.style.color = 'red';
            requestFormMessage.textContent = 'Error submitting request.';
            console.error(err);
        }
    });

    // NDA upload form
    ndaUploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        ndaUploadMessage.textContent = '';
        const fileInput = ndaUploadForm.nda_pdf;
        if (!fileInput.files.length) {
            ndaUploadMessage.style.color = 'red';
            ndaUploadMessage.textContent = 'Please select a PDF file.';
            return;
        }
        const file = fileInput.files[0];
        if (file.type !== 'application/pdf') {
            ndaUploadMessage.style.color = 'red';
            ndaUploadMessage.textContent = 'Only PDF files are allowed.';
            return;
        }

        const formData = new FormData();
        formData.append('nda_pdf', file);

        try {
            const res = await fetch('/auth/upload-nda', {
                method: 'POST',
                body: formData
            });
            const result = await res.json();
            if (res.ok && result.success) {
                ndaUploadMessage.style.color = 'green';
                ndaUploadMessage.textContent = 'NDA uploaded successfully.';
                ndaUploadForm.reset();
            } else {
                ndaUploadMessage.style.color = 'red';
                ndaUploadMessage.textContent = result.message || 'Upload failed.';
            }
        } catch (err) {
            ndaUploadMessage.style.color = 'red';
            ndaUploadMessage.textContent = 'Error uploading file.';
            console.error(err);
        }
    });

    // Initial load
    loadProjectRequests();
    loadPendingApprovals();
});

function toggleOther(id) {
            const otherField = document.getElementById(id);
            const checkbox = document.getElementById(id.replace('-specify', ''));
            
            if (checkbox.checked || checkbox.type === 'radio') {
                otherField.style.display = 'block';
            } else {
                otherField.style.display = 'none';
            }
        }

        document.getElementById('metisRequisitionForm').addEventListener('submit', function() {
            // Check if at least one field is selected in question 1
            const fields = document.querySelectorAll('input[name="fields"]:checked');
            if (fields.length === 0) {
                alert('Please select at least one field for question 1');
                return;
            }
            
            // Check if at least one data type is selected in question 5
            const dataTypes = document.querySelectorAll('input[name="data-type"]:checked');
            if (dataTypes.length === 0) {
                alert('Please select at least one data type for question 5');
                return;
            }
            
            // Check if declaration is agreed
            if (!document.getElementById('agree').checked) {
                alert('Please agree to the declaration terms');
            }
            
            alert('Form submitted successfully! Your session will be scheduled based on availability.')
            // Here you would typically send the form data to a server
            window.location.href = 'user_dash.html';
        });
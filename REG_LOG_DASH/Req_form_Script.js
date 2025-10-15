function toggleOther(id) {
            const otherField = document.getElementById(id);
            const checkbox = document.getElementById(id.replace('-specify', ''));
            
            if (checkbox.checked || checkbox.type === 'radio') {
                otherField.style.display = 'block';
            } else {
                otherField.style.display = 'none';
            }
        }

        document.getElementById('metisRequisitionForm').addEventListener('submit', async function(e) {
            e.preventDefault();
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
                return;
            }

            const projectTitle = document.getElementById('project_title').value.trim();
            const description = document.getElementById('description').value.trim();
            const purpose = document.getElementById('purpose').value.trim();
            const expectedDuration = document.getElementById('expected_duration').value.trim();

            if (!projectTitle || !description || !purpose) {
                alert('Please fill in Project Title, Description, and Purpose.');
                return;
            }

            const selectedFields = Array.from(fields).map(el => el.value);
            const packageChoice = (document.querySelector('input[name="package"]:checked') || {}).value;
            const datasetStatus = (document.querySelector('input[name="dataset-status"]:checked') || {}).value;
            const datasetSize = (document.querySelector('input[name="dataset-size"]:checked') || {}).value;
            const selectedDataTypes = Array.from(dataTypes).map(el => el.value);
            const cores = (document.querySelector('input[name="cores"]:checked') || {}).value;

            const payload = {
                project_title: projectTitle,
                description: description,
                purpose: purpose,
                expected_duration: expectedDuration || null,
                priority: 'medium',
                fields: selectedFields,
                package: packageChoice || null,
                dataset_status: datasetStatus || null,
                dataset_size: datasetSize || null,
                data_type: selectedDataTypes,
                cores: cores || null,
                additional_requirements: null,
                agree: true
            };

            try {
                const res = await fetch('/projects/submit', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                const result = await res.json();
                if (!res.ok || !result.success) {
                    alert(result.message || 'Failed to submit request');
                    return;
                }

                alert('Request submitted successfully');
                window.location.href = '/dashboard';
            } catch (err) {
                alert('Network error submitting request');
            }
        });
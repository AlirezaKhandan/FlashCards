document.addEventListener('DOMContentLoaded', () => {
    // Select all forms that we want to submit via AJAX
    const forms = document.querySelectorAll('.ajax-form');

    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = new FormData(form);
            
            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                return response.json().then(data => ({
                    data: data, 
                    status: response.status 
                }));
            })
            .then(({ data, status }) => {
                if (status === 200) {
                    // Success scenario. Check for warning
                    if (data.warning) {
                        alert(data.warning);
                    }
                    alert(data.detail || "Created successfully!");
                    // If you want to redirect after success:
                    // window.location.href = "/sets/"; // or another relevant URL
                } else if (status === 429) {
                    // Limit exceeded error
                    alert(data.detail || "You have reached your limit.");
                } else {
                    // Some other error
                    alert(data.detail || "An unknown error occurred.");
                }
            })
            .catch(err => {
                console.error('Error:', err);
                alert("A network error occurred. Please try again.");
            });
        });
    });
});

document.addEventListener('DOMContentLoaded', () => {
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
                const messageBox = form.querySelector('#message-box');
                if (messageBox) {
                    messageBox.innerHTML = ''; // Clear old messages
                }

                if (status === 200) {
                    // Success scenario
                    if (data.warning) {
                        // Insert a warning message
                        if (messageBox) {
                            messageBox.innerHTML += `<div class="bg-yellow-100 text-yellow-700 p-3 rounded mb-3">${data.warning}</div>`;
                        }
                    }
                    if (data.detail) {
                        // Insert success message
                        if (messageBox) {
                            messageBox.innerHTML += `<div class="bg-green-100 text-green-700 p-3 rounded">${data.detail}</div>`;
                        }
                    }
                } else if (status === 429) {
                    // Limit exceeded error
                    if (data.detail && messageBox) {
                        messageBox.innerHTML += `<div class="bg-red-100 text-red-700 p-3 rounded">${data.detail}</div>`;
                    }
                } else {
                    // Some other error (e.g. validation errors)
                    if (data.detail && messageBox) {
                        messageBox.innerHTML += `<div class="bg-red-100 text-red-700 p-3 rounded">${data.detail}</div>`;
                    } else {
                        // Generic error
                        if (messageBox) {
                            messageBox.innerHTML += `<div class="bg-red-100 text-red-700 p-3 rounded">An unknown error occurred.</div>`;
                        }
                    }
                }
            })
            .catch(err => {
                const messageBox = form.querySelector('#message-box');
                if (messageBox) {
                    messageBox.innerHTML = `<div class="bg-red-100 text-red-700 p-3 rounded">A network error occurred. Please try again.</div>`;
                }
                console.error('Error:', err);
            });
        });
    });
});

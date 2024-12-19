// form_submit.js
document.addEventListener('DOMContentLoaded', () => {
    const ajaxForms = document.querySelectorAll('.ajax-form');

    ajaxForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = new FormData(form);
            const messageBox = form.querySelector('#message-box');

            // Clear old messages if present
            if (messageBox) messageBox.innerHTML = '';

            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response =>
                response.json().then(data => ({
                    data: data,
                    status: response.status
                }))
            )
            .then(({ data, status }) => {
                if (messageBox) {
                    // Always clear out old messages before showing new ones
                    messageBox.innerHTML = '';
                }

                if (status === 200) {
                    // Success scenario
                    if (data.warning && messageBox) {
                        messageBox.innerHTML += `<div class="bg-yellow-100 text-yellow-700 p-3 rounded mb-3">${data.warning}</div>`;
                    }
                    if (data.detail && messageBox) {
                        messageBox.innerHTML += `<div class="bg-green-100 text-green-700 p-3 rounded">${data.detail}</div>`;
                    }
                    if (data.redirect_url) {
                        window.location.href = data.redirect_url;
                    }
                } else if (status === 429) {
                    // Limit exceeded error
                    if (data.detail && messageBox) {
                        messageBox.innerHTML += `<div class="bg-red-100 text-red-700 p-3 rounded">${data.detail}</div>`;
                    }
                } else {
                    // Validation or unknown error
                    if (data.detail && messageBox) {
                        messageBox.innerHTML += `<div class="bg-red-100 text-red-700 p-3 rounded">${data.detail}</div>`;
                    } else if (messageBox) {
                        messageBox.innerHTML += `<div class="bg-red-100 text-red-700 p-3 rounded">An unknown error occurred.</div>`;
                    }
                }
            })
            .catch(err => {
                if (messageBox) {
                    messageBox.innerHTML = `<div class="bg-red-100 text-red-700 p-3 rounded">A network error occurred. Please try again.</div>`;
                }
                console.error('Error:', err);
            });
        });
    });
});

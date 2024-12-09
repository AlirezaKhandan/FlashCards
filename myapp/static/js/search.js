document.addEventListener('DOMContentLoaded', () => {
    // Handle Add buttons for sets and collections
    const addButtons = document.querySelectorAll('.add-button');
    addButtons.forEach(button => {
        button.addEventListener('click', () => {
            const type = button.getAttribute('data-type'); // 'set' or 'collection'
            const id = button.getAttribute('data-id');

            fetch(`/api/add/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ type, id })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(`${type.charAt(0).toUpperCase() + type.slice(1)} added successfully!`);
                } else {
                    alert(`Failed to add ${type}.`);
                }
            })
            .catch(err => console.error(err));
        });
    });

    // Handle Follow buttons for users
    const followButtons = document.querySelectorAll('.follow-button');
    followButtons.forEach(button => {
        button.addEventListener('click', () => {
            const userId = button.getAttribute('data-id');

            fetch(`/api/follow/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ user_id: userId })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('User followed successfully!');
                } else {
                    alert('Failed to follow user.');
                }
            })
            .catch(err => console.error(err));
        });
    });
});

// Utility function to get CSRF token from cookies for AJAX POST requests in Django
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i=0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

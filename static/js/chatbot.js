function toggleUserDetails() {
    const details = document.getElementById('user-details');
    if (details.style.display === 'none' || details.style.display === '') {
        details.style.display = 'block';
    } else {
        details.style.display = 'none';
    }
}

// Optional: close user details if clicked outside
document.addEventListener('click', function(event) {
    const details = document.getElementById('user-details');
    const userBar = document.getElementById('user-bar');
    if (details && userBar) {
        if (!details.contains(event.target) && !userBar.contains(event.target)) {
            details.style.display = 'none';
        }
    }
});

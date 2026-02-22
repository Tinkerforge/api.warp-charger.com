// ---------------------------------------------------------------------------
// Theme toggle (same pattern as vislog.warp-charger.com)
// ---------------------------------------------------------------------------
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-bs-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-bs-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const lightIcon = document.getElementById('theme-icon-light');
    const darkIcon = document.getElementById('theme-icon-dark');
    if (!lightIcon || !darkIcon) return;
    if (theme === 'dark') {
        lightIcon.classList.add('d-none');
        darkIcon.classList.remove('d-none');
    } else {
        lightIcon.classList.remove('d-none');
        darkIcon.classList.add('d-none');
    }
}

// Apply saved theme immediately (before DOMContentLoaded)
(function() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-bs-theme', savedTheme);
    // Icon update deferred until DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            updateThemeIcon(savedTheme);
        });
    } else {
        updateThemeIcon(savedTheme);
    }
})();

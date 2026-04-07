// ============================================
//   BOOKSHARE — MAIN JAVASCRIPT
// ============================================

// --- USER DROPDOWN ---
function toggleUserMenu() {
    const dropdown = document.getElementById('userDropdown');
    if (dropdown) dropdown.classList.toggle('open');
}

document.addEventListener('click', function (e) {
    const dropdown = document.getElementById('userDropdown');
    const userBtn = document.querySelector('.user-btn');
    if (dropdown && userBtn && !userBtn.contains(e.target)) {
        dropdown.classList.remove('open');
    }
});

// --- MOBILE MENU ---
function toggleMobileMenu() {
    const menu = document.getElementById('mobileMenu');
    if (menu) menu.classList.toggle('open');
}

// --- PASSWORD VISIBILITY TOGGLE ---
function togglePassword(inputId, btn) {
    const input = document.getElementById(inputId);
    if (!input) return;
    const isText = input.type === 'text';
    input.type = isText ? 'password' : 'text';
    btn.innerHTML = isText
        ? `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
         <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
         <circle cx="12" cy="12" r="3"/>
       </svg>`
        : `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
         <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
         <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
         <line x1="1" y1="1" x2="23" y2="23"/>
       </svg>`;
}

// --- AUTO-DISMISS FLASH MESSAGES ---
document.addEventListener('DOMContentLoaded', function () {
    const flashes = document.querySelectorAll('.flash');
    flashes.forEach(function (flash) {
        setTimeout(function () {
            flash.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            flash.style.opacity = '0';
            flash.style.transform = 'translateX(20px)';
            setTimeout(function () { flash.remove(); }, 400);
        }, 4000);
    });
});

// --- ACTIVE NAV LINK HIGHLIGHT ---
document.addEventListener('DOMContentLoaded', function () {
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link, .mobile-menu a').forEach(function (link) {
        if (link.getAttribute('href') === currentPath) {
            link.style.color = 'var(--green-main)';
            link.style.background = 'var(--bg-subtle)';
        }
    });
});
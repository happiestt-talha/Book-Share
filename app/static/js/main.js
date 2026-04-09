// ============================================
//   BOOKSHARE — MAIN JAVASCRIPT  (Phase 7)
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
    const ham = document.querySelector('.hamburger');
    if (menu) {
        menu.classList.toggle('open');
        if (ham) ham.classList.toggle('open');
    }
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
        }, 4500);
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

// --- BACK TO TOP BUTTON ---
document.addEventListener('DOMContentLoaded', function () {
    const btn = document.createElement('button');
    btn.className = 'back-to-top';
    btn.title = 'Back to top';
    btn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none"
                      stroke="currentColor" stroke-width="2.5">
                      <polyline points="18 15 12 9 6 15"/>
                     </svg>`;
    btn.onclick = () => window.scrollTo({ top: 0, behavior: 'smooth' });
    document.body.appendChild(btn);

    window.addEventListener('scroll', function () {
        btn.classList.toggle('visible', window.scrollY > 400);
    });
});

// --- SUBMIT BUTTON LOADING STATE ---
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('form').forEach(function (form) {
        form.addEventListener('submit', function () {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.closest('[onsubmit]')) {
                setTimeout(function () {
                    submitBtn.disabled = true;
                    submitBtn.style.opacity = '0.7';
                }, 50);
            }
        });
    });
});

// --- DASHBOARD TAB SWITCHING ---
function switchTab(tabId, btn) {
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.dash-tab').forEach(b => b.classList.remove('active'));
    const panel = document.getElementById('tab-' + tabId);
    if (panel) panel.classList.add('active');
    if (btn) btn.classList.add('active');

    // Update URL hash without scrolling
    history.replaceState(null, '', '#' + tabId);
}

// Auto-open tab from URL hash
document.addEventListener('DOMContentLoaded', function () {
    const hash = window.location.hash.replace('#', '');
    const valid = ['my-books', 'pending', 'borrows', 'notifications'];
    if (valid.includes(hash)) {
        const btn = document.querySelector(`.dash-tab[onclick*="${hash}"]`);
        if (btn) switchTab(hash, btn);
    }
});

// --- SMOOTH SCROLL FOR ANCHOR LINKS ---
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
        anchor.addEventListener('click', function (e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
});

// --- BORROW MODAL ---
function openBorrowModal() {
    const m = document.getElementById('borrowModal');
    if (m) { m.classList.add('open'); document.body.style.overflow = 'hidden'; }
}
function closeBorrowModal(e) {
    if (e && e.target !== document.getElementById('borrowModal')) return;
    const m = document.getElementById('borrowModal');
    if (m) { m.classList.remove('open'); document.body.style.overflow = ''; }
}

// Close modal with Escape key
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        const m = document.getElementById('borrowModal');
        if (m && m.classList.contains('open')) {
            m.classList.remove('open');
            document.body.style.overflow = '';
        }
        const dropdown = document.getElementById('userDropdown');
        if (dropdown) dropdown.classList.remove('open');
    }
});

// --- FILE UPLOAD HELPERS (add book page) ---
function toggleBookType(type) {
    const physical = document.getElementById('physical-fields');
    const digital = document.getElementById('digital-fields');
    if (physical) physical.style.display = type === 'physical' ? 'block' : 'none';
    if (digital) digital.style.display = type === 'digital' ? 'block' : 'none';
    document.querySelectorAll('.type-option').forEach(el => el.classList.remove('type-selected'));
    const radio = document.querySelector(`.type-option input[value="${type}"]`);
    if (radio) radio.parentElement.classList.add('type-selected');
}

function showFileName(input) {
    const chosen = document.getElementById('file-chosen');
    if (chosen && input.files && input.files[0]) {
        chosen.textContent = '✓ ' + input.files[0].name;
        chosen.style.display = 'block';
    }
}

// Drag and drop
document.addEventListener('DOMContentLoaded', function () {
    const dropArea = document.getElementById('fileDropArea');
    if (!dropArea) return;
    ['dragenter', 'dragover'].forEach(e =>
        dropArea.addEventListener(e, ev => {
            ev.preventDefault();
            dropArea.classList.add('drag-over');
        })
    );
    ['dragleave', 'drop'].forEach(e =>
        dropArea.addEventListener(e, ev => {
            ev.preventDefault();
            dropArea.classList.remove('drag-over');
        })
    );
    dropArea.addEventListener('drop', ev => {
        const files = ev.dataTransfer.files;
        const fileInput = document.getElementById('file_upload');
        if (files[0] && fileInput) {
            fileInput.files = files;
            showFileName(fileInput);
        }
    });

    // Init correct book type state on page load
    const checkedType = document.querySelector('input[name="book_type"]:checked');
    if (checkedType) toggleBookType(checkedType.value);
});
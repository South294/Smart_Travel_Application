document.addEventListener('DOMContentLoaded', function () {
    initViewSwitching();
    initSidebar();
    initModals();
    initApprovalFlow();
    initVoucherActions();
    initSettingsToggles();
});

function initViewSwitching() {
    const navLinks = document.querySelectorAll('.admin-nav-link[data-view]');
    const views = document.querySelectorAll('.admin-view');
    const headerTitle = document.getElementById('adminHeaderTitle');

    navLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            const viewId = this.getAttribute('data-view');

            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');

            views.forEach(v => {
                v.classList.remove('is-active');
                if (v.id === viewId) v.classList.add('is-active');
            });

            if (headerTitle) headerTitle.textContent = this.textContent.trim();

            if (window.innerWidth <= 768) {
                closeSidebar();
            }
        });
    });
}

function initSidebar() {
    const menuBtn = document.querySelector('.admin-menu-btn');
    const sidebar = document.getElementById('adminSidebar');
    const overlay = document.querySelector('.sidebar-overlay');

    if (menuBtn) {
        menuBtn.addEventListener('click', () => {
            sidebar.classList.add('active');
            overlay.classList.add('is-active');
        });
    }

    if (overlay) {
        overlay.addEventListener('click', closeSidebar);
    }
}

function closeSidebar() {
    const sidebar = document.getElementById('adminSidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    if (sidebar) sidebar.classList.remove('active');
    if (overlay) overlay.classList.remove('is-active');
}

function initModals() {
    document.querySelectorAll('[data-modal-target]').forEach(btn => {
        btn.addEventListener('click', () => {
            const modalId = btn.getAttribute('data-modal-target');
            const modal = document.getElementById(modalId);
            if (modal) modal.classList.add('is-active');
        });
    });

    document.querySelectorAll('[data-modal-close]').forEach(btn => {
        btn.addEventListener('click', () => {
            const modal = btn.closest('.modal-overlay');
            if (modal) modal.classList.remove('is-active');
        });
    });

    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) overlay.classList.remove('is-active');
        });
    });
}

function initApprovalFlow() {
    let currentTargetRow = null;

    document.querySelectorAll('[data-action="approve"]').forEach(btn => {
        btn.addEventListener('click', function () {
            const modal = this.closest('.modal-overlay');
            if (modal) modal.classList.remove('is-active');
            
            showToast('Phê duyệt thành công!', 'success');
            updatePendingCount(-1);
        });
    });

    document.querySelectorAll('[data-action="reject"]').forEach(btn => {
        btn.addEventListener('click', function () {
            currentTargetRow = this.closest('tr');
            const rejectModal = document.getElementById('rejectModal');
            if (rejectModal) rejectModal.classList.add('is-active');
        });
    });

    const confirmRejectBtn = document.getElementById('confirmRejectBtn');
    if (confirmRejectBtn) {
        confirmRejectBtn.addEventListener('click', () => {
            const reason = document.getElementById('rejectReason').value;
            if (!reason) {
                alert('Vui lòng nhập lý do từ chối');
                return;
            }

            if (currentTargetRow) {
                const badge = currentTargetRow.querySelector('.badge');
                if (badge) {
                    badge.className = 'badge badge-danger';
                    badge.textContent = 'Đã từ chối';
                }
                const actions = currentTargetRow.querySelector('.action-group');
                if (actions) actions.innerHTML = '<span class="text-danger text-sm font-semibold">Đã xử lý</span>';
            }

            const modal = document.getElementById('rejectModal');
            if (modal) modal.classList.remove('is-active');
            
            showToast('Yêu cầu đã bị từ chối', 'error');
            updatePendingCount(-1);
        });
    }
}

function updatePendingCount(change) {
    const el = document.getElementById('pendingCount');
    if (el) {
        let count = parseInt(el.textContent) || 0;
        count += change;
        el.textContent = count > 0 ? count : 0;
        if (count <= 0) el.style.display = 'none';
    }
}

function initVoucherActions() {
    const form = document.getElementById('addVoucherForm');
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            showToast('Tạo Voucher thành công!', 'success');
            form.reset();
        });
    }
}

function initSettingsToggles() {
    document.querySelectorAll('.toggle-switch input').forEach(toggle => {
        toggle.addEventListener('change', function () {
            const state = this.checked ? 'Bật' : 'Tắt';
            showToast(`Đã ${state} cài đặt`, 'info');
        });
    });
}

function showToast(message, type = 'success') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = 'bx-check-circle';
    if (type === 'error') icon = 'bx-error-circle';
    if (type === 'info') icon = 'bx-info-circle';

    toast.innerHTML = `
        <i class="bx ${icon} toast-icon"></i>
        <span>${message}</span>
        <button class="toast-close">&times;</button>
    `;

    container.appendChild(toast);

    toast.querySelector('.toast-close').addEventListener('click', () => {
        toast.classList.add('toast-out');
        setTimeout(() => toast.remove(), 300);
    });

    setTimeout(() => {
        if (toast.parentNode) {
            toast.classList.add('toast-out');
            setTimeout(() => toast.remove(), 300);
        }
    }, 3000);
}

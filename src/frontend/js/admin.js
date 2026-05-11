async function fetchApi(url, options = {}) {
    var token = localStorage.getItem('access_token');
    var headers = { 'Content-Type': 'application/json' };
    if (options.headers) {
        Object.keys(options.headers).forEach(function(k) { headers[k] = options.headers[k]; });
    }
    if (token) headers['Authorization'] = 'Bearer ' + token;
    var res = await fetch('http://localhost:8000' + url, { method: options.method || 'GET', headers: headers, body: options.body });
    if (res.status === 401) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('isLoggedIn');
        window.location.href = 'auth.html';
    }
    return res;
}

document.addEventListener('DOMContentLoaded', async function () {
    initViewSwitching();
    initSidebar();
    initModals();
    initVoucherActions();
    initSettingsToggles();
    await loadDashboardStats();
    await loadPendingGuides();
    await loadActiveVouchers();
});

async function loadDashboardStats() {
    try {
        var res = await fetchApi('/api/admin/dashboard');
        if (!res.ok) return;
        var data = await res.json();

        var statCards = document.querySelectorAll('.stat-card .stat-value');
        if (statCards.length >= 4) {
            statCards[0].textContent = data.users_count;
            statCards[1].textContent = data.tours_count;
            statCards[2].textContent = data.bookings_count || '0';
            statCards[3].textContent = data.pending_guides_count;
        }

        var pendingCountEl = document.getElementById('pendingCount');
        if (pendingCountEl) {
            pendingCountEl.textContent = data.pending_guides_count;
            pendingCountEl.style.display = data.pending_guides_count > 0 ? 'inline-block' : 'none';
        }
    } catch(e) {}
}

async function loadPendingGuides() {
    try {
        var res = await fetchApi('/api/admin/guides/pending');
        if (!res.ok) return;
        var guides = await res.json();

        var tbody = document.querySelector('#guidesView tbody');
        if (!tbody) return;

        var badgeEl = document.getElementById('guidePendingBadge');
        if (badgeEl) {
            badgeEl.textContent = guides.length + ' hồ sơ chờ duyệt';
            badgeEl.className = guides.length > 0 ? 'badge badge-warning' : 'badge badge-success';
            if (guides.length === 0) badgeEl.textContent = 'Không có hồ sơ chờ';
        }

        tbody.innerHTML = '';
        if (guides.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding: 24px;">Không có hồ sơ chờ duyệt</td></tr>';
            return;
        }

        guides.forEach(function(guide) {
            var tr = document.createElement('tr');
            tr.innerHTML =
                '<td>' +
                '<div class="user-info-table">' +
                '<div class="user-avatar-sm">' + guide.name.charAt(0) + '</div>' +
                '<div><span class="font-bold">' + guide.name + '</span></div>' +
                '</div>' +
                '</td>' +
                '<td>' + guide.experience_years + ' năm</td>' +
                '<td>' + (guide.areas || []).join(', ') + '</td>' +
                '<td><span class="badge badge-warning">Chờ duyệt</span></td>' +
                '<td>' +
                '<div class="action-group">' +
                '<button class="btn btn-sm btn-outline btn-approve" data-id="' + guide.id + '">Duyệt</button>' +
                '<button class="btn btn-sm btn-outline-danger btn-reject" data-id="' + guide.id + '">Từ chối</button>' +
                '</div>' +
                '</td>';
            tbody.appendChild(tr);
        });

        document.querySelectorAll('.btn-approve').forEach(function(btn) {
            btn.addEventListener('click', async function() {
                var id = this.getAttribute('data-id');
                await handleGuideAction(id, 'approve');
            });
        });

        document.querySelectorAll('.btn-reject').forEach(function(btn) {
            btn.addEventListener('click', async function() {
                var id = this.getAttribute('data-id');
                await handleGuideAction(id, 'reject');
            });
        });

    } catch(e) {}
}

async function handleGuideAction(id, action) {
    try {
        var res = await fetchApi('/api/guides/' + id + '/' + action, { method: 'PATCH' });
        if (res.ok) {
            showToast('Đã ' + (action === 'approve' ? 'duyệt' : 'từ chối') + ' hồ sơ', 'success');
            await loadPendingGuides();
            await loadDashboardStats();
        } else {
            showToast('Lỗi khi xử lý', 'error');
        }
    } catch(e) {
        showToast('Lỗi kết nối', 'error');
    }
}

async function loadActiveVouchers() {
    var container = document.getElementById('activeVouchersList');
    if (!container) return;

    try {
        var res = await fetchApi('/api/vouchers');
        if (!res.ok) {
            container.innerHTML = '<div class="admin-empty-state"><p>Không thể tải danh sách</p></div>';
            return;
        }
        var vouchers = await res.json();

        if (vouchers.length === 0) {
            container.innerHTML = '<div class="admin-empty-state"><i class="bx bx-purchase-tag-alt"></i><p>Chưa có voucher nào</p></div>';
            return;
        }

        container.innerHTML = vouchers.map(function(v) {
            var typeLabel = v.discount_type === 'percent' ? ('Giảm ' + v.discount_value + '%') : ('Giảm ' + new Intl.NumberFormat('vi-VN').format(v.discount_value) + '₫');
            return '<div class="card voucher-card">' +
                '<div>' +
                '<p class="voucher-code">' + v.code + '</p>' +
                '<p class="text-xs text-muted mt-1">' + typeLabel + ' - Hết hạn: ' + v.expiry_date + '</p>' +
                '</div>' +
                '<div class="flex gap-2">' +
                '<span class="badge ' + (v.is_active ? 'badge-success' : 'badge-danger') + '">' + (v.is_active ? 'Active' : 'Inactive') + '</span>' +
                '</div>' +
                '</div>';
        }).join('');
    } catch(e) {
        container.innerHTML = '<div class="admin-empty-state"><p>Lỗi kết nối</p></div>';
    }
}

function initViewSwitching() {
    var navLinks = document.querySelectorAll('.admin-nav-link[data-view]');
    var views = document.querySelectorAll('.admin-view');
    var headerTitle = document.getElementById('adminHeaderTitle');

    navLinks.forEach(function(link) {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            var viewId = this.getAttribute('data-view');

            navLinks.forEach(function(l) { l.classList.remove('active'); });
            this.classList.add('active');

            views.forEach(function(v) {
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
    var menuBtn = document.querySelector('.admin-menu-btn');
    var sidebar = document.getElementById('adminSidebar');
    var overlay = document.querySelector('.sidebar-overlay');

    if (menuBtn) {
        menuBtn.addEventListener('click', function() {
            sidebar.classList.add('active');
            overlay.classList.add('is-active');
        });
    }

    if (overlay) {
        overlay.addEventListener('click', closeSidebar);
    }
}

function closeSidebar() {
    var sidebar = document.getElementById('adminSidebar');
    var overlay = document.querySelector('.sidebar-overlay');
    if (sidebar) sidebar.classList.remove('active');
    if (overlay) overlay.classList.remove('is-active');
}

function initModals() {
    document.querySelectorAll('[data-modal-target]').forEach(function(btn) {
        btn.addEventListener('click', function() {
            var modalId = btn.getAttribute('data-modal-target');
            var modal = document.getElementById(modalId);
            if (modal) modal.classList.add('is-active');
        });
    });

    document.querySelectorAll('[data-modal-close]').forEach(function(btn) {
        btn.addEventListener('click', function() {
            var modal = btn.closest('.modal-overlay');
            if (modal) modal.classList.remove('is-active');
        });
    });

    document.querySelectorAll('.modal-overlay').forEach(function(overlay) {
        overlay.addEventListener('click', function(e) {
            if (e.target === overlay) overlay.classList.remove('is-active');
        });
    });
}

function initVoucherActions() {
    var form = document.getElementById('addVoucherForm');
    if (!form) return;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        var code = form.querySelector('[name="code"]').value.trim();
        var title = form.querySelector('[name="title"]').value.trim();
        var description = form.querySelector('[name="description"]').value.trim();
        var discountType = form.querySelector('[name="discount_type"]').value;
        var discountValue = parseFloat(form.querySelector('[name="discount_value"]').value);
        var expiryDate = form.querySelector('[name="expiry_date"]').value;

        if (!code || !title || !discountValue || !expiryDate) {
            showToast('Vui lòng điền đầy đủ thông tin', 'error');
            return;
        }

        var submitBtn = form.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Đang tạo...';

        try {
            var res = await fetchApi('/api/vouchers', {
                method: 'POST',
                body: JSON.stringify({
                    code: code,
                    title: title,
                    description: description,
                    discount_type: discountType,
                    discount_value: discountValue,
                    expiry_date: expiryDate,
                    is_active: true
                })
            });

            if (res.ok) {
                showToast('Tạo Voucher thành công!', 'success');
                form.reset();
                await loadActiveVouchers();
            } else {
                var err = await res.json();
                showToast(err.detail || 'Lỗi khi tạo voucher', 'error');
            }
        } catch(e) {
            showToast('Lỗi kết nối máy chủ', 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Tạo Voucher ngay';
        }
    });
}

function initSettingsToggles() {
    document.querySelectorAll('.toggle-switch input').forEach(function(toggle) {
        toggle.addEventListener('change', function () {
            var state = this.checked ? 'Bật' : 'Tắt';
            showToast('Đã ' + state + ' cài đặt', 'info');
        });
    });
}

function showToast(message, type) {
    type = type || 'success';
    var container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    var toast = document.createElement('div');
    toast.className = 'toast toast-' + type;

    var icon = 'bx-check-circle';
    if (type === 'error') icon = 'bx-error-circle';
    if (type === 'info') icon = 'bx-info-circle';

    toast.innerHTML =
        '<i class="bx ' + icon + ' toast-icon"></i>' +
        '<span>' + message + '</span>' +
        '<button class="toast-close">&times;</button>';

    container.appendChild(toast);

    toast.querySelector('.toast-close').addEventListener('click', function() {
        toast.classList.add('toast-out');
        setTimeout(function() { toast.remove(); }, 300);
    });

    setTimeout(function() {
        if (toast.parentNode) {
            toast.classList.add('toast-out');
            setTimeout(function() { toast.remove(); }, 300);
        }
    }, 3000);
}

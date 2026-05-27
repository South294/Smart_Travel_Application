function getBaseUrl() {
    return window.location.pathname.includes('/admin/') ? '../' : '';
}

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
        window.location.href = getBaseUrl() + 'auth.html';
    }
    return res;
}

document.addEventListener('DOMContentLoaded', async function () {
    await ensureAdminAccess();
    initViewSwitching();
    initSidebar();
    initModals();
    initGuideAssignments();
    initVoucherActions();
    initSettingsToggles();
    await loadAdminProfile();
    await loadDashboardStats();
    await loadUsers();
    await loadPendingGuides();
    await loadGuidesList();
    await loadBookings();
    await loadActiveVouchers();
    await loadAdminSettings();
    initDashboardInteractions();
    await loadAdminDashboardData();
});

async function ensureAdminAccess() {
    var token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = getBaseUrl() + 'auth.html';
        return;
    }

    try {
        var res = await fetchApi('/api/users/me');
        if (!res.ok) {
            window.location.href = getBaseUrl() + 'auth.html';
            return;
        }
        var user = await res.json();
        if (!user || user.role !== 'admin') {
            localStorage.removeItem('access_token');
            localStorage.removeItem('isLoggedIn');
            showToast('Ban khong co quyen truy cap trang admin', 'error');
            setTimeout(function() { window.location.href = getBaseUrl() + 'index.html'; }, 1200);
        }
    } catch (e) {
        window.location.href = getBaseUrl() + 'auth.html';
    }
}

async function loadAdminProfile() {
    try {
        var res = await fetchApi('/api/users/me');
        if (!res.ok) return;
        var user = await res.json();
        if (!user) return;

        var nameEl = document.getElementById('adminUserName');
        var roleEl = document.getElementById('adminUserRole');
        var avatarEl = document.getElementById('adminUserAvatar');
        var name = user.full_name || user.email || 'Admin';
        var initials = getInitials(name);

        if (nameEl) nameEl.textContent = name;
        if (roleEl) roleEl.textContent = user.role === 'admin' ? 'Quan tri vien' : (user.role || 'User');
        if (avatarEl) avatarEl.textContent = initials;
    } catch (e) {}
}

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

async function loadUsers() {
    var tbody = document.querySelector('#usersView tbody');
    if (!tbody) return;

    try {
        var res = await fetchApi('/api/admin/users');
        if (!res.ok) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding: 24px;">Không thể tải danh sách</td></tr>';
            return;
        }

        var users = await res.json();
        if (!Array.isArray(users) || users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding: 24px;">Chưa có người dùng</td></tr>';
            return;
        }

        tbody.innerHTML = users.map(function(user) {
            var name = user.full_name || user.email || 'Người dùng';
            var initials = getInitials(name);
            var role = normalizeRole(user.role);
            var status = user.is_active === false ? 'Bị khóa' : 'Hoạt động';
            var statusClass = user.is_active === false ? 'badge badge-danger' : 'badge badge-success';
            var createdAt = formatDate(user.created_at);
            return (
                '<tr>' +
                '<td>' +
                '<div class="flex items-center gap-3">' +
                '<div class="user-avatar user-avatar-sm">' + initials + '</div>' +
                '<div>' +
                '<p class="font-bold text-sm">' + escapeHtml(name) + '</p>' +
                '<p class="text-xs text-muted">' + escapeHtml(user.email || '') + '</p>' +
                '</div>' +
                '</div>' +
                '</td>' +
                '<td>' + role.badge + '</td>' +
                '<td><span class="' + statusClass + '">' + status + '</span></td>' +
                '<td>' + createdAt + '</td>' +
                '<td>' +
                '<div class="action-group">' +
                '<button class="btn btn-sm btn-outline btn-toggle-user" data-id="' + user.id + '" data-active="' + (user.is_active !== false) + '">' +
                (user.is_active === false ? 'Mở khóa' : 'Khóa') +
                '</button>' +
                '</div>' +
                '</td>' +
                '</tr>'
            );
        }).join('');

        document.querySelectorAll('.btn-toggle-user').forEach(function(btn) {
            btn.addEventListener('click', async function() {
                var id = this.getAttribute('data-id');
                var isActive = this.getAttribute('data-active') === 'true';
                await toggleUserStatus(id, !isActive);
            });
        });
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding: 24px;">Lỗi kết nối</td></tr>';
    }
}

async function toggleUserStatus(userId, makeActive) {
    try {
        var res = await fetchApi('/api/admin/users/' + userId + '/status', {
            method: 'PATCH',
            body: JSON.stringify({ is_active: makeActive })
        });
        if (res.ok) {
            showToast(makeActive ? 'Đã mở khóa tài khoản' : 'Đã khóa tài khoản', 'success');
            await loadUsers();
        } else {
            var errText = 'Lỗi khi cập nhật';
            try {
                var err = await res.json();
                errText = err.detail || errText;
            } catch (e) {}
            showToast(errText, 'error');
        }
    } catch (e) {
        showToast('Lỗi kết nối', 'error');
    }
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

async function loadGuidesList() {
    var tbody = document.getElementById('guidesListBody');
    if (!tbody) return;

    try {
        var res = await fetchApi('/api/admin/guides');
        if (!res.ok) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding: 24px;">Không thể tải danh sách</td></tr>';
            return;
        }
        var guides = await res.json();
        var badge = document.getElementById('guidesCountBadge');
        if (badge) badge.textContent = guides.length + ' hướng dẫn viên';

        if (guides.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding: 24px;">Chưa có hướng dẫn viên</td></tr>';
            return;
        }

        tbody.innerHTML = guides.map(function(guide) {
            var areas = (guide.areas || []).join(', ') || '--';
            var languages = (guide.languages || []).join(', ') || '--';
            var status = guide.status || 'approved';
            var statusBadge = status === 'approved'
                ? '<span class="badge badge-success">Đã duyệt</span>'
                : (status === 'pending' ? '<span class="badge badge-warning">Chờ duyệt</span>' : '<span class="badge badge-danger">Từ chối</span>');
            var assignBtn = status === 'approved'
                ? '<button class="btn btn-sm btn-outline btn-assign" data-id="' + guide.id + '" data-name="' + escapeHtml(guide.name || '') + '">Tạo chuyến</button>'
                : '';
            return (
                '<tr>' +
                '<td>' +
                '<div class="user-info-table">' +
                '<div class="user-avatar-sm">' + getInitials(guide.name || 'GD') + '</div>' +
                '<div><span class="font-bold">' + escapeHtml(guide.name || 'Hướng dẫn viên') + '</span></div>' +
                '</div>' +
                '</td>' +
                '<td>' + escapeHtml(areas) + '</td>' +
                '<td>' + escapeHtml(languages) + '</td>' +
                '<td>' + statusBadge + '</td>' +
                '<td>' +
                '<div class="action-group">' +
                assignBtn +
                '<button class="btn btn-sm btn-outline btn-approve" data-id="' + guide.id + '">Duyệt</button>' +
                '<button class="btn btn-sm btn-outline-danger btn-reject" data-id="' + guide.id + '">Từ chối</button>' +
                '</div>' +
                '</td>' +
                '</tr>'
            );
        }).join('');

        document.querySelectorAll('#guidesListView .btn-approve').forEach(function(btn) {
            btn.addEventListener('click', async function() {
                var id = this.getAttribute('data-id');
                await handleGuideAction(id, 'approve');
                await loadGuidesList();
            });
        });

        document.querySelectorAll('#guidesListView .btn-reject').forEach(function(btn) {
            btn.addEventListener('click', async function() {
                var id = this.getAttribute('data-id');
                await handleGuideAction(id, 'reject');
                await loadGuidesList();
            });
        });

        document.querySelectorAll('#guidesListView .btn-assign').forEach(function(btn) {
            btn.addEventListener('click', function() {
                openAssignGuideModal(btn.getAttribute('data-id'));
            });
        });
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding: 24px;">Lỗi kết nối</td></tr>';
    }
}

function initGuideAssignments() {
    var form = document.getElementById('assignGuideForm');
    if (!form) return;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        var payload = {
            guide_id: document.getElementById('assignGuideId').value,
            tour_title: document.getElementById('assignTourTitle').value.trim(),
            destination: document.getElementById('assignDestination').value.trim(),
            trip_date: document.getElementById('assignTripDate').value,
            earning: parseFloat(document.getElementById('assignEarning').value) || 0
        };

        if (!payload.guide_id || !payload.tour_title || !payload.destination || !payload.trip_date) {
            showToast('Vui lòng nhập đầy đủ thông tin', 'error');
            return;
        }

        var submitBtn = form.querySelector('button[type="submit"]');
        var originalText = submitBtn.textContent;
        submitBtn.textContent = 'Đang tạo...';
        submitBtn.disabled = true;

        try {
            var res = await fetchApi('/api/admin/guides/assign', {
                method: 'POST',
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                showToast('Đã tạo chuyến cho hướng dẫn viên', 'success');
                closeModalById('assignGuideModal');
                form.reset();
            } else {
                var err = await res.json();
                showToast(err.detail || 'Không thể tạo chuyến', 'error');
            }
        } catch (e) {
            showToast('Lỗi kết nối', 'error');
        } finally {
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
        }
    });
}

function openAssignGuideModal(guideId) {
    var modal = document.getElementById('assignGuideModal');
    var idInput = document.getElementById('assignGuideId');
    if (idInput) idInput.value = guideId || '';
    if (modal) modal.classList.add('is-active');
}

function closeModalById(id) {
    var modal = document.getElementById(id);
    if (modal) modal.classList.remove('is-active');
}

async function handleGuideAction(id, action) {
    try {
        var res = await fetchApi('/api/guides/' + id + '/' + action, { method: 'PATCH' });
        if (res.ok) {
            showToast('Đã ' + (action === 'approve' ? 'duyệt' : 'từ chối') + ' hồ sơ', 'success');
            await loadPendingGuides();
            await loadDashboardStats();
            await loadGuidesList();
        } else {
            var errText = 'Lỗi khi xử lý';
            try {
                var err = await res.json();
                errText = err.detail || errText;
            } catch (e) {}
            showToast(errText, 'error');
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

            if (window.innerWidth <= 768 && window.innerWidth > 420) {
                closeSidebar();
            }
        });
    });
}

function initDashboardInteractions() {
    document.querySelectorAll('.stat-card[data-view-target]').forEach(function(card) {
        card.addEventListener('click', function() {
            var target = this.getAttribute('data-view-target');
            switchAdminView(target);
        });
    });

    document.querySelectorAll('.admin-tab-group .admin-tab').forEach(function(tab) {
        tab.addEventListener('click', function() {
            document.querySelectorAll('.admin-tab-group .admin-tab').forEach(function(t) {
                t.classList.remove('active');
            });
            tab.classList.add('active');
            var mode = tab.getAttribute('data-chart');
            updateChartSummary(mode);
        });
    });

    var viewAllBtn = document.getElementById('viewAllActivities');
    if (viewAllBtn) {
        viewAllBtn.addEventListener('click', function() {
            var modal = document.getElementById('activityModal');
            if (modal) modal.classList.add('is-active');
        });
    }

    var reloadToursBtn = document.getElementById('reloadToursBtn');
    if (reloadToursBtn) {
        reloadToursBtn.addEventListener('click', async function() {
            reloadToursBtn.disabled = true;
            var originalText = reloadToursBtn.innerHTML;
            reloadToursBtn.innerHTML = '<i class="bx bx-loader-alt"></i> Đang tải';
            await loadDemoTours();
            setTimeout(function() {
                reloadToursBtn.disabled = false;
                reloadToursBtn.innerHTML = originalText;
                showToast('Đã làm mới danh sách tour', 'success');
            }, 300);
        });
    }

    var reloadBookingsBtn = document.getElementById('reloadBookingsBtn');
    if (reloadBookingsBtn) {
        reloadBookingsBtn.addEventListener('click', async function() {
            reloadBookingsBtn.disabled = true;
            var originalText = reloadBookingsBtn.innerHTML;
            reloadBookingsBtn.innerHTML = '<i class="bx bx-loader-alt"></i> Đang tải';
            await loadBookings();
            setTimeout(function() {
                reloadBookingsBtn.disabled = false;
                reloadBookingsBtn.innerHTML = originalText;
                showToast('Đã làm mới danh sách booking', 'success');
            }, 300);
        });
    }
}

function switchAdminView(viewId) {
    var navLinks = document.querySelectorAll('.admin-nav-link[data-view]');
    var views = document.querySelectorAll('.admin-view');
    var headerTitle = document.getElementById('adminHeaderTitle');

    navLinks.forEach(function(l) {
        l.classList.toggle('active', l.getAttribute('data-view') === viewId);
    });

    views.forEach(function(v) {
        v.classList.toggle('is-active', v.id === viewId);
    });

    var activeLink = document.querySelector('.admin-nav-link[data-view][class*="active"]');
    if (headerTitle && activeLink) headerTitle.textContent = activeLink.textContent.trim();
}

async function loadAdminDashboardData() {
    renderActivityList(getDemoActivities());
    updateChartSummary('week');
    await loadDemoTours();
    renderReportCards(getDemoReports());
    renderTopTours(getDemoTopTours());
}

function updateChartSummary(mode) {
    var summary = document.getElementById('chartSummary');
    if (!summary) return;
    summary.textContent = mode === 'month'
        ? 'Doanh thu tháng: 2.4 tỉ ₫ (tăng 8.5%)'
        : 'Doanh thu tuần: 620 triệu ₫ (tăng 5.2%)';
}

function renderActivityList(activities) {
    var list = document.getElementById('activityList');
    var modalList = document.getElementById('activityModalList');
    if (list) list.innerHTML = activities.slice(0, 4).map(renderActivityItem).join('');
    if (modalList) modalList.innerHTML = activities.map(renderActivityItem).join('');
}

function renderActivityItem(item) {
    return (
        '<div class="activity-item">' +
        '<div class="activity-dot ' + item.dot + '"></div>' +
        '<div class="flex-1">' +
        '<p class="text-sm font-semibold">' + escapeHtml(item.title) + '</p>' +
        '<p class="activity-time">' + escapeHtml(item.time) + '</p>' +
        '</div>' +
        '</div>'
    );
}

async function loadDemoTours() {
    var tbody = document.getElementById('toursTableBody');
    if (!tbody) return;
    var tours = getDemoTours();
    window.__demoTours = tours;
    tbody.innerHTML = tours.map(function(tour, index) {
        var statusBadge = tour.is_active ? '<span class="badge badge-success">Đang mở</span>' : '<span class="badge badge-danger">Tạm dừng</span>';
        return (
            '<tr>' +
            '<td>' +
            '<div class="user-info-table">' +
            '<div class="user-avatar-sm">' + escapeHtml(tour.title.slice(0, 2).toUpperCase()) + '</div>' +
            '<div><span class="font-bold">' + escapeHtml(tour.title) + '</span></div>' +
            '</div>' +
            '</td>' +
            '<td>' + escapeHtml(tour.category) + '</td>' +
            '<td>' + formatCurrency(tour.price) + '</td>' +
            '<td>' + statusBadge + '</td>' +
            '<td><button class="btn btn-sm btn-outline btn-tour-detail" data-index="' + index + '">Chi tiết</button></td>' +
            '</tr>'
        );
    }).join('');

    document.querySelectorAll('.btn-tour-detail').forEach(function(btn) {
        btn.addEventListener('click', function() {
            var index = parseInt(btn.getAttribute('data-index'), 10);
            var tour = window.__demoTours && window.__demoTours[index];
            if (tour) openTourDetail(tour);
        });
    });
}

async function loadBookings() {
    var tbody = document.getElementById('bookingsTableBody');
    if (!tbody) return;

    try {
        var res = await fetchApi('/api/admin/bookings');
        if (!res.ok) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 24px;">Không thể tải danh sách</td></tr>';
            return;
        }
        var bookings = await res.json();
        if (!Array.isArray(bookings) || bookings.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 24px;">Chưa có booking</td></tr>';
            return;
        }

        tbody.innerHTML = bookings.map(function(booking) {
            var statusBadge = booking.status === 'confirmed'
                ? '<span class="badge badge-success">Đã xác nhận</span>'
                : (booking.status === 'cancelled' ? '<span class="badge badge-danger">Đã hủy</span>' : '<span class="badge badge-warning">Chờ xử lý</span>');
            var actions = '';
            if (booking.status === 'pending') {
                actions = '<div class="action-group">' +
                    '<button class="btn btn-sm btn-outline btn-booking-approve" data-id="' + booking.id + '">Duyệt</button>' +
                    '<button class="btn btn-sm btn-outline-danger btn-booking-cancel" data-id="' + booking.id + '">Hủy</button>' +
                    '</div>';
            } else {
                actions = '<span class="text-xs text-muted">Đã xử lý</span>';
            }
            return (
                '<tr>' +
                '<td>#' + escapeHtml(booking.id.slice(-6).toUpperCase()) + '</td>' +
                '<td>' + escapeHtml(booking.tour_title || 'Tour') + '</td>' +
                '<td>' + escapeHtml(booking.travel_date || '--') + '</td>' +
                '<td>' + statusBadge + '</td>' +
                '<td>' + formatCurrency(booking.total_amount) + '</td>' +
                '<td>' + actions + '</td>' +
                '</tr>'
            );
        }).join('');

        document.querySelectorAll('.btn-booking-approve').forEach(function(btn) {
            btn.addEventListener('click', async function() {
                var id = this.getAttribute('data-id');
                await updateBookingStatus(id, 'confirmed');
            });
        });

        document.querySelectorAll('.btn-booking-cancel').forEach(function(btn) {
            btn.addEventListener('click', async function() {
                var id = this.getAttribute('data-id');
                await updateBookingStatus(id, 'cancelled');
            });
        });
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 24px;">Lỗi kết nối</td></tr>';
    }
}

async function updateBookingStatus(id, status) {
    try {
        var res = await fetchApi('/api/admin/bookings/' + id + '/status', {
            method: 'PATCH',
            body: JSON.stringify({ status: status })
        });
        if (res.ok) {
            showToast(status === 'confirmed' ? 'Đã duyệt booking' : 'Đã hủy booking', 'success');
            await loadBookings();
        } else {
            var errText = 'Không thể cập nhật booking';
            try {
                var err = await res.json();
                errText = err.detail || errText;
            } catch (e) {}
            showToast(errText, 'error');
        }
    } catch (e) {
        showToast('Lỗi kết nối', 'error');
    }
}

function openTourDetail(tour) {
    var modal = document.getElementById('tourDetailModal');
    if (!modal) return;
    setText('tourDetailName', tour.title);
    setText('tourDetailCategory', tour.category);
    setText('tourDetailPrice', formatCurrency(tour.price));
    setText('tourDetailStatus', tour.is_active ? 'Đang mở' : 'Tạm dừng');
    setText('tourDetailDuration', tour.duration || '2N1Đ');
    setText('tourDetailDesc', tour.description || 'Tour trải nghiệm nổi bật với lịch trình được tối ưu.');
    modal.classList.add('is-active');
}

function setText(id, value) {
    var el = document.getElementById(id);
    if (el) el.textContent = value || '--';
}

function renderReportCards(items) {
    var container = document.getElementById('reportCards');
    if (!container) return;
    container.innerHTML = items.map(function(item) {
        return (
            '<div class="report-card">' +
            '<p class="text-xs text-muted">' + escapeHtml(item.label) + '</p>' +
            '<p class="font-bold text-lg">' + escapeHtml(item.value) + '</p>' +
            '<p class="text-xs ' + (item.trend > 0 ? 'text-success' : 'text-danger') + '">' +
            (item.trend > 0 ? '+' : '') + item.trend + '%</p>' +
            '</div>'
        );
    }).join('');
}

function renderTopTours(items) {
    var tbody = document.getElementById('topToursBody');
    if (!tbody) return;
    tbody.innerHTML = items.map(function(item) {
        return (
            '<tr>' +
            '<td>' + escapeHtml(item.title) + '</td>' +
            '<td>' + item.bookings + '</td>' +
            '<td>' + formatCurrency(item.revenue) + '</td>' +
            '</tr>'
        );
    }).join('');
}

function getDemoActivities() {
    return [
        { title: 'Vũ Văn Sơn đã được duyệt làm HDV', time: '5 phút trước', dot: 'activity-dot-success' },
        { title: 'Booking mới: Tour Hạ Long #BK928', time: '12 phút trước', dot: 'activity-dot-info' },
        { title: 'Nguyễn Thanh Nam yêu cầu rút tiền: 2.000.000₫', time: '45 phút trước', dot: 'activity-dot-warning' },
        { title: 'Hủy booking: #BK812 - Lý do: Đổi lịch', time: '1 giờ trước', dot: 'activity-dot-danger' },
        { title: 'Voucher SUMMER20 vừa được tạo', time: '2 giờ trước', dot: 'activity-dot-info' },
        { title: 'Guide mới gửi hồ sơ: Trần Thu Hà', time: '3 giờ trước', dot: 'activity-dot-warning' }
    ];
}

function getDemoTours() {
    return [
        { title: 'Vịnh Hạ Long 2N1Đ', category: 'Biển', price: 2500000, is_active: true, duration: '2N1Đ', description: 'Hành trình du thuyền, ngắm vịnh và trải nghiệm hải sản địa phương.' },
        { title: 'Mộc Châu Mộng Mơ 3N2Đ', category: 'Núi', price: 3500000, is_active: true, duration: '3N2Đ', description: 'Khám phá cao nguyên, đồi chè và homestay bản địa.' },
        { title: 'Ninh Bình Tràng An 2N1Đ', category: 'Văn hóa', price: 1800000, is_active: false, duration: '2N1Đ', description: 'Tràng An - Bái Đính - Tam Cốc, tour văn hóa lịch sử.' },
        { title: 'Sapa Fansipan 3N2Đ', category: 'Trekking', price: 3200000, is_active: true, duration: '3N2Đ', description: 'Chinh phục Fansipan, trải nghiệm bản Cát Cát.' }
    ];
}

function getDemoReports() {
    return [
        { label: 'Doanh thu hôm nay', value: '320.000.000₫', trend: 6.2 },
        { label: 'Booking tuần', value: '128 đơn', trend: 4.1 },
        { label: 'Tỉ lệ hủy', value: '2.3%', trend: -0.8 },
        { label: 'Khách quay lại', value: '18.5%', trend: 3.4 }
    ];
}

function getDemoTopTours() {
    return [
        { title: 'Vịnh Hạ Long 2N1Đ', bookings: 42, revenue: 126000000 },
        { title: 'Mộc Châu Mộng Mơ 3N2Đ', bookings: 31, revenue: 108500000 },
        { title: 'Sapa Fansipan 3N2Đ', bookings: 24, revenue: 76800000 }
    ];
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

    var saveBtn = document.getElementById('saveSettingsBtn');
    if (saveBtn) {
        saveBtn.addEventListener('click', async function() {
            await saveAdminSettings();
        });
    }
}

async function loadAdminSettings() {
    try {
        var res = await fetchApi('/api/admin/settings');
        if (!res.ok) return;
        var settings = await res.json();
        setToggleValue('settingMaintenance', settings.maintenance_mode);
        setToggleValue('settingAutoGuide', settings.auto_approve_guides);
        setToggleValue('settingEmailBooking', settings.email_new_booking);
    } catch (e) {}
}

async function saveAdminSettings() {
    var payload = {
        maintenance_mode: getToggleValue('settingMaintenance'),
        auto_approve_guides: getToggleValue('settingAutoGuide'),
        email_new_booking: getToggleValue('settingEmailBooking')
    };

    var btn = document.getElementById('saveSettingsBtn');
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Đang lưu...';
    }

    try {
        var res = await fetchApi('/api/admin/settings', {
            method: 'PUT',
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            showToast('Đã lưu cài đặt hệ thống', 'success');
        } else {
            var errText = 'Không thể lưu cài đặt';
            try {
                var err = await res.json();
                errText = err.detail || errText;
            } catch (e) {}
            showToast(errText, 'error');
        }
    } catch (e) {
        showToast('Lỗi kết nối', 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = 'Lưu tất cả cài đặt';
        }
    }
}

function setToggleValue(id, value) {
    var el = document.getElementById(id);
    if (el) el.checked = value === true;
}

function getToggleValue(id) {
    var el = document.getElementById(id);
    return el ? !!el.checked : false;
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

    var icons = {
        success: 'bx-check-circle',
        error: 'bx-error-circle',
        info: 'bx-info-circle'
    };

    var iconEl = document.createElement('i');
    iconEl.className = 'bx ' + (icons[type] || icons.success) + ' toast-icon';
    
    var spanEl = document.createElement('span');
    spanEl.textContent = message;
    
    var closeBtn = document.createElement('button');
    closeBtn.className = 'toast-close';
    closeBtn.innerHTML = '&times;';

    toast.appendChild(iconEl);
    toast.appendChild(spanEl);
    toast.appendChild(closeBtn);

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

function normalizeRole(role) {
    if (role === 'admin') {
        return { badge: '<span class="role-badge role-admin"><i class="bx bx-shield-quarter"></i> Admin</span>' };
    }
    if (role === 'guide') {
        return { badge: '<span class="role-badge role-guide"><i class="bx bx-map-pin"></i> Guide</span>' };
    }
    return { badge: '<span class="role-badge role-user"><i class="bx bx-user"></i> User</span>' };
}

function formatDate(value) {
    if (!value) return '--';
    var date = new Date(value);
    if (Number.isNaN(date.getTime())) return '--';
    var day = String(date.getDate()).padStart(2, '0');
    var month = String(date.getMonth() + 1).padStart(2, '0');
    var year = date.getFullYear();
    return day + '/' + month + '/' + year;
}

function getInitials(name) {
    if (!name) return 'ST';
    var parts = name.trim().split(/\s+/).filter(Boolean);
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function escapeHtml(value) {
    return String(value || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function formatCurrency(value) {
    if (value == null) return '--';
    return new Intl.NumberFormat('vi-VN').format(value) + '₫';
}

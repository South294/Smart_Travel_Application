async function fetchApi(url, options = {}) {
    const token = localStorage.getItem('access_token');
    const headers = { 'Content-Type': 'application/json', ...options.headers };
    if (token) headers['Authorization'] = 'Bearer ' + token;
    const res = await fetch('http://localhost:8000' + url, { ...options, headers });
    if (res.status === 401) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('isLoggedIn');
        localStorage.removeItem('userRole');
    }
    return res;
}

document.addEventListener('DOMContentLoaded', async function() {
  initNavigation();
  initMobileMenu();
  await initAuthState();
  await initProfileData();
  initPreferenceChips();
  initCustomPreferenceActions();
  initTripItemModalAccess();
  initProfileNavSpy();
  initLogoutAction();
  initPaymentOptions();
  initModals();
  initUploadAreas();
  await initPromoClaim();
  initAdminSidebar();
  initProfileSave();
  initGuideRegisterForm();
  initGuideHireActions();
  await initGuidesDirectory();
  await initGuideDashboard();
  initCheckoutData();
  initCheckoutPayment();
});

function initNavigation() {
  var currentPath = window.location.pathname;
  var navLinks = document.querySelectorAll('.nav-link');

  navLinks.forEach(function(link) {
    var href = link.getAttribute('href');
    link.classList.remove('active');

    var isHomePage = (currentPath.endsWith('/') || currentPath.endsWith('index.html')) && href === 'index.html';
    var isCurrentPage = currentPath.endsWith(href) && href !== 'index.html';

    if (isHomePage || isCurrentPage) {
      link.classList.add('active');
    }
  });
}

function initMobileMenu() {
  var menuBtn = document.querySelector('.mobile-menu-btn');
  var navLinks = document.querySelector('.nav-links');

  if (!menuBtn || !navLinks) return;

  menuBtn.addEventListener('click', function() {
    navLinks.classList.toggle('is-active');
    var icon = menuBtn.querySelector('i');
    if (navLinks.classList.contains('is-active')) {
      icon.className = 'bx bx-x';
    } else {
      icon.className = 'bx bx-menu';
    }
  });

  document.addEventListener('click', function(e) {
    if (!menuBtn.contains(e.target) && !navLinks.contains(e.target)) {
      navLinks.classList.remove('is-active');
      var icon = menuBtn.querySelector('i');
      if (icon) icon.className = 'bx bx-menu';
    }
  });
}

async function initAuthState() {
  var isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
  var containers = document.querySelectorAll('.nav-actions');

  if (!isLoggedIn) return;

  var profile = await getStoredUserProfile();
  if (!profile.email) return;

  var initials = getInitials(profile.full_name || profile.email || 'ST');
  var role = profile.role || localStorage.getItem('userRole') || '';
  var showGuideDashboard = false;

  if (role === 'guide') {
    try {
      var guideRes = await fetchApi('/api/guides/me');
      if (guideRes.ok) {
        var guideProfile = await guideRes.json();
        showGuideDashboard = guideProfile && guideProfile.status === 'approved';
      }
    } catch (e) {}
  }

  containers.forEach(function(container) {
    if (container.closest('.admin-page')) return;
    var links = '';
    if (showGuideDashboard) {
      links += '<a href="guide-dashboard.html" class="btn btn-ghost">HDV Dashboard</a>';
    }
    links += '<a href="profile.html" class="user-avatar" title="Trang cá nhân">' + initials + '</a>';
    container.innerHTML = links;
  });
}

async function initProfileData() {
  var isProfilePage = window.location.pathname.endsWith('profile.html');
  if (!isProfilePage) return;

  var isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
  if (!isLoggedIn) {
    window.location.href = 'auth.html';
    return;
  }

  var profile = await getStoredUserProfile();
  var fullName = profile.full_name;
  var email = profile.email;
  var initials = getInitials(fullName || email);

  setTextBySelector('.profile-display-name', fullName);
  setTextBySelector('.profile-display-email', email);
  setInputValueBySelector('.profile-input-name', fullName);
  setInputValueBySelector('.profile-input-email', email);
  setInputValueBySelector('.profile-input-phone', profile.phone || '');
  setInputValueBySelector('.profile-input-birth', profile.birth_date || '');
  setInputValueBySelector('.profile-input-address', profile.address || '');
  setSelectValueBySelector('.profile-input-gender', profile.gender || '');
  setSelectValueBySelector('.profile-setting-language', profile.settings?.language || 'vi');
  setCheckedBySelector('.profile-setting-email', profile.settings?.email_notifications !== false);
  setCheckedBySelector('.profile-setting-sms', profile.settings?.sms_notifications === true);
  setCheckedBySelector('.profile-setting-ai', profile.settings?.ai_personalization !== false);

  document.querySelectorAll('.profile-initials').forEach(function(el) {
    el.textContent = initials;
  });

  syncPreferenceChips(profile.preferences || []);
  renderCustomPreferenceChips(profile.custom_preferences || []);
  await renderSavedVouchers();
  await renderMyBookings();
}

async function renderMyBookings() {
  var container = document.querySelector('#my-trips');
  if (!container) return;

  var listWrap = container.querySelector('.trip-list');
  if (!listWrap) return;

  try {
    var res = await fetchApi('/api/bookings/me');
    if (!res.ok) {
      listWrap.innerHTML = '<div class="text-muted text-sm">Không thể tải danh sách chuyến đi.</div>';
      return;
    }

    var bookings = await res.json();
    if (!Array.isArray(bookings) || bookings.length === 0) {
      listWrap.innerHTML = '<div class="text-muted text-sm">Chưa có chuyến đi nào.</div>';
      return;
    }

    listWrap.innerHTML = bookings.map(function(booking) {
      var statusText = mapBookingStatus(booking.status);
      var statusClass = mapBookingStatusClass(booking.status);
      return (
        '<div class="trip-item flex items-center gap-4 pb-4 border-b">' +
        '<div class="icon-circle icon-circle-primary"><i class="bx bx-map-pin"></i></div>' +
        '<div class="flex-1">' +
        '<h4 class="font-semibold">' + escapeHtml(booking.tour_title || 'Tour') + '</h4>' +
        '<p class="text-muted text-sm">' + escapeHtml(booking.travel_date || '--') + '</p>' +
        '</div>' +
        '<span class="badge ' + statusClass + '">' + statusText + '</span>' +
        '</div>'
      );
    }).join('');
  } catch (e) {
    listWrap.innerHTML = '<div class="text-muted text-sm">Không thể tải danh sách chuyến đi.</div>';
  }
}

function mapBookingStatus(status) {
  if (status === 'confirmed') return 'Đã xác nhận';
  if (status === 'cancelled') return 'Đã hủy';
  return 'Chờ xử lý';
}

function mapBookingStatusClass(status) {
  if (status === 'confirmed') return 'badge-success';
  if (status === 'cancelled') return 'badge-danger';
  return 'badge-warning';
}

function initLogoutAction() {
  document.querySelectorAll('[data-logout]').forEach(function(link) {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      localStorage.removeItem('isLoggedIn');
      localStorage.removeItem('userProfile');
      localStorage.removeItem('userRole');
      showToast('Ban da dang xuat thanh cong', 'success');
      setTimeout(function() { window.location.href = 'auth.html'; }, 800);
    });
  });
}

async function getStoredUserProfile() {
  try {
    const res = await fetchApi('/api/users/me');
    if (res.ok) {
      return await res.json();
    }
  } catch (e) {
  }
  return {};
}

async function getStoredSavedVouchers() {
  try {
    const res = await fetchApi('/api/vouchers/me');
    if (res.ok) {
      return await res.json();
    }
  } catch(e) {}
  return [];
}

async function saveVoucher(voucherCode) {
  try {
    const res = await fetchApi(`/api/vouchers/${voucherCode}/claim`, { method: 'POST' });
    return res.ok;
  } catch (e) {
    return false;
  }
}

function normalizeVoucher(voucher) {
  if (!voucher) return null;

  if (typeof voucher === 'string') {
    var codeFromString = voucher.trim();
    if (!codeFromString) return null;
    return {
      code: codeFromString,
      title: 'Voucher ' + codeFromString,
      description: 'Uu dai da duoc luu vao vi cua ban.',
      expiry: 'Con hieu luc'
    };
  }

  if (!voucher.code) return null;

  return {
    code: String(voucher.code).trim(),
    title: voucher.title || ('Voucher ' + voucher.code),
    description: voucher.description || 'Uu dai da duoc luu vao vi cua ban.',
    expiry: voucher.expiry || 'Con hieu luc'
  };
}

async function renderSavedVouchers() {
  var container = document.getElementById('saved-vouchers-list');
  if (!container) return;

  var saved = await getStoredSavedVouchers();
  if (saved.length === 0) {
    container.innerHTML =
      '<div class="empty-state">' +
      '<i class="bx bx-wallet"></i>' +
      '<p>Ban chua luu voucher nao. Hay vao trang khuyen mai de nhan uu dai.</p>' +
      '</div>';
    return;
  }

  container.innerHTML = saved.map(function(voucher) {
    return (
      '<div class="saved-voucher-card">' +
      '<div class="saved-voucher-top">' +
      '<h4>' + voucher.title + '</h4>' +
      '<span class="badge badge-success">' + voucher.code + '</span>' +
      '</div>' +
      '<p class="text-muted text-sm">' + (voucher.description || 'Uu dai da duoc luu vao vi cua ban.') + '</p>' +
      '<div class="saved-voucher-footer">' +
      '<span class="text-sm text-warning"><i class="bx bx-time"></i> ' + (voucher.expiry_date || 'Con hieu luc') + '</span>' +
      '</div>' +
      '</div>'
    );
  }).join('');
}

function initPreferenceChips() {
  var chips = document.querySelectorAll('[data-pref-tag]');
  if (chips.length === 0) return;

  chips.forEach(function(chip) {
    chip.addEventListener('click', function() {
      this.classList.toggle('is-active');
    });
  });
}

function initCustomPreferenceActions() {
  var addBtn = document.querySelector('.profile-add-pref-btn');
  var input = document.querySelector('.profile-custom-pref-input');
  if (!addBtn || !input) return;

  addBtn.addEventListener('click', function() {
    addCustomPreferenceFromInput();
  });

  input.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      addCustomPreferenceFromInput();
    }
  });
}

function initTripItemModalAccess() {
  var items = document.querySelectorAll('.trip-clickable[data-modal-target]');
  if (items.length === 0) return;

  items.forEach(function(item) {
    item.addEventListener('keydown', function(e) {
      if (e.key !== 'Enter' && e.key !== ' ') return;
      e.preventDefault();
      var target = item.getAttribute('data-modal-target');
      if (target) openModal(target);
    });
  });
}

function initProfileNavSpy() {
  var navLinks = document.querySelectorAll('.profile-nav-link[href^="#"]');
  var navContainer = document.querySelector('.profile-nav');
  if (navLinks.length === 0) return;

  function activateByHash(hash) {
    var activeLink = null;
    navLinks.forEach(function(link) {
      var isActive = link.getAttribute('href') === hash;
      link.classList.toggle('active', isActive);
      if (isActive) activeLink = link;
    });

    if (activeLink && navContainer && navContainer.scrollWidth > navContainer.clientWidth) {
      activeLink.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    }
  }

  navLinks.forEach(function(link) {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      var hash = this.getAttribute('href');
      var targetId = hash.slice(1);
      var section = document.getElementById(targetId);
      if (section) {
        var top = section.getBoundingClientRect().top + window.scrollY - 100;
        window.scrollTo({ top: top, behavior: 'smooth' });
      }
      activateByHash(hash);
    });
  });

  var sections = [];
  navLinks.forEach(function(link) {
    var id = link.getAttribute('href').slice(1);
    var section = document.getElementById(id);
    if (section) {
      sections.push({ id: id, section: section });
    }
  });

  if (sections.length === 0) return;

  function syncActiveSection() {
    var scrollPoint = window.scrollY + 140;
    var currentHash = '#' + sections[0].id;

    sections.forEach(function(item) {
      if (item.section.offsetTop <= scrollPoint) {
        currentHash = '#' + item.id;
      }
    });

    activateByHash(currentHash);
  }

  window.addEventListener('scroll', syncActiveSection, { passive: true });
  window.addEventListener('resize', syncActiveSection);
  syncActiveSection();
}

function addCustomPreferenceFromInput() {
  var input = document.querySelector('.profile-custom-pref-input');
  if (!input) return;

  var value = input.value.trim();
  if (!value) return;

  var current = getCustomPreferenceKeywords();
  var isDuplicate = current.some(function(item) {
    return item.toLowerCase() === value.toLowerCase();
  });

  if (!isDuplicate) {
    current.push(value);
    renderCustomPreferenceChips(current);
  }

  input.value = '';
}

function renderCustomPreferenceChips(keywords) {
  var container = document.getElementById('custom-pref-list');
  if (!container) return;

  var list = Array.isArray(keywords) ? keywords : [];
  container.innerHTML = list.map(function(keyword) {
    return (
      '<button type="button" class="pref-chip custom-pref-chip is-active" data-custom-pref="' +
      escapeHtml(keyword) + '">' +
      '<i class="bx bx-tag"></i>' +
      '<span>' + escapeHtml(keyword) + '</span>' +
      '<i class="bx bx-x"></i>' +
      '</button>'
    );
  }).join('');

  container.querySelectorAll('[data-custom-pref]').forEach(function(chip) {
    chip.addEventListener('click', function() {
      this.remove();
    });
  });
}

function getCustomPreferenceKeywords() {
  var list = [];
  document.querySelectorAll('[data-custom-pref]').forEach(function(chip) {
    var value = chip.getAttribute('data-custom-pref');
    if (value) list.push(value);
  });
  return list;
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function syncPreferenceChips(preferences) {
  var selected = Array.isArray(preferences) ? preferences : [];
  document.querySelectorAll('[data-pref-tag]').forEach(function(chip) {
    var tag = chip.getAttribute('data-pref-tag');
    chip.classList.toggle('is-active', selected.indexOf(tag) !== -1);
  });
}

function getSelectedPreferenceTags() {
  var selected = [];
  document.querySelectorAll('[data-pref-tag].is-active').forEach(function(chip) {
    var tag = chip.getAttribute('data-pref-tag');
    if (tag) selected.push(tag);
  });
  return selected;
}

function getInitials(text) {
  if (!text) return 'ST';
  var trimmed = String(text).trim();
  if (!trimmed) return 'ST';

  var words = trimmed.split(/\s+/).filter(Boolean);
  if (words.length >= 2) {
    return (words[0][0] + words[words.length - 1][0]).toUpperCase();
  }

  return trimmed.slice(0, 2).toUpperCase();
}

function setTextBySelector(selector, value) {
  var el = document.querySelector(selector);
  if (el) el.textContent = value;
}

function setInputValueBySelector(selector, value) {
  var el = document.querySelector(selector);
  if (el) el.value = value;
}

function setSelectValueBySelector(selector, value) {
  var el = document.querySelector(selector);
  if (el) el.value = value || '';
}

function setCheckedBySelector(selector, value) {
  var el = document.querySelector(selector);
  if (el) el.checked = !!value;
}

function initPaymentOptions() {
  var paymentOptions = document.querySelectorAll('.payment-option');
  if (paymentOptions.length === 0) return;

  paymentOptions.forEach(function(option) {
    option.addEventListener('click', function() {
      paymentOptions.forEach(function(opt) { opt.classList.remove('selected'); });
      this.classList.add('selected');

      var radio = this.querySelector('input[type="radio"]');
      if (radio) radio.checked = true;
    });
  });
}

function initModals() {
  document.querySelectorAll('[data-modal-target]').forEach(function(trigger) {
    trigger.addEventListener('click', function() {
      var modalId = this.getAttribute('data-modal-target');
      openModal(modalId);
    });
  });

  document.querySelectorAll('[data-modal-close]').forEach(function(closer) {
    closer.addEventListener('click', function() {
      var modal = this.closest('.modal-overlay');
      if (modal) closeModal(modal.id);
    });
  });

  document.querySelectorAll('.modal-overlay').forEach(function(overlay) {
    overlay.addEventListener('click', function(e) {
      if (e.target === overlay) closeModal(overlay.id);
    });
  });
}

function openModal(id) {
  var modal = document.getElementById(id);
  if (modal) modal.classList.add('is-active');
}

function closeModal(id) {
  var modal = document.getElementById(id);
  if (modal) modal.classList.remove('is-active');
}

function showToast(message, type) {
  type = type || 'success';
  var container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  var icons = {
    success: 'bx-check-circle',
    error: 'bx-error-circle',
    warning: 'bx-error'
  };

  var toast = document.createElement('div');
  toast.className = 'toast toast-' + type;
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
    removeToast(toast);
  });

  setTimeout(function() { removeToast(toast); }, 4000);
}

function removeToast(toast) {
  if (!toast || !toast.parentNode) return;
  toast.classList.add('toast-out');
  setTimeout(function() {
    if (toast.parentNode) toast.parentNode.removeChild(toast);
  }, 300);
}

function initUploadAreas() {
  document.querySelectorAll('.upload-area').forEach(function(area) {
    var fileInput = area.querySelector('input[type="file"]');
    if (!fileInput) return;

    area.addEventListener('click', function() {
      fileInput.click();
    });

    fileInput.addEventListener('click', function(e) {
      e.stopPropagation();
    });

    fileInput.addEventListener('change', function() {
      if (this.files && this.files[0]) {
        var file = this.files[0];

        area.classList.add('has-file');

        var existingPreview = area.querySelector('.upload-preview');
        if (existingPreview) existingPreview.remove();

        var icon = area.querySelector('i');
        var text = area.querySelector('p');

        if (file.type.startsWith('image/')) {
          var reader = new FileReader();
          reader.onload = function(e) {
            var img = document.createElement('img');
            img.src = e.target.result;
            img.className = 'upload-preview';
            area.appendChild(img);
          };
          reader.readAsDataURL(file);
        }

        if (icon) icon.className = 'bx bx-check-circle';
        if (text) text.textContent = file.name;
      }
    });
  });
}

async function initPromoClaim() {
  var saved = await getStoredSavedVouchers();

  document.querySelectorAll('.btn-claim-promo').forEach(function(btn) {
    var currentCode = btn.getAttribute('data-code');
    var isSaved = saved.some(function(item) { return item.code === currentCode; });

    if (isSaved) {
      btn.textContent = 'Đã lưu';
      btn.classList.remove('btn-primary');
      btn.classList.add('btn-outline', 'disabled');
      btn.disabled = true;
    }

    btn.addEventListener('click', async function() {
      var isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
      var code = this.getAttribute('data-code');

      if (!isLoggedIn) {
        showToast('Vui lòng đăng nhập để lưu mã khuyến mãi', 'warning');
        setTimeout(function() { window.location.href = 'auth.html'; }, 1500);
        return;
      }

      var success = await saveVoucher(code);

      if (success) {
        this.textContent = 'Đã lưu';
        this.classList.remove('btn-primary');
        this.classList.add('btn-outline', 'disabled');
        this.disabled = true;
        showToast('Đã lưu mã ' + code + ' vào ví của bạn', 'success');
      } else {
        showToast('Không thể lưu mã ' + code, 'error');
      }
    });
  });
}

function initCheckoutPayment() {
  var btn = document.getElementById('checkoutPayBtn');
  var modal = document.getElementById('paymentSuccessModal');
  var qrModal = document.getElementById('paymentQrModal');
  var qrConfirmBtn = document.getElementById('paymentQrConfirmBtn');
  if (!btn || !modal) return;

  if (qrConfirmBtn) {
    qrConfirmBtn.addEventListener('click', function() {
      closeModal('paymentQrModal');
      openModal('paymentSuccessModal');
      showToast('Thanh toan QR mo phong thanh cong', 'success');
    });
  }

  btn.addEventListener('click', async function() {
    var isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
    if (!isLoggedIn) {
      showToast('Vui lòng đăng nhập để đặt tour', 'warning');
      setTimeout(function() { window.location.href = 'auth.html'; }, 1200);
      return;
    }

    btn.classList.add('is-loading');
    btn.disabled = true;

    try {
      var bookingPayload = buildBookingPayload();
      if (!bookingPayload) {
        btn.classList.remove('is-loading');
        btn.disabled = false;
        return;
      }

      var res = await fetchApi('/api/bookings', {
        method: 'POST',
        body: JSON.stringify(bookingPayload)
      });

      var data = await res.json();
      if (!res.ok) {
        showToast(data.detail || 'Không thể tạo booking', 'error');
        return;
      }

      await submitSelectedGuideRequest();

      var orderCode = data.id ? String(data.id).slice(-6).toUpperCase() : generateOrderCode();
      var totalText = formatCurrency(data.total_amount || 0);
      var orderEl = document.getElementById('paymentOrderCode');
      var totalModal = document.getElementById('paymentTotal');
      var qrOrderEl = document.getElementById('paymentQrOrder');
      var qrTotalEl = document.getElementById('paymentQrTotal');

      if (orderEl) orderEl.textContent = orderCode;
      if (totalModal) totalModal.textContent = totalText;
      if (qrOrderEl) qrOrderEl.textContent = orderCode;
      if (qrTotalEl) qrTotalEl.textContent = totalText;

      var selectedOption = document.querySelector('.payment-option.selected');
      var method = selectedOption ? selectedOption.getAttribute('data-method') : '';

      if (method === 'qr' && qrModal) {
        openModal('paymentQrModal');
        showToast('Vui lòng quét mã QR để thanh toán', 'success');
        return;
      }

      openModal('paymentSuccessModal');
      showToast('Đặt tour thành công, đang chờ xác nhận', 'success');
    } catch (e) {
      showToast('Lỗi kết nối máy chủ', 'error');
    } finally {
      btn.classList.remove('is-loading');
      btn.disabled = false;
    }
  });
}

function generateOrderCode() {
  var random = Math.floor(100000 + Math.random() * 900000);
  return 'ST-' + random;
}

function initAdminSidebar() {
  var menuBtn = document.querySelector('.admin-menu-btn');
  var sidebar = document.getElementById('adminSidebar');
  if (!menuBtn || !sidebar) return;

  menuBtn.addEventListener('click', function() {
    sidebar.classList.toggle('active');
  });

  document.addEventListener('click', function(e) {
    if (window.innerWidth <= 768 && !sidebar.contains(e.target) && !menuBtn.contains(e.target)) {
      sidebar.classList.remove('active');
    }
  });
}

function initProfileSave() {
  var saveBtn = document.querySelector('.btn-save-profile');
  if (!saveBtn) return;

  saveBtn.addEventListener('click', async function() {
    var nameInput = document.querySelector('.profile-input-name');
    var phoneInput = document.querySelector('.profile-input-phone');
    var birthInput = document.querySelector('.profile-input-birth');
    var genderInput = document.querySelector('.profile-input-gender');
    var addressInput = document.querySelector('.profile-input-address');
    
    var settingEmail = document.querySelector('.profile-setting-email');
    var settingSms = document.querySelector('.profile-setting-sms');
    var settingAi = document.querySelector('.profile-setting-ai');
    var settingLanguage = document.querySelector('.profile-setting-language');

    var btn = this;
    btn.classList.add('is-loading');
    btn.disabled = true;

    try {
        await fetchApi('/api/users/me', {
            method: 'PUT',
            body: JSON.stringify({
                full_name: nameInput ? nameInput.value.trim() : null,
                phone: phoneInput ? phoneInput.value.trim() : null,
                birth_date: birthInput ? birthInput.value : null,
                gender: genderInput ? genderInput.value : null,
                address: addressInput ? addressInput.value.trim() : null
            })
        });

        await fetchApi('/api/users/me/preferences', {
            method: 'PUT',
            body: JSON.stringify({
                preferences: getSelectedPreferenceTags(),
                custom_preferences: getCustomPreferenceKeywords()
            })
        });

        await fetchApi('/api/users/me/settings', {
            method: 'PUT',
            body: JSON.stringify({
                settings: {
                    email_notifications: settingEmail ? !!settingEmail.checked : true,
                    sms_notifications: settingSms ? !!settingSms.checked : false,
                    ai_personalization: settingAi ? !!settingAi.checked : true,
                    language: settingLanguage ? settingLanguage.value : 'vi'
                }
            })
        });

        showToast('Đã lưu thay đổi thành công', 'success');
        setTimeout(() => location.reload(), 1000);
    } catch(e) {
        showToast('Lỗi khi lưu hồ sơ', 'error');
    } finally {
        btn.classList.remove('is-loading');
        btn.disabled = false;
    }
  });
}

function initGuideRegisterForm() {
  var form = document.getElementById('guide-register-form');
  if (!form) return;

  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    var submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.classList.add('is-loading');
    submitBtn.disabled = true;

    var data = {
        name: document.querySelector('input[name="guide_name"]') ? document.querySelector('input[name="guide_name"]').value : '',
        experience_years: parseInt(document.querySelector('input[name="guide_experience"]').value, 10) || 0,
        price_per_day: parseFloat(document.querySelector('input[name="guide_price"]').value) || 0,
        areas: (document.querySelector('input[name="guide_areas"]').value || '').split(',').map(function(item) { return item.trim(); }).filter(Boolean),
        languages: (document.querySelector('input[name="guide_languages"]').value || '').split(',').map(function(item) { return item.trim(); }).filter(Boolean),
        bio: document.querySelector('textarea[name="guide_bio"]').value || '',
        id_front_url: document.querySelector('input[name="guide_id_front"]').value || '',
        id_back_url: document.querySelector('input[name="guide_id_back"]').value || ''
    };

    try {
        var res = await fetchApi('/api/guides/apply', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        if (res.ok) {
            showToast('Đã gửi yêu cầu phê duyệt thành công!', 'success');
            setTimeout(function() { window.location.href = 'guides.html'; }, 2000);
        } else {
            var err = await res.json();
            showToast(err.detail || 'Lỗi khi gửi yêu cầu', 'error');
        }
    } catch(err) {
        showToast('Lỗi kết nối máy chủ', 'error');
    } finally {
        submitBtn.classList.remove('is-loading');
        submitBtn.disabled = false;
    }
  });
}

function initGuideHireActions() {
  var buttons = document.querySelectorAll('.btn-hire-guide');
  if (buttons.length === 0) return;

  var hireForm = document.getElementById('hireGuideForm');
  if (hireForm) {
    hireForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      await submitGuideHire();
    });
  }

  buttons.forEach(function(btn) {
    btn.addEventListener('click', async function() {
      var isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
      if (!isLoggedIn) {
        showToast('Vui lòng đăng nhập để thuê hướng dẫn viên', 'warning');
        setTimeout(function() { window.location.href = 'auth.html'; }, 1200);
        return;
      }

      var guideId = btn.getAttribute('data-guide-id');
      if (!guideId || guideId.indexOf('guide-demo') === 0) {
        showToast('Demo: Hãy chọn hướng dẫn viên thật từ dữ liệu hệ thống', 'info');
        return;
      }
      openHireGuideModal(guideId);
    });
  });
}

function openHireGuideModal(guideId) {
  var modal = document.getElementById('hireGuideModal');
  var idInput = document.getElementById('hireGuideId');
  if (idInput) idInput.value = guideId || '';
  if (modal) modal.classList.add('is-active');
}

async function submitGuideHire() {
  var guideId = document.getElementById('hireGuideId').value;
  var destination = document.getElementById('hireDestination').value.trim();
  var tripDate = document.getElementById('hireTripDate').value;
  var note = document.getElementById('hireNote').value.trim();

  if (!guideId || !destination || !tripDate) {
    showToast('Vui lòng nhập đầy đủ thông tin', 'error');
    return;
  }

  var btn = document.querySelector('#hireGuideForm button[type="submit"]');
  var originalText = btn ? btn.textContent : '';
  if (btn) {
    btn.textContent = 'Đang gửi...';
    btn.disabled = true;
  }

  try {
    var res = await fetchApi('/api/guides/requests', {
      method: 'POST',
      body: JSON.stringify({
        guide_id: guideId,
        trip_date: tripDate,
        destination: destination,
        note: note
      })
    });

    if (res.ok) {
      showToast('Đã gửi yêu cầu hướng dẫn viên', 'success');
      closeHireModal();
      document.getElementById('hireGuideForm').reset();
    } else {
      var err = await res.json();
      showToast(err.detail || 'Không thể gửi yêu cầu', 'error');
    }
  } catch (e) {
    showToast('Lỗi kết nối máy chủ', 'error');
  } finally {
    if (btn) {
      btn.textContent = originalText;
      btn.disabled = false;
    }
  }
}

function closeHireModal() {
  var modal = document.getElementById('hireGuideModal');
  if (modal) modal.classList.remove('is-active');
}

async function initGuideDashboard() {
  var isGuideDashboard = window.location.pathname.endsWith('guide-dashboard.html');
  if (!isGuideDashboard) return;

  var isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
  if (!isLoggedIn) {
    window.location.href = 'auth.html';
    return;
  }

  try {
    var meRes = await fetchApi('/api/users/me');
    if (!meRes.ok) {
      window.location.href = 'auth.html';
      return;
    }

    var profile = await meRes.json();
    if (!profile || profile.role !== 'guide') {
      showToast('Tai khoan chua duoc duyet huong dan vien', 'warning');
      setTimeout(function() { window.location.href = 'guides.html'; }, 1200);
      return;
    }
  } catch (e) {
    window.location.href = 'auth.html';
    return;
  }

  try {
    var dashboardRes = await fetchApi('/api/guides/me/dashboard');
    if (dashboardRes.ok) {
      var data = await dashboardRes.json();
      setTextBySelector('#guideTripsMonth', String(data.stats && data.stats.trips_month || 0));
      setTextBySelector('#guideEarningsMonth', formatCurrency(data.stats && data.stats.earnings_month || 0));
      renderGuideHistory(data.history || []);
    }
  } catch (e) {}

  try {
    var reqRes = await fetchApi('/api/guides/me/requests');
    if (reqRes.ok) {
      var requests = await reqRes.json();
      renderGuideRequests(requests || []);
    }
  } catch (e) {}
}

function renderGuideHistory(list) {
  var container = document.getElementById('guideHistoryList');
  var badge = document.getElementById('guideHistoryBadge');
  if (!container) return;

  if (!Array.isArray(list) || list.length === 0) {
    container.innerHTML = '<div class="text-muted text-sm">Chua co chuyẹn nao.</div>';
    if (badge) badge.textContent = '0 chuyến';
    return;
  }

  if (badge) badge.textContent = list.length + ' chuyến';
  container.innerHTML = list.map(function(item) {
    return (
      '<div class="guide-history-card">' +
      '<h4>' + escapeHtml(item.tour_title || 'Tour') + '</h4>' +
      '<div class="guide-meta">' +
      '<span><i class="bx bx-map"></i> ' + escapeHtml(item.destination || '--') + '</span>' +
      '<span><i class="bx bx-calendar"></i> ' + escapeHtml(item.trip_date || '--') + '</span>' +
      '</div>' +
      '<div class="guide-earn">Thu nhap: ' + formatCurrency(item.earning || 0) + '</div>' +
      '</div>'
    );
  }).join('');
}

function renderGuideRequests(list) {
  var container = document.getElementById('guideRequestsList');
  var badge = document.getElementById('guideRequestsBadge');
  var countEl = document.getElementById('guideRequestsCount');
  if (!container) return;

  if (!Array.isArray(list) || list.length === 0) {
    container.innerHTML = '<div class="text-muted text-sm">Chua co yeu cau moi.</div>';
    if (badge) {
      badge.textContent = '0 yêu cầu';
      badge.className = 'badge badge-success';
    }
    if (countEl) countEl.textContent = '0';
    return;
  }

  if (badge) {
    badge.textContent = list.length + ' yêu cầu';
    badge.className = 'badge badge-warning';
  }
  if (countEl) countEl.textContent = String(list.length);

  container.innerHTML = list.map(function(item) {
    return (
      '<div class="guide-request-card">' +
      '<h4>' + escapeHtml(item.customer_name || 'Khach hang') + '</h4>' +
      '<div class="guide-meta">' +
      '<span><i class="bx bx-map"></i> ' + escapeHtml(item.destination || '--') + '</span>' +
      '<span><i class="bx bx-calendar"></i> ' + escapeHtml(item.trip_date || '--') + '</span>' +
      '</div>' +
      '<div class="guide-meta">' +
      '<span><i class="bx bx-phone"></i> ' + escapeHtml(item.customer_phone || '--') + '</span>' +
      '</div>' +
      '</div>'
    );
  }).join('');
}

function formatCurrency(value) {
  if (value == null) return '--';
  return new Intl.NumberFormat('vi-VN').format(value) + '₫';
}

function initCheckoutData() {
  var isCheckout = window.location.pathname.endsWith('checkout.html');
  if (!isCheckout) return;

  var params = new URLSearchParams(window.location.search);
  var title = params.get('title');
  var price = parseInt(params.get('price'));
  var originalPrice = parseInt(params.get('original'));
  var duration = params.get('duration');
  var img = params.get('img');
  var tourId = params.get('tourId');

  if (!title || !price) {
    var titleEl = document.getElementById('checkoutTourTitle');
    if (titleEl) titleEl.textContent = 'Vui lòng chọn tour từ trang Tour du lịch';
    return;
  }

  var titleEl = document.getElementById('checkoutTourTitle');
  var imgEl = document.getElementById('checkoutTourImg');
  var durationEl = document.getElementById('checkoutTourDuration');
  var adultLabel = document.getElementById('checkoutAdultLabel');
  var adultPrice = document.getElementById('checkoutAdultPrice');
  var childrenLabel = document.getElementById('checkoutChildrenLabel');
  var childrenPrice = document.getElementById('checkoutChildrenPrice');
  var insurancePrice = document.getElementById('checkoutInsurancePrice');
  var totalEl = document.getElementById('checkoutTotal');
  var adultsSelect = document.getElementById('checkoutAdults');
  var childrenSelect = document.getElementById('checkoutChildren');
  var insuranceCheckbox = document.getElementById('checkoutInsurance');
  var voucherInput = document.getElementById('checkoutVoucher');
  var voucherApply = document.getElementById('checkoutVoucherApply');
  var voucherValue = document.getElementById('checkoutVoucherValue');
  var travelDateInput = document.getElementById('checkoutTravelDate');
  var dateLabel = document.getElementById('checkoutTourDate');

  if (titleEl) titleEl.textContent = title;
  if (imgEl && img) imgEl.src = img;
  if (durationEl && duration) durationEl.innerHTML = '<i class="bx bx-time"></i> ' + duration;

  var currentVoucher = null;

  function updateCheckoutTotals() {
    var fmt = new Intl.NumberFormat('vi-VN');
    var adults = getPassengerCount(adultsSelect, 2);
    var children = getPassengerCount(childrenSelect, 0);
    var insurance = insuranceCheckbox && insuranceCheckbox.checked ? 150000 : 0;
    var adultTotal = price * adults;
    var childTotal = Math.round(price * 0.5) * children;
    var insuranceTotal = insurance * (adults + children);
    var subtotal = adultTotal + childTotal + insuranceTotal;
    var discount = calculateVoucherDiscount(currentVoucher, subtotal, insuranceTotal);
    var total = Math.max(0, subtotal - discount);

    if (adultLabel) adultLabel.textContent = 'Người lớn x' + adults;
    if (adultPrice) adultPrice.textContent = fmt.format(adultTotal) + '₫';
    if (childrenLabel) childrenLabel.textContent = 'Trẻ em x' + children;
    if (childrenPrice) childrenPrice.textContent = fmt.format(childTotal) + '₫';
    if (insurancePrice) insurancePrice.textContent = fmt.format(insuranceTotal) + '₫';
    if (voucherValue) voucherValue.textContent = discount ? '-' + fmt.format(discount) + '₫' : '--';
    if (totalEl) totalEl.textContent = fmt.format(total) + '₫';
  }

  function syncTravelDateLabel() {
    if (dateLabel && travelDateInput) {
      dateLabel.innerHTML = '<i class="bx bx-calendar"></i> ' + (travelDateInput.value || 'Chọn ngày khởi hành');
    }
  }

  if (adultsSelect) adultsSelect.addEventListener('change', updateCheckoutTotals);
  if (childrenSelect) childrenSelect.addEventListener('change', updateCheckoutTotals);
  if (insuranceCheckbox) insuranceCheckbox.addEventListener('change', updateCheckoutTotals);
  if (travelDateInput) travelDateInput.addEventListener('change', syncTravelDateLabel);

  if (voucherApply && voucherInput) {
    voucherApply.addEventListener('click', async function() {
      var code = voucherInput.value.trim().toUpperCase();
      if (!code) {
        currentVoucher = null;
        updateCheckoutTotals();
        showToast('Vui lòng nhập mã giảm giá', 'warning');
        return;
      }

      try {
        var res = await fetchApi('/api/vouchers');
        var list = res.ok ? await res.json() : [];
        currentVoucher = Array.isArray(list) ? list.find(function(v) { return v.code === code; }) : null;
        if (!currentVoucher) {
          showToast('Mã giảm giá không hợp lệ', 'error');
        } else {
          showToast('Áp dụng mã thành công', 'success');
        }
        updateCheckoutTotals();
      } catch (e) {
        showToast('Không thể kiểm tra mã giảm giá', 'error');
      }
    });
  }

  syncTravelDateLabel();
  updateCheckoutTotals();
  initCheckoutGuides();

  if (!tourId) {
    resolveTourIdFromTitle(title);
  } else {
    localStorage.setItem('checkout_tour_id', tourId);
  }
}

function getPassengerCount(selectEl, fallback) {
  if (!selectEl) return fallback;
  var value = selectEl.value || '';
  var match = value.match(/\d+/);
  if (!match) return fallback;
  return parseInt(match[0], 10) || fallback;
}

function calculateVoucherDiscount(voucher, subtotal, insuranceTotal) {
  if (!voucher) return 0;
  if (voucher.discount_type === 'percent') {
    var discount = subtotal * (voucher.discount_value / 100);
    if (voucher.max_discount && discount > voucher.max_discount) {
      discount = voucher.max_discount;
    }
    return Math.round(discount);
  }
  if (voucher.discount_type === 'fixed') {
    return Math.round(voucher.discount_value || 0);
  }
  if (voucher.discount_type === 'free_insurance') {
    return Math.round(Math.min(voucher.discount_value || 0, insuranceTotal));
  }
  return 0;
}

async function initCheckoutGuides() {
  var select = document.getElementById('checkoutGuideSelect');
  if (!select) return;

  try {
    var res = await fetchApi('/api/guides');
    if (!res.ok) return;
    var guides = await res.json();
    if (!Array.isArray(guides) || guides.length === 0) return;

    guides.forEach(function(guide) {
      var option = document.createElement('option');
      option.value = guide.id;
      option.textContent = guide.name + ' - ' + formatCurrency(guide.price_per_day) + '/ngay';
      select.appendChild(option);
    });
  } catch (e) {}
}

async function resolveTourIdFromTitle(title) {
  if (!title) return;
  try {
    var res = await fetchApi('/api/tours');
    if (!res.ok) return;
    var tours = await res.json();
    if (!Array.isArray(tours)) return;
    var matched = tours.find(function(tour) {
      return tour.title === title;
    });
    if (matched && matched.id) {
      localStorage.setItem('checkout_tour_id', matched.id);
    }
  } catch (e) {}
}

function buildBookingPayload() {
  var tourId = localStorage.getItem('checkout_tour_id');
  if (!tourId) {
    showToast('Thiếu mã tour, vui lòng chọn tour lại', 'error');
    return null;
  }

  var travelDate = document.getElementById('checkoutTravelDate') ? document.getElementById('checkoutTravelDate').value : '';
  var adults = getPassengerCount(document.getElementById('checkoutAdults'), 2);
  var children = getPassengerCount(document.getElementById('checkoutChildren'), 0);
  var insurance = document.getElementById('checkoutInsurance') ? document.getElementById('checkoutInsurance').checked : false;
  var phone = document.getElementById('checkoutContactPhone') ? document.getElementById('checkoutContactPhone').value.trim() : '';
  var note = document.getElementById('checkoutNote') ? document.getElementById('checkoutNote').value.trim() : '';
  var voucherCode = document.getElementById('checkoutVoucher') ? document.getElementById('checkoutVoucher').value.trim().toUpperCase() : '';

  var selectedOption = document.querySelector('.payment-option.selected');
  var paymentMethod = selectedOption ? selectedOption.getAttribute('data-method') : 'credit_card';
  if (paymentMethod === 'qr') {
    paymentMethod = 'bank_transfer';
  }

  if (!travelDate) {
    showToast('Vui lòng chọn ngày khởi hành', 'warning');
    return null;
  }
  if (!phone) {
    showToast('Vui lòng nhập số điện thoại liên hệ', 'warning');
    return null;
  }

  return {
    tour_id: tourId,
    travel_date: travelDate,
    adults: adults,
    children: children,
    insurance: insurance,
    coupon_code: voucherCode || null,
    payment_method: paymentMethod,
    contact_phone: phone,
    note: note || null
  };
}

async function initGuidesDirectory() {
  var grid = document.getElementById('guidesGrid');
  if (!grid) return;

  try {
    var res = await fetchApi('/api/guides');
    if (!res.ok) {
      grid.innerHTML = '<div class="card p-6 text-center text-muted">Không thể tải danh sách hướng dẫn viên.</div>';
      return;
    }

    var guides = await res.json();
    if (!Array.isArray(guides) || guides.length === 0) {
      grid.innerHTML = '<div class="card p-6 text-center text-muted">Chưa có hướng dẫn viên khả dụng.</div>';
      return;
    }

    grid.innerHTML = guides.map(function(guide) {
      var langs = Array.isArray(guide.languages) ? guide.languages : [];
      var areas = Array.isArray(guide.areas) ? guide.areas.join(', ') : '';
      return (
        '<div class="guide-card">' +
        '<img src="https://images.unsplash.com/photo-1531427186611-ecfd6d936c79?auto=format&fit=crop&q=80&w=200" alt="' + escapeHtml(guide.name) + '" class="guide-avatar">' +
        '<div class="guide-info">' +
        '<div class="guide-header">' +
        '<span class="badge badge-primary"><i class="bx bx-check-shield"></i> Đã xác minh</span>' +
        '<span class="status-available">Sẵn sàng</span>' +
        '</div>' +
        '<h3 class="font-bold text-lg mt-2">' + escapeHtml(guide.name) + '</h3>' +
        '<p class="text-muted text-sm"><i class="bx bx-map"></i> ' + escapeHtml(areas || 'Địa điểm linh hoạt') + '</p>' +
        '<div class="guide-stats">' +
        '<span><i class="bx bx-briefcase"></i> ' + escapeHtml(String(guide.experience_years || 0)) + ' năm kinh nghiệm</span>' +
        '</div>' +
        '<div class="mb-4">' + langs.map(function(lang) { return '<span class="lang-tag">' + escapeHtml(lang) + '</span>'; }).join('') + '</div>' +
        '<div class="guide-price mb-4">' + formatCurrency(guide.price_per_day || 0) + ' <span class="guide-price-unit">/ ngày</span></div>' +
        '<button class="btn btn-primary w-full btn-hire-guide" data-guide-id="' + escapeHtml(guide.id) + '">Thuê ngay</button>' +
        '</div>' +
        '</div>'
      );
    }).join('');

    initGuideHireActions();
  } catch (e) {
    grid.innerHTML = '<div class="card p-6 text-center text-muted">Không thể tải danh sách hướng dẫn viên.</div>';
  }
}

async function submitSelectedGuideRequest() {
  var select = document.getElementById('checkoutGuideSelect');
  if (!select || !select.value) return;
  var guideNote = document.getElementById('checkoutGuideNote') ? document.getElementById('checkoutGuideNote').value.trim() : '';
  var travelDate = document.getElementById('checkoutTravelDate') ? document.getElementById('checkoutTravelDate').value : '';
  var destination = document.getElementById('checkoutTourTitle') ? document.getElementById('checkoutTourTitle').textContent.trim() : '';
  var phone = document.getElementById('checkoutContactPhone') ? document.getElementById('checkoutContactPhone').value.trim() : '';

  if (!travelDate || !destination) return;

  try {
    await fetchApi('/api/guides/requests', {
      method: 'POST',
      body: JSON.stringify({
        guide_id: select.value,
        trip_date: travelDate,
        destination: destination,
        note: guideNote || null,
        customer_phone: phone || null
      })
    });
  } catch (e) {}
}

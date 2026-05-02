document.addEventListener('DOMContentLoaded', function() {
  initNavigation();
  initMobileMenu();
  initAuthState();
  initProfileData();
  initPreferenceChips();
  initCustomPreferenceActions();
  initTripItemModalAccess();
  initProfileNavSpy();
  initLogoutAction();
  initPaymentOptions();
  initModals();
  initUploadAreas();
  initPromoClaim();
  initAdminSidebar();
  initProfileSave();
  initGuideRegisterForm();
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

function initAuthState() {
  var isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
  var profile = getStoredUserProfile();
  var initials = getInitials(profile.fullName || profile.email || 'ST');
  var containers = document.querySelectorAll('.nav-actions');

  containers.forEach(function(container) {
    if (container.closest('.admin-page')) return;

    if (isLoggedIn) {
      container.innerHTML = '<a href="profile.html" class="user-avatar" title="Trang cá nhân">' + initials + '</a>';
    }
  });
}

function initProfileData() {
  var isProfilePage = window.location.pathname.endsWith('profile.html');
  if (!isProfilePage) return;

  var isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
  if (!isLoggedIn) {
    window.location.href = 'auth.html';
    return;
  }

  var profile = getStoredUserProfile();
  var fullName = profile.fullName;
  var email = profile.email;
  var initials = getInitials(fullName || email);

  setTextBySelector('.profile-display-name', fullName);
  setTextBySelector('.profile-display-email', email);
  setInputValueBySelector('.profile-input-name', fullName);
  setInputValueBySelector('.profile-input-email', email);
  setInputValueBySelector('.profile-input-phone', profile.phone);
  setInputValueBySelector('.profile-input-birth', profile.birthDate);
  setInputValueBySelector('.profile-input-address', profile.address);
  setSelectValueBySelector('.profile-input-gender', profile.gender);
  setSelectValueBySelector('.profile-setting-language', profile.settings.language);
  setCheckedBySelector('.profile-setting-email', profile.settings.emailNotifications);
  setCheckedBySelector('.profile-setting-sms', profile.settings.smsNotifications);
  setCheckedBySelector('.profile-setting-ai', profile.settings.aiPersonalization);

  document.querySelectorAll('.profile-initials').forEach(function(el) {
    el.textContent = initials;
  });

  syncPreferenceChips(profile.preferences);
  renderCustomPreferenceChips(profile.customPreferences || []);
  renderSavedVouchers();
}

function initLogoutAction() {
  document.querySelectorAll('[data-logout]').forEach(function(link) {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      localStorage.removeItem('isLoggedIn');
      localStorage.removeItem('userProfile');
      showToast('Ban da dang xuat thanh cong', 'success');
      setTimeout(function() { window.location.href = 'auth.html'; }, 800);
    });
  });
}

function getStoredUserProfile() {
  var defaultProfile = {
    fullName: 'Khach Hang',
    email: 'khachhang@example.com',
    phone: '',
    birthDate: '',
    gender: '',
    address: '',
    preferences: [],
    customPreferences: [],
    savedVouchers: [],
    settings: {
      emailNotifications: true,
      smsNotifications: false,
      aiPersonalization: true,
      language: 'vi'
    }
  };

  try {
    var raw = localStorage.getItem('userProfile');
    if (!raw) return defaultProfile;
    var parsed = JSON.parse(raw) || {};

    return {
      fullName: parsed.fullName || defaultProfile.fullName,
      email: parsed.email || defaultProfile.email,
      phone: parsed.phone || defaultProfile.phone,
      birthDate: parsed.birthDate || defaultProfile.birthDate,
      gender: parsed.gender || defaultProfile.gender,
      address: parsed.address || defaultProfile.address,
      preferences: Array.isArray(parsed.preferences) ? parsed.preferences : defaultProfile.preferences,
      customPreferences: Array.isArray(parsed.customPreferences) ? parsed.customPreferences : defaultProfile.customPreferences,
      savedVouchers: Array.isArray(parsed.savedVouchers) ? parsed.savedVouchers : defaultProfile.savedVouchers,
      settings: {
        emailNotifications: parsed.settings && typeof parsed.settings.emailNotifications === 'boolean'
          ? parsed.settings.emailNotifications
          : defaultProfile.settings.emailNotifications,
        smsNotifications: parsed.settings && typeof parsed.settings.smsNotifications === 'boolean'
          ? parsed.settings.smsNotifications
          : defaultProfile.settings.smsNotifications,
        aiPersonalization: parsed.settings && typeof parsed.settings.aiPersonalization === 'boolean'
          ? parsed.settings.aiPersonalization
          : defaultProfile.settings.aiPersonalization,
        language: parsed.settings && parsed.settings.language
          ? parsed.settings.language
          : defaultProfile.settings.language
      }
    };
  } catch (e) {
    return defaultProfile;
  }
}

function getStoredSavedVouchers() {
  var profile = getStoredUserProfile();
  var merged = [];

  function pushUnique(voucher) {
    var normalized = normalizeVoucher(voucher);
    if (!normalized) return;
    var exists = merged.some(function(item) { return item.code === normalized.code; });
    if (!exists) merged.push(normalized);
  }

  try {
    var raw = localStorage.getItem('savedVouchers');
    if (raw) {
      var parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) parsed.forEach(pushUnique);
    }
  } catch (e) {
    merged = [];
  }

  if (Array.isArray(profile.savedVouchers)) {
    profile.savedVouchers.forEach(pushUnique);
  }

  return merged;
}

function saveVoucher(voucher) {
  var normalized = normalizeVoucher(voucher);
  if (!normalized) return false;

  var saved = getStoredSavedVouchers();
  var exists = saved.some(function(item) { return item.code === normalized.code; });
  if (exists) return false;

  saved.push(normalized);
  localStorage.setItem('savedVouchers', JSON.stringify(saved));

  var profile = getStoredUserProfile();
  profile.savedVouchers = saved;
  localStorage.setItem('userProfile', JSON.stringify(profile));

  return true;
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

function renderSavedVouchers() {
  var container = document.getElementById('saved-vouchers-list');
  if (!container) return;

  var saved = getStoredSavedVouchers();
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
      '<span class="text-sm text-warning"><i class="bx bx-time"></i> ' + (voucher.expiry || 'Con hieu luc') + '</span>' +
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
  toast.innerHTML =
    '<i class="bx ' + (icons[type] || icons.success) + ' toast-icon"></i>' +
    '<span>' + message + '</span>' +
    '<button class="toast-close">&times;</button>';

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

function initPromoClaim() {
  var saved = getStoredSavedVouchers();

  document.querySelectorAll('.btn-claim-promo').forEach(function(btn) {
    var currentCode = btn.getAttribute('data-code');
    var isSaved = saved.some(function(item) { return item.code === currentCode; });

    if (isSaved) {
      btn.textContent = 'Đã lưu';
      btn.classList.remove('btn-primary');
      btn.classList.add('btn-outline', 'disabled');
      btn.disabled = true;
    }

    btn.addEventListener('click', function() {
      var isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
      var code = this.getAttribute('data-code');

      if (!isLoggedIn) {
        showToast('Vui lòng đăng nhập để lưu mã khuyến mãi', 'warning');
        setTimeout(function() { window.location.href = 'auth.html'; }, 1500);
        return;
      }

      var promoCard = this.closest('.promo-card');
      var titleEl = promoCard ? promoCard.querySelector('h3') : null;
      var expiryEl = promoCard ? promoCard.querySelector('.promo-expiry') : null;
      var descEl = promoCard ? promoCard.querySelector('.text-muted') : null;

      var voucher = {
        code: code,
        title: titleEl ? titleEl.textContent.trim() : 'Voucher uu dai',
        description: descEl ? descEl.textContent.trim() : '',
        expiry: expiryEl ? expiryEl.textContent.trim() : ''
      };

      saveVoucher(voucher);

      this.textContent = 'Đã lưu';
      this.classList.remove('btn-primary');
      this.classList.add('btn-outline', 'disabled');
      this.disabled = true;
      showToast('Đã lưu mã ' + code + ' vào ví của bạn', 'success');
    });
  });
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

  document.querySelectorAll('[data-admin-approve]').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var row = this.closest('tr');
      var badge = row.querySelector('.badge');
      if (badge) {
        badge.className = 'badge badge-success';
        badge.textContent = 'Đã duyệt';
      }
      this.textContent = 'Đã duyệt';
      this.disabled = true;
      this.classList.add('disabled');
      showToast('Đã duyệt thành công', 'success');
    });
  });

  document.querySelectorAll('[data-admin-reject]').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var row = this.closest('tr');
      var badge = row.querySelector('.badge');
      if (badge) {
        badge.className = 'badge badge-danger';
        badge.textContent = 'Từ chối';
      }
      showToast('Đã từ chối yêu cầu', 'error');
    });
  });
}

function initProfileSave() {
  var saveBtn = document.querySelector('.btn-save-profile');
  if (!saveBtn) return;

  saveBtn.addEventListener('click', function() {
    var nameInput = document.querySelector('.profile-input-name');
    var emailInput = document.querySelector('.profile-input-email');
    var phoneInput = document.querySelector('.profile-input-phone');
    var birthInput = document.querySelector('.profile-input-birth');
    var genderInput = document.querySelector('.profile-input-gender');
    var addressInput = document.querySelector('.profile-input-address');
    var settingEmail = document.querySelector('.profile-setting-email');
    var settingSms = document.querySelector('.profile-setting-sms');
    var settingAi = document.querySelector('.profile-setting-ai');
    var settingLanguage = document.querySelector('.profile-setting-language');
    var updatedName = nameInput ? nameInput.value.trim() : '';
    var updatedEmail = emailInput ? emailInput.value.trim() : '';

    var profile = getStoredUserProfile();
    profile.fullName = updatedName || profile.fullName || 'Khach Hang';
    profile.email = updatedEmail || profile.email || 'khachhang@example.com';
    profile.phone = phoneInput ? phoneInput.value.trim() : profile.phone;
    profile.birthDate = birthInput ? birthInput.value : profile.birthDate;
    profile.gender = genderInput ? genderInput.value : profile.gender;
    profile.address = addressInput ? addressInput.value.trim() : profile.address;
    profile.preferences = getSelectedPreferenceTags();
    profile.customPreferences = getCustomPreferenceKeywords();
    profile.savedVouchers = getStoredSavedVouchers();
    profile.settings = {
      emailNotifications: settingEmail ? !!settingEmail.checked : true,
      smsNotifications: settingSms ? !!settingSms.checked : false,
      aiPersonalization: settingAi ? !!settingAi.checked : true,
      language: settingLanguage ? settingLanguage.value : 'vi'
    };

    localStorage.setItem('userProfile', JSON.stringify(profile));

    setTextBySelector('.profile-display-name', profile.fullName);
    setTextBySelector('.profile-display-email', profile.email);

    var initials = getInitials(profile.fullName || profile.email);
    document.querySelectorAll('.profile-initials').forEach(function(el) {
      el.textContent = initials;
    });

    var btn = this;
    btn.classList.add('is-loading');
    btn.disabled = true;

    setTimeout(function() {
      btn.classList.remove('is-loading');
      btn.disabled = false;
      showToast('Đã lưu thay đổi thành công', 'success');
    }, 1200);
  });
}

function initGuideRegisterForm() {
  var form = document.getElementById('guide-register-form');
  if (!form) return;

  form.addEventListener('submit', function(e) {
    e.preventDefault();
    var submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.classList.add('is-loading');
    submitBtn.disabled = true;

    setTimeout(function() {
      submitBtn.classList.remove('is-loading');
      submitBtn.disabled = false;
      showToast('Đã gửi yêu cầu phê duyệt thành công! Admin sẽ kiểm tra hồ sơ của bạn.', 'success');
      setTimeout(function() { window.location.href = 'guides.html'; }, 2000);
    }, 1500);
  });
}

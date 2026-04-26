document.addEventListener('DOMContentLoaded', function() {
  initNavigation();
  initMobileMenu();
  initAuthState();
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
  var containers = document.querySelectorAll('.nav-actions');

  containers.forEach(function(container) {
    if (container.closest('.admin-page')) return;

    if (isLoggedIn) {
      container.innerHTML = '<a href="profile.html" class="user-avatar" title="Trang cá nhân">ST</a>';
    }
  });
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
  document.querySelectorAll('.btn-claim-promo').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
      var code = this.getAttribute('data-code');

      if (!isLoggedIn) {
        showToast('Vui lòng đăng nhập để lưu mã khuyến mãi', 'warning');
        setTimeout(function() { window.location.href = 'auth.html'; }, 1500);
        return;
      }

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

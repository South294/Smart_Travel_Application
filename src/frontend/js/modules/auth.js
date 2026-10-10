var SmartTravelAuth = (function() {
  async function getStoredUserProfile() {
    var raw = localStorage.getItem('userProfile');
    if (raw) {
      try {
        var cached = JSON.parse(raw);
        if (cached && typeof cached === 'object') return cached;
      } catch (e) {}
    }

    if (!localStorage.getItem('access_token')) return null;

    try {
      var res = await fetchApi('/api/users/me');
      if (res.ok) {
        var profile = await res.json();
        localStorage.setItem('userProfile', JSON.stringify(profile));
        return profile;
      }
    } catch (e) {}
    return null;
  }

  async function initAuthState() {
    var isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
    var containers = document.querySelectorAll('.nav-actions');
    var hireGuideLink = document.querySelector('a.nav-link[href="guides.html"]');
    var registerHdvLink = document.querySelector('a.nav-link[href="guide-register.html"]');
    var guideHdvLink = document.querySelector('a.nav-link[href="guide-dashboard.html"]');

    if (hireGuideLink) {
      hireGuideLink.textContent = 'Thuê HDV';
      hireGuideLink.style.display = '';
    }
    if (guideHdvLink) guideHdvLink.style.display = 'none';

    if (!isLoggedIn) return;

    var profile = await getStoredUserProfile();
    var userRole = (profile && profile.role) || localStorage.getItem('userRole') || 'user';

    if (userRole === 'guide' && guideHdvLink) {
      guideHdvLink.style.display = '';
      if (registerHdvLink) registerHdvLink.style.display = 'none';
    }

    containers.forEach(function(container) {
      var displayName = (profile && profile.full_name) || 'Tài khoản';
      var avatar = (profile && profile.avatar_url) ? profile.avatar_url : 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=100&q=80';
      var initials = displayName.split(' ').map(function(w) { return w[0]; }).join('').slice(-2).toUpperCase();
      var isAdmin = userRole === 'admin';

      container.innerHTML =
        '<div class="user-menu">' +
          '<button class="user-btn" aria-haspopup="true" aria-expanded="false">' +
            '<span class="user-avatar" style="background-image: url(\'' + avatar + '\'); background-size: cover; background-position: center;">' +
              (avatar ? '' : initials) +
            '</span>' +
            '<span class="user-name">' + displayName + '</span>' +
            '<i class="bx bx-chevron-down"></i>' +
          '</button>' +
          '<div class="dropdown-menu" role="menu">' +
            (isAdmin ? '<a href="admin/index.html" class="dropdown-item" role="menuitem"><i class="bx bxs-dashboard"></i> Trang quản trị</a>' : '') +
            '<a href="profile.html" class="dropdown-item" role="menuitem"><i class="bx bx-user"></i> Hồ sơ của tôi</a>' +
            '<a href="promotions.html" class="dropdown-item" role="menuitem"><i class="bx bx-gift"></i> Ví voucher</a>' +
            (userRole === 'guide' ? '<a href="guide-dashboard.html" class="dropdown-item" role="menuitem"><i class="bx bx-briefcase"></i> Dashboard HDV</a>' : '') +
            '<div class="dropdown-divider"></div>' +
            '<a href="#" class="dropdown-item btn-logout" role="menuitem"><i class="bx bx-log-out"></i> Đăng xuất</a>' +
          '</div>' +
        '</div>';

      var userBtn = container.querySelector('.user-btn');
      var dropdown = container.querySelector('.dropdown-menu');

      if (userBtn && dropdown) {
        userBtn.addEventListener('click', function(e) {
          e.stopPropagation();
          dropdown.classList.toggle('is-active');
          userBtn.setAttribute('aria-expanded', dropdown.classList.contains('is-active'));
        });
      }
    });

    document.addEventListener('click', function() {
      document.querySelectorAll('.dropdown-menu.is-active').forEach(function(menu) {
        menu.classList.remove('is-active');
        var btn = menu.closest('.user-menu') && menu.closest('.user-menu').querySelector('.user-btn');
        if (btn) btn.setAttribute('aria-expanded', 'false');
      });
    });

    initLogoutAction();
  }

  function initLogoutAction() {
    document.querySelectorAll('.btn-logout').forEach(function(btn) {
      btn.addEventListener('click', function(e) {
        e.preventDefault();
        localStorage.removeItem('access_token');
        localStorage.removeItem('isLoggedIn');
        localStorage.removeItem('userRole');
        localStorage.removeItem('userProfile');
        localStorage.removeItem('savedVouchers');
        showToast('Đã đăng xuất thành công', 'success');
        setTimeout(function() {
          window.location.href = 'index.html';
        }, 600);
      });
    });
  }

  return {
    getStoredUserProfile: getStoredUserProfile,
    initAuthState: initAuthState,
    initLogoutAction: initLogoutAction
  };
})();

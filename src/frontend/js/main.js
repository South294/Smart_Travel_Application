function getDeviceFingerprint() {
    var stored = sessionStorage.getItem('smart_travel_device_fingerprint');
    if (stored) return stored;
    var canvasData = '';
    try {
        var canvas = document.createElement('canvas');
        var ctx = canvas.getContext('2d');
        if (ctx) {
            ctx.textBaseline = 'top';
            ctx.font = '14px Arial';
            ctx.fillStyle = '#2563eb';
            ctx.fillRect(100, 1, 50, 20);
            ctx.fillStyle = '#06b6d4';
            ctx.fillText('SmartTravel2026', 2, 12);
            canvasData = canvas.toDataURL();
        }
    } catch (e) {
        canvasData = 'canvas_na';
    }
    var rawStr = [
        navigator.userAgent || '',
        navigator.language || '',
        screen.colorDepth || '',
        (screen.width || '') + 'x' + (screen.height || ''),
        new Date().getTimezoneOffset(),
        navigator.hardwareConcurrency || '',
        canvasData.slice(-80)
    ].join('||');
    var hash = 0;
    for (var i = 0; i < rawStr.length; i++) {
        var charCode = rawStr.charCodeAt(i);
        hash = ((hash << 5) - hash) + charCode;
        hash = hash & hash;
    }
    var fp = 'dev_' + Math.abs(hash).toString(16) + '_' + (navigator.hardwareConcurrency || 4);
    sessionStorage.setItem('smart_travel_device_fingerprint', fp);
    return fp;
}

async function fetchApi(url, options = {}) {
    const token = localStorage.getItem('access_token');
    const deviceFp = getDeviceFingerprint();
    const headers = { 'Content-Type': 'application/json', ...options.headers };
    if (token) headers['Authorization'] = 'Bearer ' + token;
    if (deviceFp) headers['X-Device-Fingerprint'] = deviceFp;
    const apiBase = window.SMART_TRAVEL_API_URL || 'http://localhost:8000';
    const res = await fetch(apiBase + url, { ...options, headers });
    if (res.status === 401) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('isLoggedIn');
        localStorage.removeItem('userRole');
    }
    return res;
}

document.addEventListener('DOMContentLoaded', async function() {
  document.addEventListener('click', function(e) {
    var link = e.target.closest('a[href*="checkout.html"]');
    if (link) {
      var href = link.getAttribute('href') || '';
      if (href.indexOf('mode=combo') === -1) {
        localStorage.removeItem('checkout_mode');
        localStorage.removeItem('checkout_combo_items');
      }
    }
  });

  initNavigation();
  initMobileMenu();
  await initAuthState();
  await initProfileData();
  initPreferenceChips();
  initCustomPreferenceActions();
  initTripItemModalAccess();
  initBookingContractActions();
  initProfileNavSpy();
  initLogoutAction();
  initPaymentOptions();
  initModals();
  initUploadAreas();
  await initPromoClaim();
  initAdminSidebar();
  initProfileSave();
  initChangePasswordAction();
  await initCCCDVerification();
  initGuideRegisterForm();
  initGuideHireActions();
  await initGuidesDirectory();
  await initGuideProfilePage();
  await initGuideDashboard();
  await initCheckoutData();
  initCheckoutPayment();
  await initTrendingTours();
  await initPersonalizedRecommendations();
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
  if (!profile.email) return;

  var initials = getInitials(profile.full_name || profile.email || 'ST');
  var showGuideDashboard = false;
  var isGuideApproved = false;
  var hasGuideApplication = false;

  if (isLoggedIn) {
    try {
      var guideRes = await fetchApi('/api/guides/me');
      if (guideRes.ok) {
        var guideProfile = await guideRes.json();
        hasGuideApplication = true;
        isGuideApproved = guideProfile && guideProfile.status === 'approved';
        showGuideDashboard = isGuideApproved;
      }
    } catch (e) {}
  }

  if (registerHdvLink) {
    registerHdvLink.style.display = hasGuideApplication ? 'none' : '';
  }
  if (guideHdvLink) {
    guideHdvLink.style.display = isGuideApproved ? '' : 'none';
  }

  var dashboardBtn = document.querySelector('a.btn-ghost[href="guide-dashboard.html"]');
  if (dashboardBtn) {
    if (!isGuideApproved) {
      dashboardBtn.style.display = 'none';
    } else {
      dashboardBtn.style.display = '';
    }
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
    var vipTripCountText = document.getElementById('vipTripCountText');
    var vipProgressBar = document.getElementById('vipProgressBar');
    var vipStatusBadge = document.getElementById('vipStatusBadge');
    var btnUpgradeVip = document.getElementById('btnUpgradeVip');
    var tripCount = Array.isArray(bookings) ? bookings.length : 0;

    if (vipTripCountText) {
      vipTripCountText.textContent = tripCount + '/10 chuyến';
    }
    if (vipProgressBar) {
      var pct = Math.min(100, Math.round((tripCount / 10) * 100));
      vipProgressBar.style.width = pct + '%';
    }
    if (vipStatusBadge && tripCount >= 10 && localStorage.getItem('isVipUser') === 'true') {
      vipStatusBadge.innerHTML = '<i class="bx bxs-crown"></i> Hội Viên VIP';
      vipStatusBadge.style.background = '#dcfce7';
      vipStatusBadge.style.color = '#15803d';
      vipStatusBadge.style.borderColor = '#86efac';
    }

    if (btnUpgradeVip) {
      btnUpgradeVip.onclick = function() {
        if (tripCount < 10) {
          showToast('Bạn cần hoàn thành tối thiểu 10 chuyến đi để đủ điều kiện nâng hạng VIP (hiện tại: ' + tripCount + '/10 chuyến).', 'warning');
          return;
        }
        localStorage.setItem('isVipUser', 'true');
        showToast('Chúc mừng bạn đã nâng cấp thành công Hội viên VIP SmartTravel!', 'success');
        if (vipStatusBadge) {
          vipStatusBadge.innerHTML = '<i class="bx bxs-crown"></i> Hội Viên VIP';
          vipStatusBadge.style.background = '#dcfce7';
          vipStatusBadge.style.color = '#15803d';
          vipStatusBadge.style.borderColor = '#86efac';
        }
      };
    }

    if (!Array.isArray(bookings) || bookings.length === 0) {
      listWrap.innerHTML = '<div class="empty-state p-6 text-center text-muted"><i class="bx bx-compass" style="font-size: 2.4rem; color: var(--primary-color);"></i><p class="mt-2 mb-0">Bạn chưa có chuyến đi nào được đặt. Hãy khám phá ngay các tour hấp dẫn!</p></div>';
      return;
    }

    listWrap.innerHTML = bookings.map(function(booking) {
      var statusText = mapBookingStatus(booking.status);
      var statusClass = mapBookingStatusClass(booking.status);
      var bookingCode = booking.booking_code || ('ST-' + String(booking.id || '').slice(-8).toUpperCase());
      var thumb = getBookingThumbnail(booking);
      var cleanTitle = (booking.tour_title || 'Tour du lịch khám phá').replace(/\s*-\s*Tour\s*\d+N\d+Đ/i, '');

      return (
        '<div class="my-trip-card" data-booking-id="' + escapeHtml(booking.id) + '">' +
          '<div class="my-trip-media">' +
            '<img src="' + escapeHtml(thumb) + '" alt="' + escapeHtml(booking.tour_title || 'Tour') + '" class="my-trip-img" onerror="this.onerror=null;this.src=\'https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=600&q=80\';">' +
            '<span class="my-trip-code-tag">' + escapeHtml(bookingCode) + '</span>' +
          '</div>' +
          '<div class="my-trip-content">' +
            '<div class="my-trip-top-row">' +
              '<h4 class="my-trip-heading">' + escapeHtml(cleanTitle) + '</h4>' +
              '<span class="badge ' + statusClass + '">' + statusText + '</span>' +
            '</div>' +
            '<div class="my-trip-info-grid">' +
              '<div class="my-trip-info-cell"><i class="bx bx-map-pin text-primary"></i> <span>' + escapeHtml(booking.tour_location || 'Việt Nam') + '</span></div>' +
              '<div class="my-trip-info-cell"><i class="bx bx-calendar text-primary"></i> <span>Ngày đi: <strong>' + escapeHtml(booking.travel_date || '--') + '</strong></span></div>' +
              '<div class="my-trip-info-cell"><i class="bx bx-user-voice text-primary"></i> <span>HDV: <strong>' + escapeHtml(booking.guide_name || 'Vũ Văn Sơn (HDV SmartTravel)') + '</strong></span></div>' +
              '<div class="my-trip-info-cell"><i class="bx bx-wallet text-primary"></i> <span>Tổng tiền: <strong class="text-primary">' + formatCurrency(booking.total_amount || 0) + '</strong></span></div>' +
            '</div>' +
            '<div class="my-trip-bottom-row">' +
              '<span class="text-xs text-muted"><i class="bx bx-shield-quarter text-success"></i> Gói tour có HDV & Bảo hiểm</span>' +
              '<button type="button" class="btn btn-outline btn-sm btn-trip-detail"><i class="bx bx-calendar-star"></i> Xem chi tiết lịch trình</button>' +
            '</div>' +
          '</div>' +
        '</div>'
      );
    }).join('');

    listWrap.querySelectorAll('[data-booking-id]').forEach(function(item) {
      item.addEventListener('click', function() {
        var booking = bookings.find(function(entry) { return entry.id === item.getAttribute('data-booking-id'); });
        if (booking) openBookingDetail(booking);
      });
    });
  } catch (e) {
    listWrap.innerHTML = '<div class="text-muted text-sm">Không thể tải danh sách chuyến đi.</div>';
  }
}

function getBookingThumbnail(booking) {
  if (booking && booking.tour_image) return booking.tour_image;
  var text = ((booking && booking.tour_location) || '') + ' ' + ((booking && booking.tour_title) || '');
  var textLower = text.toLowerCase();
  if (textLower.indexOf('phú quốc') !== -1) return 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=600&q=80';
  if (textLower.indexOf('sapa') !== -1 || textLower.indexOf('sa pa') !== -1 || textLower.indexOf('fansipan') !== -1) return 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=600&q=80';
  if (textLower.indexOf('hà giang') !== -1) return 'https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=600&q=80';
  if (textLower.indexOf('hạ long') !== -1) return 'https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?auto=format&fit=crop&w=600&q=80';
  if (textLower.indexOf('mộc châu') !== -1) return 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=600&q=80';
  if (textLower.indexOf('tam đảo') !== -1) return 'https://images.unsplash.com/photo-1589308078059-be1415eab4c3?auto=format&fit=crop&w=600&q=80';
  if (textLower.indexOf('cát bà') !== -1) return 'https://images.unsplash.com/photo-1605538032432-a9f0c8d9baac?auto=format&fit=crop&w=600&q=80';
  if (textLower.indexOf('nha trang') !== -1 || textLower.indexOf('vĩnh hy') !== -1) return 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=600&q=80';
  if (textLower.indexOf('hồ hoàn kiếm') !== -1 || textLower.indexOf('hà nội') !== -1) return 'https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=600&q=80';
  return 'https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=600&q=80';
}

function cleanItineraryText(text) {
  if (!text) return '';
  return String(text)
    .replace(/Vinpearl Safari & Grand World Không Ngủ \d+N\d+Đ/g, 'Vinpearl Safari & Grand World')
    .replace(/Phú Quốc Nghỉ Dưỡng Thượng Lưu\s*-\s*/g, '')
    .replace(/Trekking Sapa\s*-\s*Chinh phục Fansipan \d+N\d+Đ/g, 'Sa Pa & Fansipan Legend')
    .replace(/Hà Giang Loop\s*-\s*Cung đèo Hạnh Phúc \d+N\d+Đ/g, 'Đèo Mã Pí Lèng & Cao nguyên đá Hà Giang')
    .replace(/Du thuyền Vịnh Hạ Long 5 Sao/g, 'Vịnh Hạ Long')
    .replace(/Hồ Hoàn Kiếm\s*-\s*/g, 'Hà Nội');
}

function formatBookingDate(value) {
  if (!value) return '--';
  var date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('vi-VN');
}

function openBookingDetail(booking) {
  var modal = document.getElementById('bookingDetailModal');
  if (!modal) return;
  var setText = function(id, value) {
    var element = document.getElementById(id);
    if (element) element.textContent = value || '--';
  };
  setText('bookingDetailTitle', booking.tour_title || 'Tour du lịch');
  setText('bookingDetailCode', booking.booking_code || ('ST-' + String(booking.id || '').slice(-8).toUpperCase()));
  setText('bookingDetailTravelDate', booking.travel_date);
  setText('bookingDetailPaidAt', booking.paid_at ? formatBookingDate(booking.paid_at) : 'Chưa thanh toán');
  setText('bookingDetailLocation', booking.tour_location || 'Đang cập nhật');
  setText('bookingDetailStatus', mapBookingStatus(booking.status));
  setText('bookingDetailTotal', formatCurrency(booking.total_amount || 0));

  var tripTypeTag = document.getElementById('bookingDetailTripTypeTag');
  if (tripTypeTag) {
    tripTypeTag.textContent = booking.trip_type === 'inter_provincial'
      ? 'Chuyến đi trọn gói liên tuyến (Cả đi và đến kèm xe đưa đón du lịch)'
      : 'Chuyến đi khám phá tại điểm đến (Khám phá toàn diện địa phương)';
  }

  setText('bookingDetailGuideName', booking.guide_name || 'Vũ Văn Sơn (HDV SmartTravel)');
  setText('bookingDetailGuideExp', booking.guide_experience || '5 năm kinh nghiệm dẫn đoàn');
  setText('bookingDetailGuidePhone', booking.guide_phone || '0912 345 678');
  setText('bookingDetailTransportation', booking.transportation || 'Xe ô tô du lịch chất lượng cao đời mới phục vụ suốt tuyến, đón trả tận nơi.');

  var timelineContainer = document.getElementById('bookingDetailTimeline');
  if (timelineContainer) {
    var itinerary = booking.itinerary_details;
    if (Array.isArray(itinerary) && itinerary.length > 0) {
      timelineContainer.innerHTML = itinerary.map(function(dayPlan) {
        var items = dayPlan.timeline || [];
        var cleanDayTitle = cleanItineraryText(dayPlan.title || 'Lịch trình chi tiết');
        var dayTitle = '<div class="booking-day-header"><i class="bx bx-calendar-star"></i> ' + escapeHtml(cleanDayTitle) + '</div>';
        var itemsHtml = items.map(function(item) {
          var typeIcon = item.type === 'dining' ? 'bx-restaurant' : (item.type === 'departure' || item.type === 'return' ? 'bx-car' : 'bx-map-pin');
          var badgeClass = item.type === 'dining' ? 'badge-dining' : (item.type === 'departure' ? 'badge-departure' : (item.type === 'return' ? 'badge-return' : 'badge-sightseeing'));
          var activityClean = cleanItineraryText(item.activity || '');
          var locationClean = cleanItineraryText(item.location || '');
          var delicacyHtml = '';
          if (item.delicacy) {
            delicacyHtml = '<div style="margin-top:5px;"><span class="badge" style="background:#fff3cd; color:#997404; border:1px solid #ffeeba; font-weight:600; font-size:0.78rem; padding:3px 8px; border-radius:4px;"><i class="bx bx-dish"></i> Đặc sản ẩm thực: ' + escapeHtml(item.delicacy) + '</span></div>';
          }
          return (
            '<div class="timeline-step-card">' +
              '<div class="timeline-step-badge ' + badgeClass + '">' +
                '<i class="bx ' + typeIcon + '"></i> ' + escapeHtml(item.time || '--') +
              '</div>' +
              '<div class="timeline-step-body">' +
                '<p class="timeline-step-text">' + escapeHtml(activityClean) + '</p>' +
                delicacyHtml +
                (locationClean ? '<span class="timeline-step-loc" style="display:inline-block; margin-top:4px;"><i class="bx bx-current-location"></i> ' + escapeHtml(locationClean) + '</span>' : '') +
              '</div>' +
            '</div>'
          );
        }).join('');
        return '<div class="booking-day-block">' + dayTitle + '<div class="timeline-step-list">' + itemsHtml + '</div></div>';
      }).join('');
    } else {
      timelineContainer.innerHTML = '<div class="text-muted text-sm p-4 bg-light rounded text-center">Lịch trình chi tiết đang được hướng dẫn viên cập nhật theo thời gian thực của chuyến đi.</div>';
    }
  }

  var mapLink = document.getElementById('bookingDetailMapLink');
  if (mapLink) {
    if (booking.route_map_url) {
      mapLink.href = booking.route_map_url;
    } else {
      var query = booking.tour_lat && booking.tour_lng ? booking.tour_lat + ',' + booking.tour_lng : booking.tour_location || booking.tour_title;
      mapLink.href = 'https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(query);
    }
  }

  modal._currentBooking = booking;
  openModal('bookingDetailModal');
}

async function openBookingContractModal(booking) {
  if (!booking) return;
  var body = document.getElementById('tourContractModalBody');
  if (body) {
    body.innerHTML = '<div class="text-center p-6 text-muted"><i class="bx bx-loader-alt bx-spin" style="font-size: 28px;"></i> Đang tải dữ liệu hợp đồng điện tử...</div>';
  }
  openModal('tourContractModal');

  try {
    var bookingId = booking.id || booking._id;
    var res = await fetchApi('/api/bookings/' + encodeURIComponent(bookingId) + '/contract');
    if (res.ok) {
      var data = await res.json();
      if (body && data.contract_html) {
        body.innerHTML = data.contract_html;
        return;
      }
    }
  } catch (e) {}

  if (body) {
    body.innerHTML = '<div class="card p-6" style="background:#fff; border-radius:8px;">' +
      '<div style="text-align:center; border-bottom:2px solid #0284c7; padding-bottom:12px; margin-bottom:16px;">' +
      '<h2 style="color:#0369a1; margin:0 0 4px 0;">HỢP ĐỒNG DU LỊCH & LỮ HÀNH ĐIỆN TỬ</h2>' +
      '<p style="margin:0; font-size:13px; color:#64748b;">Mã HĐ: ' + escapeHtml(booking.contract_code || ('HDDL-ST-' + String(booking.id || '').slice(-6).toUpperCase())) + '</p>' +
      '</div>' +
      '<p><strong>Tên chuyến đi:</strong> ' + escapeHtml(booking.tour_title || 'Tour du lịch') + '</p>' +
      '<p><strong>Ngày khởi hành:</strong> ' + escapeHtml(booking.travel_date || '--') + '</p>' +
      '<p><strong>Khách hàng đại diện:</strong> ' + escapeHtml(booking.contact_name || 'Quý khách') + '</p>' +
      '<p><strong>Email nhận thông tin:</strong> ' + escapeHtml(booking.contact_email || '--') + '</p>' +
      '<p><strong>Tổng tiền:</strong> ' + formatCurrency(booking.total_amount || 0) + '</p>' +
      '<p><strong>Hướng dẫn viên:</strong> ' + escapeHtml(booking.guide_name || 'Vũ Văn Sơn (HDV SmartTravel)') + ' - Hotline: ' + escapeHtml(booking.guide_phone || '0912 345 678') + '</p>' +
      '<p style="color:#15803d; font-weight:600;"><i class="bx bx-check-circle"></i> Trạng thái: Hợp đồng đã có hiệu lực pháp lý và bảo hiểm toàn diện.</p>' +
      '</div>';
  }
}

async function sendBookingContractEmail(bookingId) {
  if (!bookingId) {
    showToast('Không xác định được mã booking', 'error');
    return;
  }
  try {
    showToast('Đang gửi hợp đồng và lịch trình về Gmail...', 'info');
    var res = await fetchApi('/api/bookings/' + encodeURIComponent(bookingId) + '/send-contract-email', {
      method: 'POST'
    });
    if (res.ok) {
      showToast('Hợp đồng & Lịch trình chi tiết đã được gửi về Gmail của bạn!', 'success');
    } else {
      var err = await res.json().catch(function() { return {}; });
      showToast(err.detail || 'Không thể gửi email lúc này. Hợp đồng vẫn được lưu trong hồ sơ.', 'warning');
    }
  } catch (e) {
    showToast('Lỗi kết nối khi gửi email', 'error');
  }
}

function initBookingContractActions() {
  var viewBtn = document.getElementById('btnViewBookingContract');
  var resendBtn = document.getElementById('btnResendBookingContract');
  var modalSendBtn = document.getElementById('btnModalContractSendEmail');
  var printBtn = document.getElementById('btnPrintContract');
  var detailModal = document.getElementById('bookingDetailModal');

  if (viewBtn) {
    viewBtn.addEventListener('click', function() {
      var booking = detailModal ? detailModal._currentBooking : null;
      if (booking) {
        openBookingContractModal(booking);
      } else {
        showToast('Vui lòng chọn một chuyến đi', 'warning');
      }
    });
  }

  if (resendBtn) {
    resendBtn.addEventListener('click', function() {
      var booking = detailModal ? detailModal._currentBooking : null;
      if (booking) {
        sendBookingContractEmail(booking.id || booking._id);
      }
    });
  }

  if (modalSendBtn) {
    modalSendBtn.addEventListener('click', function() {
      var booking = detailModal ? detailModal._currentBooking : null;
      if (booking) {
        sendBookingContractEmail(booking.id || booking._id);
      }
    });
  }

  if (printBtn) {
    printBtn.addEventListener('click', function() {
      var body = document.getElementById('tourContractModalBody');
      if (!body) return;
      var printWindow = window.open('', '_blank');
      if (printWindow) {
        printWindow.document.write('<html><head><title>Hợp Đồng Du Lịch SmartTravel</title><style>body{font-family:sans-serif;padding:20px;}</style></head><body>' + body.innerHTML + '</body></html>');
        printWindow.document.close();
        printWindow.focus();
        printWindow.print();
      } else {
        window.print();
      }
    });
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

function initUploadAreas() {
  var areas = document.querySelectorAll('.upload-area');
  if (!areas || areas.length === 0) return;

  areas.forEach(function(area) {
    var fileInput = area.querySelector('input[type="file"]');
    var hiddenInput = area.querySelector('input[type="hidden"]');
    var previewBox = area.querySelector('.upload-preview-box');
    var previewImg = area.querySelector('.upload-preview');
    var titleEl = area.querySelector('p');
    var iconEl = area.querySelector('i');

    if (!fileInput) return;

    area.addEventListener('click', function(e) {
      if (e.target !== fileInput) {
        fileInput.click();
      }
    });

    ['dragenter', 'dragover'].forEach(function(eventName) {
      area.addEventListener(eventName, function(e) {
        e.preventDefault();
        e.stopPropagation();
        area.style.borderColor = 'var(--primary-color)';
        area.style.background = 'rgba(10, 169, 130, 0.08)';
      });
    });

    ['dragleave', 'drop'].forEach(function(eventName) {
      area.addEventListener(eventName, function(e) {
        e.preventDefault();
        e.stopPropagation();
        if (!area.classList.contains('has-file')) {
          area.style.borderColor = '';
          area.style.background = '';
        }
      });
    });

    area.addEventListener('drop', function(e) {
      var dt = e.dataTransfer;
      if (dt && dt.files && dt.files.length > 0) {
        processUploadedImage(dt.files[0], area, hiddenInput, previewBox, previewImg, titleEl, iconEl);
      }
    });

    fileInput.addEventListener('change', function() {
      if (!fileInput.files || fileInput.files.length === 0) return;
      processUploadedImage(fileInput.files[0], area, hiddenInput, previewBox, previewImg, titleEl, iconEl);
    });
  });
}

function processUploadedImage(file, area, hiddenInput, previewBox, previewImg, titleEl, iconEl) {
  if (!file.type.match(/^image\//)) {
    showToast('Vui lòng chọn tệp hình ảnh hợp lệ (JPG, PNG, WebP)', 'error');
    return;
  }
  if (file.size > 8 * 1024 * 1024) {
    showToast('Kích thước ảnh không được vượt quá 8MB', 'error');
    return;
  }

  var reader = new FileReader();
  reader.onload = function(evt) {
    var base64Data = evt.target.result;
    if (hiddenInput) hiddenInput.value = base64Data;
    if (previewImg) previewImg.src = base64Data;
    if (previewBox) previewBox.style.display = 'block';
    area.classList.add('has-file');
    area.style.borderColor = 'var(--success)';
    area.style.background = 'rgba(16, 185, 129, 0.04)';
    if (titleEl) titleEl.textContent = file.name;
    if (iconEl) iconEl.className = 'bx bx-check-circle text-success';
  };
  reader.readAsDataURL(file);
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

  var paymentStatus = new URLSearchParams(window.location.search).get('payment');
  if (paymentStatus === 'success') {
    var returnedBookingId = new URLSearchParams(window.location.search).get('booking_id');
    if (returnedBookingId) {
      fetchApi('/api/bookings/' + encodeURIComponent(returnedBookingId)).then(function(response) {
        return response.ok ? response.json() : null;
      }).then(function(booking) {
        if (!booking) return;
        var returnedCode = document.getElementById('paymentOrderCode');
        var returnedTotal = document.getElementById('paymentTotal');
        if (returnedCode) returnedCode.textContent = booking.booking_code || ('ST-' + String(booking.id).slice(-8).toUpperCase());
        if (returnedTotal) returnedTotal.textContent = formatCurrency(booking.total_amount || 0);
      }).catch(function() {});
    }
    openModal('paymentSuccessModal');
    showToast('Thanh toán VNPay thành công', 'success');
  } else if (paymentStatus === 'failed') {
    showToast('Thanh toán chưa thành công, booking vẫn đang chờ xử lý', 'warning');
  } else if (paymentStatus === 'invalid') {
    showToast('Không xác thực được kết quả thanh toán', 'error');
  }

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
      var params = new URLSearchParams(window.location.search);
      var tourIdParam = params.get('tourId') || params.get('tour_id');
      var isComboMode = params.get('mode') === 'combo' && !tourIdParam && !params.get('title');
      var res;
      var data;

      if (isComboMode) {
        var comboPayload = buildComboBookingPayload();
        if (!comboPayload) {
          btn.classList.remove('is-loading');
          btn.disabled = false;
          return;
        }
        res = await fetchApi('/api/bookings/combo', {
          method: 'POST',
          body: JSON.stringify(comboPayload)
        });
        data = await res.json();
        if (!res.ok) {
          showToast(data.detail || 'Không thể tạo đơn đặt combo', 'error');
          return;
        }
        localStorage.removeItem('checkout_combo_items');
        localStorage.removeItem('checkout_mode');
      } else {
        localStorage.removeItem('checkout_combo_items');
        localStorage.removeItem('checkout_mode');
        var bookingPayload = buildBookingPayload();
        if (!bookingPayload) {
          btn.classList.remove('is-loading');
          btn.disabled = false;
          return;
        }
        res = await fetchApi('/api/bookings', {
          method: 'POST',
          body: JSON.stringify(bookingPayload)
        });
        data = await res.json();
        if (!res.ok) {
          showToast(data.detail || 'Không thể tạo booking', 'error');
          return;
        }
      }

      await submitSelectedGuideRequest();

      var selectedOption = document.querySelector('.payment-option.selected');
      var method = selectedOption ? selectedOption.getAttribute('data-method') : '';
      var orderCode = data.booking_code || (data.id ? String(data.id).slice(-6).toUpperCase() : generateOrderCode());
      var totalText = formatCurrency(data.total_amount || 0);
      var orderEl = document.getElementById('paymentOrderCode');
      var totalModal = document.getElementById('paymentTotal');
      var qrOrderEl = document.getElementById('paymentQrOrder');
      var qrTotalEl = document.getElementById('paymentQrTotal');

      if (orderEl) orderEl.textContent = orderCode;
      if (totalModal) totalModal.textContent = totalText;
      if (qrOrderEl) qrOrderEl.textContent = orderCode;
      if (qrTotalEl) qrTotalEl.textContent = totalText;

      if (data.is_free) {
        var freeTitle = document.getElementById('paymentSuccessTitle');
        if (freeTitle) freeTitle.textContent = 'Đặt tour miễn phí thành công';
        openModal('paymentSuccessModal');
        showToast('Đặt tour miễn phí thành công, không cần thanh toán', 'success');
        return;
      }

      if (method === 'qr') {
        var qrConfirmRes = await fetchApi('/api/payments/qr/confirm', {
          method: 'POST',
          body: JSON.stringify({ booking_id: data.id })
        });
        var qrConfirmData = await qrConfirmRes.json();
        if (!qrConfirmRes.ok) {
          showToast(qrConfirmData.detail || 'Không thể xác nhận thanh toán QR', 'error');
          return;
        }
        var qrTitle = document.getElementById('paymentSuccessTitle');
        if (qrTitle) qrTitle.textContent = 'Thanh toán QR demo thành công';
        openModal('paymentSuccessModal');
        showToast('Đặt tour và thanh toán QR demo thành công', 'success');
        return;
      }

      var paymentUrlEndpoint = isComboMode ? '/api/payments/vnpay/create-combo' : '/api/payments/vnpay/create';
      var paymentRes = await fetchApi(paymentUrlEndpoint, {
        method: 'POST',
        body: JSON.stringify({ booking_id: data.id })
      });
      var paymentData = await paymentRes.json();
      if (!paymentRes.ok) {
        showToast(paymentData.detail || 'Chưa thể khởi tạo thanh toán VNPay', 'error');
        return;
      }
      if (paymentData.payment_url) {
        window.location.href = paymentData.payment_url;
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

  var uploadAvatarBtn = document.getElementById('btn-upload-avatar');
  var avatarFileInput = document.getElementById('profile-avatar-file');
  var avatarDisplay = document.querySelector('.profile-initials');

  if (uploadAvatarBtn && avatarFileInput) {
    uploadAvatarBtn.addEventListener('click', function() {
      avatarFileInput.click();
    });

    avatarFileInput.addEventListener('change', function() {
      if (!this.files || !this.files[0]) return;
      var file = this.files[0];
      if (!file.type.match(/^image\//)) {
        showToast('Vui lòng chọn file hình ảnh hợp lệ (JPG, PNG, WebP)', 'error');
        return;
      }
      if (file.size > 5 * 1024 * 1024) {
        showToast('Kích thước ảnh không được vượt quá 5MB', 'error');
        return;
      }

      var reader = new FileReader();
      reader.onload = async function(evt) {
        var base64 = evt.target.result;
        if (avatarDisplay) {
          avatarDisplay.style.backgroundImage = 'url(' + base64 + ')';
          avatarDisplay.style.backgroundSize = 'cover';
          avatarDisplay.style.backgroundPosition = 'center';
          avatarDisplay.textContent = '';
        }
        try {
          var res = await fetchApi('/api/users/me', {
            method: 'PUT',
            body: JSON.stringify({ avatar_url: base64 })
          });
          if (res.ok) {
            showToast('Cập nhật ảnh đại diện thành công!', 'success');
            localStorage.removeItem('userProfile');
          } else {
            showToast('Không thể lưu ảnh đại diện', 'error');
          }
        } catch (err) {
          showToast('Lỗi kết nối khi cập nhật ảnh đại diện', 'error');
        }
      };
      reader.readAsDataURL(file);
    });
  }

  initChangePasswordAction();
}

function initChangePasswordAction() {
  var changePasswordBtn = document.getElementById('btn-change-password');
  if (!changePasswordBtn) return;

  changePasswordBtn.addEventListener('click', async function() {
    var oldPass = document.getElementById('profile-old-password') ? document.getElementById('profile-old-password').value : '';
    var newPass = document.getElementById('profile-new-password') ? document.getElementById('profile-new-password').value : '';
    var confirmPass = document.getElementById('profile-confirm-password') ? document.getElementById('profile-confirm-password').value : '';

    if (!oldPass) {
      showToast('Vui lòng nhập mật khẩu hiện tại', 'error');
      return;
    }
    if (!newPass || newPass.length < 6) {
      showToast('Mật khẩu mới phải có ít nhất 6 ký tự', 'error');
      return;
    }
    if (newPass !== confirmPass) {
      showToast('Mật khẩu xác nhận không trùng khớp', 'error');
      return;
    }

    changePasswordBtn.disabled = true;
    changePasswordBtn.classList.add('is-loading');

    try {
      var res = await fetchApi('/api/users/me/change-password', {
        method: 'POST',
        body: JSON.stringify({ old_password: oldPass, new_password: newPass })
      });
      var data = await res.json();
      if (res.ok) {
        showToast(data.message || 'Đổi mật khẩu thành công!', 'success');
        if (document.getElementById('profile-old-password')) document.getElementById('profile-old-password').value = '';
        if (document.getElementById('profile-new-password')) document.getElementById('profile-new-password').value = '';
        if (document.getElementById('profile-confirm-password')) document.getElementById('profile-confirm-password').value = '';
      } else {
        var errorMsg = 'Không thể đổi mật khẩu';
        if (typeof data.detail === 'string') {
          errorMsg = data.detail;
        } else if (Array.isArray(data.detail) && data.detail[0] && data.detail[0].msg) {
          errorMsg = data.detail[0].msg;
        }
        showToast(errorMsg, 'error');
      }
    } catch (err) {
      showToast('Lỗi kết nối khi đổi mật khẩu', 'error');
    } finally {
      changePasswordBtn.disabled = false;
      changePasswordBtn.classList.remove('is-loading');
    }
  });
}

async function initCCCDVerification() {
  var form = document.getElementById('cccd-verify-form');
  var badge = document.getElementById('cccdStatusBadge');
  var verifiedBox = document.getElementById('cccdVerifiedBox');
  var verifiedInfo = document.getElementById('cccdVerifiedInfo');
  if (!form && !badge) return;

  if (localStorage.getItem('access_token')) {
    try {
      var res = await fetchApi('/api/users/me/cccd-status');
      if (res.ok) {
        var data = await res.json();
        if (data.is_verified) {
          if (badge) {
            badge.className = 'badge badge-success';
            badge.textContent = 'Đã xác thực CCCD';
          }
          if (verifiedBox) {
            verifiedBox.hidden = false;
            if (verifiedInfo && data.cccd) {
              verifiedInfo.textContent = 'Họ tên: ' + (data.cccd.full_name || '') + ' | Số thẻ: ' + (data.cccd.number || '');
            }
          }
          if (form) {
            form.hidden = true;
          }
        } else {
          if (badge) {
            badge.className = 'badge badge-warning';
            badge.textContent = 'Chưa xác thực';
          }
          if (verifiedBox) {
            verifiedBox.hidden = true;
          }
          if (form) {
            form.hidden = false;
          }
        }
      }
    } catch(e) {}
  }

  if (form) {
    form.addEventListener('submit', async function(e) {
      e.preventDefault();
      var btn = document.getElementById('btnSubmitCCCD');
      if (btn) {
        btn.classList.add('is-loading');
        btn.disabled = true;
      }

      var fullNameInput = form.querySelector('input[name="cccd_full_name"]');
      var numberInput = form.querySelector('input[name="cccd_number"]');
      var frontInput = form.querySelector('input[name="cccd_front_url"]');
      var backInput = form.querySelector('input[name="cccd_back_url"]');
      var portraitInput = form.querySelector('input[name="cccd_portrait_url"]');

      var payload = {
        full_name: fullNameInput ? fullNameInput.value.trim() : '',
        cccd_number: numberInput ? numberInput.value.trim() : '',
        id_front_url: frontInput ? frontInput.value.trim() : '',
        id_back_url: backInput ? backInput.value.trim() : '',
        portrait_url: portraitInput ? portraitInput.value.trim() : ''
      };

      if (!payload.cccd_number || payload.cccd_number.length !== 12 || !/^\d{12}$/.test(payload.cccd_number)) {
        showToast('Số CCCD phải gồm đúng 12 chữ số', 'error');
        if (btn) {
          btn.classList.remove('is-loading');
          btn.disabled = false;
        }
        return;
      }

      if (!payload.id_front_url || !payload.id_back_url || !payload.portrait_url) {
        showToast('Vui lòng tải lên đầy đủ ảnh mặt trước, mặt sau CCCD và ảnh chân dung thực tế', 'warning');
        if (btn) {
          btn.classList.remove('is-loading');
          btn.disabled = false;
        }
        return;
      }

      try {
        var resp = await fetchApi('/api/users/me/cccd-verify', {
          method: 'POST',
          body: JSON.stringify(payload)
        });
        if (resp.ok) {
          showToast('Xác thực CCCD thành công!', 'success');
          setTimeout(function() { location.reload(); }, 1200);
        } else {
          var errData = await resp.json();
          showToast(errData.detail || 'Lỗi khi xác thực CCCD', 'error');
        }
      } catch(err) {
        showToast('Lỗi kết nối máy chủ', 'error');
      } finally {
        if (btn) {
          btn.classList.remove('is-loading');
          btn.disabled = false;
        }
      }
    });
  }
}

function initGuideRegisterForm() {
  var form = document.getElementById('guide-register-form');
  if (!form) return;

  initGuideApplicationStatus(form);

  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    var submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.classList.add('is-loading');
    submitBtn.disabled = true;

    var cccdNumber = document.querySelector('input[name="guide_cccd_number"]') ? document.querySelector('input[name="guide_cccd_number"]').value.trim() : '';
    if (cccdNumber && (!/^\d{12}$/.test(cccdNumber))) {
        showToast('Số CCCD phải gồm đúng 12 chữ số', 'error');
        submitBtn.classList.remove('is-loading');
        submitBtn.disabled = false;
        return;
    }

    var data = {
        name: document.querySelector('input[name="guide_name"]') ? document.querySelector('input[name="guide_name"]').value : '',
        experience_years: parseInt(document.querySelector('input[name="guide_experience"]').value, 10) || 0,
        price_per_day: parseFloat(document.querySelector('input[name="guide_price"]').value) || 0,
        areas: (document.querySelector('input[name="guide_areas"]').value || '').split(',').map(function(item) { return item.trim(); }).filter(Boolean),
        languages: (document.querySelector('input[name="guide_languages"]').value || '').split(',').map(function(item) { return item.trim(); }).filter(Boolean),
        bio: document.querySelector('textarea[name="guide_bio"]').value || '',
        cccd_number: cccdNumber,
        id_front_url: document.querySelector('input[name="guide_id_front"]') ? document.querySelector('input[name="guide_id_front"]').value.trim() : '',
        id_back_url: document.querySelector('input[name="guide_id_back"]') ? document.querySelector('input[name="guide_id_back"]').value.trim() : '',
        portrait_url: document.querySelector('input[name="guide_portrait"]') ? document.querySelector('input[name="guide_portrait"]').value.trim() : ''
    };

    if (!data.id_front_url || !data.id_back_url || !data.portrait_url) {
        showToast('Vui lòng tải lên đầy đủ ảnh mặt trước, mặt sau CCCD và ảnh chân dung thực tế', 'warning');
        submitBtn.classList.remove('is-loading');
        submitBtn.disabled = false;
        return;
    }

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

async function initGuideApplicationStatus(form) {
  if (!localStorage.getItem('access_token')) return;

  try {
    var response = await fetchApi('/api/guides/me');
    if (!response.ok) return;

    var guide = await response.json();
    var statusBox = document.getElementById('guideApplicationStatus');
    if (!statusBox) return;

    statusBox.hidden = false;
    if (guide.status === 'pending') {
      statusBox.className = 'alert-box alert-warning mb-6';
      statusBox.textContent = 'Hồ sơ của bạn đang chờ admin phê duyệt.';
      form.hidden = true;
    } else if (guide.status === 'approved') {
      statusBox.className = 'alert-box alert-success mb-6';
      statusBox.textContent = 'Hồ sơ đã được duyệt. Bạn có thể vào Cổng HDV.';
      form.hidden = true;
    } else if (guide.status === 'rejected') {
      statusBox.className = 'alert-box alert-danger mb-6';
      statusBox.textContent = 'Hồ sơ chưa được duyệt. Bạn có thể cập nhật thông tin và gửi lại.';
    }
  } catch (error) {}
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

async function initGuideProfilePage() {
  if (!window.location.pathname.endsWith('guide.html')) return;

  if (localStorage.getItem('isLoggedIn') !== 'true' || !localStorage.getItem('access_token')) {
    window.location.replace('auth.html');
    return;
  }

  try {
    var response = await fetchApi('/api/guides/me');
    if (!response.ok) {
      window.location.replace('guides.html');
      return;
    }

    var guide = await response.json();
    if (guide.status !== 'approved') {
      showToast('Hồ sơ hướng dẫn viên chưa được duyệt', 'warning');
      setTimeout(function() { window.location.replace('guides.html'); }, 1000);
      return;
    }

    setTextBySelector('#guideName', guide.name || '--');
    setTextBySelector('#guideExperience', String(guide.experience_years || 0) + ' năm');
    setTextBySelector('#guideAreas', Array.isArray(guide.areas) ? guide.areas.join(', ') : '--');
    setTextBySelector('#guideLanguages', Array.isArray(guide.languages) ? guide.languages.join(', ') : '--');
    setTextBySelector('#guidePrice', formatCurrency(guide.price_per_day || 0));
    var content = document.getElementById('guidePageContent');
    if (content) content.hidden = false;
  } catch (error) {
    window.location.replace('guides.html');
  }
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

  initGuidePortalNavigation();
  var userProfile = {};

  try {
    var userRes = await fetchApi('/api/users/me');
    if (userRes.ok) {
      userProfile = await userRes.json();
      renderGuideProfile(userProfile);
    }
  } catch (e) {}

  try {
    var dashboardRes = await fetchApi('/api/guides/me/dashboard');
    if (dashboardRes.ok) {
      var data = await dashboardRes.json();
      renderGuideProfile({
        ...data.guide,
        full_name: userProfile.full_name || data.guide.name,
        email: userProfile.email || '--'
      });
      renderGuideDashboardData(data);
    }
  } catch (e) {}
}

function initGuidePortalNavigation() {
  document.querySelectorAll('[data-guide-view]').forEach(function(button) {
    button.addEventListener('click', function() {
      var viewId = button.getAttribute('data-guide-view');
      document.querySelectorAll('[data-guide-view]').forEach(function(item) { item.classList.remove('active'); });
      document.querySelectorAll('.guide-view').forEach(function(view) { view.classList.remove('active'); });
      button.classList.add('active');
      var view = document.getElementById(viewId);
      if (view) view.classList.add('active');
      setTextBySelector('#guideViewTitle', button.getAttribute('data-guide-title') || 'Cổng hướng dẫn viên');
      var sidebar = document.getElementById('guideSidebar');
      if (sidebar) sidebar.classList.remove('is-open');
    });
  });

  var menuButton = document.getElementById('guideMenuBtn');
  if (menuButton) {
    menuButton.addEventListener('click', function() {
      var sidebar = document.getElementById('guideSidebar');
      if (sidebar) sidebar.classList.toggle('is-open');
    });
  }

  var logoutButton = document.getElementById('guideLogoutBtn');
  if (logoutButton) {
    logoutButton.addEventListener('click', function() {
      localStorage.removeItem('access_token');
      localStorage.removeItem('isLoggedIn');
      localStorage.removeItem('userRole');
      window.location.href = 'auth.html';
    });
  }
}

function renderGuideDashboardData(data) {
  var stats = data.stats || {};
  var activeTrips = data.active_trips || [];
  var earnings = formatCurrency(stats.earnings_month || 0);
  var activeCount = activeTrips.length;
  var isActive = activeCount > 0;

  setTextBySelector('#guideTripsMonth', String(stats.trips_month || 0));
  setTextBySelector('#guideEarningsMonth', earnings);
  setTextBySelector('#guideWorkEarnings', earnings);
  setTextBySelector('#guideMapEarnings', earnings);
  setTextBySelector('#guideActiveTrips', String(activeCount));
  setTextBySelector('#guideWorkActiveTrips', String(activeCount));
  setTextBySelector('#guideActiveStatus', isActive ? 'Đang trong chuyến' : 'Đang rảnh');
  setTextBySelector('#guideStatusText', isActive ? 'Bạn đang trong chuyến' : 'Bạn đang không trong chuyến');
  setTextBySelector('#guideCurrentTripBadge', activeCount + ' chuyến');

  var statusDot = document.getElementById('guideStatusDot');
  if (statusDot) statusDot.classList.toggle('is-active', isActive);
  var mapEmpty = document.getElementById('guideMapEmpty');
  if (mapEmpty) mapEmpty.style.display = isActive ? 'none' : 'grid';
  var mapBadge = document.getElementById('guideMapBadge');
  if (mapBadge) mapBadge.textContent = isActive ? 'Đang dẫn tour' : 'Sẵn sàng';

  renderGuideActiveTrips(activeTrips);
  renderGuideHistory(data.history || []);
}

function renderGuideProfile(profile) {
  var guide = profile.guide || profile;
  var name = profile.full_name || guide.name || 'Hướng dẫn viên';
  var email = profile.email || '--';
  var initials = getInitials(name);
  ['#guideUserName', '#guideProfileName', '#guideInfoName'].forEach(function(selector) { setTextBySelector(selector, name); });
  ['#guideProfileEmail', '#guideInfoEmail'].forEach(function(selector) { setTextBySelector(selector, email); });
  ['#guideUserAvatar', '#guideProfileAvatar'].forEach(function(selector) { setTextBySelector(selector, initials); });
  setTextBySelector('#guideInfoExperience', (guide.experience_years || 0) + ' năm');
  setTextBySelector('#guideInfoPrice', formatCurrency(guide.price_per_day || 0) + '/ngày');
  setTextBySelector('#guideInfoAreas', (guide.areas || []).join(', ') || '--');
  setTextBySelector('#guideInfoLanguages', (guide.languages || []).join(', ') || '--');
  setTextBySelector('#guideInfoBio', guide.bio || '--');
}

function renderGuideActiveTrips(list) {
  var container = document.getElementById('guideActiveTripList');
  if (!container) return;
  if (!Array.isArray(list) || list.length === 0) {
    container.innerHTML = '<p class="text-muted text-sm">Bạn chưa có chuyến đang hoạt động.</p>';
    return;
  }
  container.innerHTML = list.map(function(item) {
    return '<div class="guide-trip-item"><h4>' + escapeHtml(item.tour_title || 'Tour') + '</h4>' +
      '<p><i class="bx bx-map"></i> ' + escapeHtml(item.destination || '--') + '</p>' +
      '<p><i class="bx bx-calendar"></i> ' + escapeHtml(item.trip_date || '--') + '</p>' +
      '<strong>' + (item.status === 'in_progress' ? 'Đang thực hiện' : 'Đã được phân công') + '</strong></div>';
  }).join('');
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

function renderCheckoutTimelinePreview(title, location, duration, isComboMode, comboItems) {
  var container = document.getElementById('checkoutTimelineList');
  if (!container) return;
  var text = (title || '') + ' ' + (location || '');
  var textLower = text.toLowerCase();
  var dest = location || 'Điểm đến du lịch';
  if (textLower.indexOf('phú quốc') !== -1) dest = 'Phú Quốc';
  else if (textLower.indexOf('sapa') !== -1 || textLower.indexOf('sa pa') !== -1 || textLower.indexOf('fansipan') !== -1) dest = 'Sa Pa';
  else if (textLower.indexOf('hà giang') !== -1) dest = 'Hà Giang';
  else if (textLower.indexOf('hạ long') !== -1) dest = 'Hạ Long';
  else if (textLower.indexOf('mộc châu') !== -1) dest = 'Mộc Châu';
  else if (textLower.indexOf('tam đảo') !== -1) dest = 'Tam Đảo';
  else if (textLower.indexOf('nha trang') !== -1 || textLower.indexOf('vĩnh hy') !== -1) dest = 'Nha Trang';
  else if (textLower.indexOf('đà nẵng') !== -1) dest = 'Đà Nẵng';
  else if (textLower.indexOf('ninh bình') !== -1) dest = 'Ninh Bình';
  else if (textLower.indexOf('đà lạt') !== -1) dest = 'Đà Lạt';
  else if (textLower.indexOf('huế') !== -1) dest = 'Huế';
  else if (textLower.indexOf('hội an') !== -1) dest = 'Hội An';
  else if (textLower.indexOf('hà nội') !== -1) dest = 'Hà Nội';

  var durText = String(duration || title || '').toLowerCase();
  var isOneDay = durText.indexOf('1 ngày') !== -1 || durText.indexOf('1n0đ') !== -1 || durText.indexOf('trong ngày') !== -1 || duration === '1' || duration === '1N0Đ';
  var isThreeDays = durText.indexOf('3 ngày') !== -1 || durText.indexOf('3n') !== -1 || durText.indexOf('3n2đ') !== -1 || duration === '3' || duration === '3N2Đ';
  var isTwoDays = durText.indexOf('2 ngày') !== -1 || durText.indexOf('2n') !== -1 || durText.indexOf('2n1đ') !== -1 || duration === '2' || duration === '2N1Đ';

  var timelineSteps = [];

  if (isComboMode && Array.isArray(comboItems) && comboItems.length > 0) {
    timelineSteps = comboItems.map(function(item, idx) {
      var itemDest = item.location || item.title || ('Điểm tham quan ' + (idx + 1));
      return {
        time: 'Ngày ' + (idx + 1) + ' (08:00 - 18:00)',
        badgeClass: 'badge-transit',
        icon: 'bx-navigation',
        title: 'Chặng ' + (idx + 1) + ': Hành trình liên tuyến đến ' + itemDest,
        sub: 'Xe du lịch đời mới đưa đón, di chuyển theo cung đường tối ưu và hướng dẫn viên đồng hành chăm sóc đoàn.'
      };
    });
    timelineSteps.push({
      time: 'Hoàn tất combo',
      badgeClass: 'badge-return',
      icon: 'bx-check-circle',
      title: 'Kết thúc chuyến đi liên tuyến & Xe đưa về điểm đón',
      sub: 'Đoàn hoàn thành toàn bộ hành trình combo liên tỉnh và trở về điểm hẹn an toàn.'
    });
  } else if (isOneDay) {
    timelineSteps = [
      {
        time: '07:30 - 08:30',
        badgeClass: 'badge-departure',
        icon: 'bx-car',
        title: 'Khởi hành & Đón khách tại điểm hẹn',
        sub: 'Tập trung tại điểm hẹn trung tâm, xe du lịch và HDV đón đoàn bắt đầu chuyến đi.'
      },
      {
        time: '11:30 - 13:00',
        badgeClass: 'badge-dining',
        icon: 'bx-restaurant',
        title: 'Nghỉ ngơi & Dùng bữa trưa theo tiêu chuẩn tour',
        sub: 'Dừng chân thư giãn tại nhà hàng địa phương trên hành trình.'
      },
      {
        time: '14:00 - 17:30',
        badgeClass: 'badge-sightseeing',
        icon: 'bx-map-pin',
        title: 'Tham quan các danh thắng biểu tượng tại ' + dest,
        sub: 'Khám phá các thắng cảnh nổi bật theo lộ trình đã được chuẩn bị.'
      },
      {
        time: '18:00 - 19:30',
        badgeClass: 'badge-return',
        icon: 'bx-check-circle',
        title: 'Khứ hồi trở về & Kết thúc tour trong ngày',
        sub: 'Xe đưa quý khách về lại điểm đón ban đầu an toàn, hoàn tất hành trình 1 ngày.'
      }
    ];
  } else if (isThreeDays) {
    timelineSteps = [
      {
        time: 'Ngày 1 (08:00 - 18:00)',
        badgeClass: 'badge-departure',
        icon: 'bx-car',
        title: 'Ngày 1: Đón đoàn & Di chuyển đến ' + dest,
        sub: 'Khởi hành từ điểm hẹn, di chuyển trên tuyến đường kết nối, nhận phòng khách sạn và dạo chơi làm quen không gian.'
      },
      {
        time: 'Ngày 2 (08:00 - 20:00)',
        badgeClass: 'badge-sightseeing',
        icon: 'bx-compass',
        title: 'Ngày 2: Trọn ngày khám phá trọng điểm danh lam & văn hóa ' + dest,
        sub: 'Tham quan các quần thể danh thắng nổi tiếng nhất, trải nghiệm sinh thái và thưởng thức phong vị bản địa.'
      },
      {
        time: 'Ngày 3 (08:00 - 17:00)',
        badgeClass: 'badge-return',
        icon: 'bx-check-circle',
        title: 'Ngày 3: Tự do thưởng ngoạn, mua quà đặc sản & Khứ hồi',
        sub: 'Dạo chơi buổi sáng, tự do chọn mua đặc sản làm quà cho người thân và xe đưa đoàn trở về điểm xuất phát.'
      }
    ];
  } else if (isTwoDays) {
    timelineSteps = [
      {
        time: 'Ngày 1 (08:00 - 18:00)',
        badgeClass: 'badge-departure',
        icon: 'bx-car',
        title: 'Ngày 1: Đón khách, khởi hành đến ' + dest + ' & Nhận phòng',
        sub: 'Di chuyển đến điểm đến, tham quan cụm danh lam mở đầu và nhận phòng nghỉ ngơi.'
      },
      {
        time: 'Ngày 2 (08:00 - 17:30)',
        badgeClass: 'badge-return',
        icon: 'bx-check-circle',
        title: 'Ngày 2: Khám phá danh lam biểu tượng & Khứ hồi về lại điểm hẹn',
        sub: 'Khám phá thắng cảnh chính trong ngày, mua sắm quà lưu niệm và xe đưa đoàn trở về an toàn.'
      }
    ];
  } else {
    timelineSteps = [
      {
        time: '08:00 - 09:00',
        badgeClass: 'badge-departure',
        icon: 'bx-car',
        title: 'Khởi hành & Bắt đầu chuyến đi khám phá ' + dest,
        sub: 'Xe du lịch chất lượng cao và hướng dẫn viên đón đoàn tại điểm hẹn.'
      },
      {
        time: 'Trong hành trình',
        badgeClass: 'badge-sightseeing',
        icon: 'bx-compass',
        title: 'Tham quan theo lộ trình được hướng dẫn viên dẫn dắt',
        sub: 'Khám phá các danh lam thắng cảnh và văn hóa đặc sắc tại điểm đến.'
      },
      {
        time: 'Kết thúc tour',
        badgeClass: 'badge-return',
        icon: 'bx-check-circle',
        title: 'Khứ hồi trở về điểm đón ban đầu an toàn',
        sub: 'Xe và hướng dẫn viên đưa quý khách trở về điểm hẹn xuất phát.'
      }
    ];
  }

  container.innerHTML = timelineSteps.map(function(step) {
    return (
      '<div class="checkout-timeline-item">' +
        '<div class="checkout-timeline-badge ' + step.badgeClass + '">' +
          '<i class="bx ' + step.icon + '"></i> ' + escapeHtml(step.time) +
        '</div>' +
        '<div class="checkout-timeline-body">' +
          '<h5 class="checkout-timeline-title">' + escapeHtml(step.title) + '</h5>' +
          '<p class="checkout-timeline-sub"><i class="bx bx-map-pin"></i> ' + escapeHtml(step.sub) + '</p>' +
        '</div>' +
      '</div>'
    );
  }).join('');
}

function initCheckoutData() {
  var isCheckout = window.location.pathname.endsWith('checkout.html');
  if (!isCheckout) return;

  var params = new URLSearchParams(window.location.search);
  var tourId = params.get('tourId') || params.get('tour_id');
  var hasSingleTourParam = Boolean(tourId || params.get('title'));

  if (hasSingleTourParam || params.get('mode') !== 'combo') {
    localStorage.removeItem('checkout_mode');
    localStorage.removeItem('checkout_combo_items');
  }

  var isComboMode = params.get('mode') === 'combo' && !hasSingleTourParam;
  var comboItems = [];
  if (isComboMode) {
    try {
      comboItems = JSON.parse(localStorage.getItem('checkout_combo_items') || '[]');
      if (!Array.isArray(comboItems)) comboItems = [];
    } catch (e) {
      comboItems = [];
    }
  }

  var title = params.get('title');
  var price = parseInt(params.get('price'));
  var originalPrice = parseInt(params.get('original'));
  var duration = params.get('duration');
  var img = params.get('img');
  var locationParam = params.get('location') || '';

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
  var payBtn = document.getElementById('checkoutPayBtn');

  var comboCard = document.getElementById('checkoutComboCard');
  var comboList = document.getElementById('checkoutComboList');
  var comboBadge = document.getElementById('checkoutComboBadge');

  if (tourId && (!title || !price)) {
    fetchApi('/api/tours/' + encodeURIComponent(tourId)).then(function(res) {
      if (res.ok) return res.json();
      return null;
    }).then(function(tourData) {
      if (!tourData) return;
      title = tourData.title || title;
      price = tourData.discount_price || tourData.price || price;
      duration = (tourData.duration_days || 1) + 'N' + (tourData.duration_nights || 0) + 'Đ';
      img = (tourData.images && tourData.images[0]) || img;
      locationParam = tourData.location || locationParam;
      if (titleEl) titleEl.textContent = title;
      if (imgEl && img) imgEl.src = img;
      if (durationEl && duration) durationEl.innerHTML = '<i class="bx bx-time"></i> ' + duration;
      renderCheckoutTimelinePreview(title, locationParam, duration, isComboMode, comboItems);
      updateCheckoutTotals();
    }).catch(function() {});
  }

  if (!isComboMode && (!title || !price) && !tourId) {
    if (titleEl) titleEl.textContent = 'Vui lòng chọn tour từ trang Tour du lịch';
    return;
  }
  if (isComboMode && comboItems.length === 0 && (!title || !price)) {
    if (titleEl) titleEl.textContent = 'Combo chưa có chuyến đi nào. Vui lòng chọn lộ trình từ chatbot';
    if (payBtn) payBtn.disabled = true;
    return;
  }

  renderCheckoutTimelinePreview(title, locationParam, duration, isComboMode, comboItems);

  var currentVoucher = null;

  function getBasePrice() {
    if (isComboMode) {
      return comboItems.reduce(function(acc, item) {
        return acc + (Number(item.price) || 0);
      }, 0);
    }
    return Number(price) || 0;
  }

  function updateCheckoutTotals() {
    var fmt = new Intl.NumberFormat('vi-VN');
    var adults = getPassengerCount(adultsSelect, 2);
    var children = getPassengerCount(childrenSelect, 0);
    var insurance = insuranceCheckbox && insuranceCheckbox.checked ? 150000 : 0;
    var basePrice = getBasePrice();
    var adultTotal = basePrice * adults;
    var childTotal = Math.round(basePrice * 0.5) * children;
    var insuranceTotal = insurance * (adults + children);
    var subtotal = adultTotal + childTotal + insuranceTotal;
    var discount = calculateVoucherDiscount(currentVoucher, subtotal, insuranceTotal);
    var total = Math.max(0, subtotal - discount);

    if (isComboMode) {
      if (titleEl) titleEl.textContent = 'Combo lộ trình (' + comboItems.length + ' chuyến)';
      if (durationEl) durationEl.innerHTML = '<i class="bx bx-time"></i> ' + comboItems.length + ' chặng di chuyển';
      if (imgEl && comboItems.length > 0 && comboItems[0].image) imgEl.src = comboItems[0].image;
    } else {
      if (titleEl) titleEl.textContent = title;
      if (imgEl && img) imgEl.src = img;
      if (durationEl && duration) durationEl.innerHTML = '<i class="bx bx-time"></i> ' + duration;
    }

    if (adultLabel) adultLabel.textContent = 'Người lớn x' + adults;
    if (adultPrice) adultPrice.textContent = fmt.format(adultTotal) + '₫';
    if (childrenLabel) childrenLabel.textContent = 'Trẻ em x' + children;
    if (childrenPrice) childrenPrice.textContent = fmt.format(childTotal) + '₫';
    if (insurancePrice) insurancePrice.textContent = fmt.format(insuranceTotal) + '₫';
    if (voucherValue) voucherValue.textContent = discount ? '-' + fmt.format(discount) + '₫' : '--';
    if (totalEl) totalEl.textContent = fmt.format(total) + '₫';
  }

  function renderComboItemsList() {
    if (!isComboMode || !comboList) return;
    if (comboCard) comboCard.style.display = 'block';

    if (comboItems.length === 0) {
      comboList.innerHTML = '<div class="card p-4 text-center text-muted" style="border: 1px dashed #cbd5e1; border-radius: 8px;">Bạn đã bỏ tất cả các chuyến trong combo. Vui lòng quay lại chatbot hoặc danh sách tour để chọn lại.</div>';
      if (comboBadge) comboBadge.textContent = '0 chuyến';
      if (payBtn) payBtn.disabled = true;
      updateCheckoutTotals();
      return;
    }

    if (payBtn) payBtn.disabled = false;
    if (comboBadge) comboBadge.textContent = comboItems.length + ' chuyến';

    comboList.innerHTML = comboItems.map(function(item, index) {
      var itemPrice = Number(item.price) || 0;
      var itemImg = item.image || 'https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=150&q=80';
      return (
        '<div class="flex items-center justify-between gap-3 p-3 border rounded-lg bg-white" data-combo-tour-id="' + escapeHtml(item.tour_id) + '" style="border: 1px solid var(--border-color); border-radius: 10px; background: #fff; margin-bottom: 8px;">' +
          '<div class="flex items-center gap-3" style="min-width: 0; flex: 1;">' +
            '<img src="' + escapeHtml(itemImg) + '" alt="' + escapeHtml(item.title) + '" style="width: 54px; height: 54px; border-radius: 8px; object-fit: cover; flex-shrink: 0;">' +
            '<div style="min-width: 0;">' +
              '<h4 class="font-semibold text-sm" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 2px;">' + escapeHtml(item.title) + '</h4>' +
              '<p class="text-muted text-xs" style="margin-bottom: 2px;"><i class="bx bx-map-pin"></i> ' + escapeHtml(item.location || 'Điểm đến') + '</p>' +
              '<span class="font-bold text-primary text-sm">' + formatCurrency(itemPrice) + '</span>' +
            '</div>' +
          '</div>' +
          '<button type="button" class="btn btn-outline btn-small checkout-remove-leg-btn" data-index="' + index + '" style="color: #ef4444; border-color: #fca5a5; padding: 6px 12px; font-size: 13px; border-radius: 6px; flex-shrink: 0;">' +
            '<i class="bx bx-trash"></i> Bỏ chuyến này' +
          '</button>' +
        '</div>'
      );
    }).join('');

    comboList.querySelectorAll('.checkout-remove-leg-btn').forEach(function(removeBtn) {
      removeBtn.addEventListener('click', function() {
        var idx = parseInt(this.getAttribute('data-index'), 10);
        if (Number.isInteger(idx) && idx >= 0 && idx < comboItems.length) {
          var removed = comboItems.splice(idx, 1)[0];
          localStorage.setItem('checkout_combo_items', JSON.stringify(comboItems));
          showToast('Đã bỏ "' + (removed.title || 'chuyến đi') + '" ra khỏi combo', 'warning');
          renderComboItemsList();
          renderCheckoutTimelinePreview(title, locationParam, duration, isComboMode, comboItems);
          updateCheckoutTotals();
        }
      });
    });
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

  if (isComboMode) {
    renderComboItemsList();
  }

  syncTravelDateLabel();
  updateCheckoutTotals();
  initCheckoutGuides();

  if (!isComboMode) {
    if (!tourId) {
      resolveTourIdFromTitle(title);
    } else {
      localStorage.setItem('checkout_tour_id', tourId);
    }
  }

  var emailInput = document.getElementById('checkoutContactEmail');
  if (emailInput) {
    emailInput.addEventListener('input', function() {
      validateCheckoutEmail(this.value);
    });
    emailInput.addEventListener('blur', function() {
      validateCheckoutEmail(this.value);
    });
  }
  if (localStorage.getItem('access_token')) {
    fetchApi('/api/users/me').then(function(res) {
      if (res.ok) return res.json();
      return null;
    }).then(function(userData) {
      if (!userData) return;
      var nameInput = document.getElementById('checkoutContactName');
      var mailInput = document.getElementById('checkoutContactEmail');
      var phoneInput = document.getElementById('checkoutContactPhone');
      if (nameInput && !nameInput.value && userData.full_name) {
        nameInput.value = userData.full_name;
      }
      if (mailInput && !mailInput.value && userData.email) {
        mailInput.value = userData.email;
        validateCheckoutEmail(userData.email);
      }
      if (phoneInput && !phoneInput.value && userData.phone) {
        phoneInput.value = userData.phone;
      }
    }).catch(function() {});
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

    select.innerHTML = '';
    guides.forEach(function(guide, idx) {
      var option = document.createElement('option');
      option.value = guide.id;
      option.textContent = guide.name + ' (' + (guide.experience_years || 3) + ' năm kinh nghiệm) - Hướng dẫn viên trong gói';
      if (idx === 0) option.selected = true;
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
    var normalizedTitle = title.toLowerCase().trim();
    var matched = tours.find(function(tour) {
      var normalizedTourTitle = String(tour.title || '').toLowerCase().trim();
      return normalizedTourTitle === normalizedTitle ||
        normalizedTitle.includes(normalizedTourTitle) ||
        normalizedTourTitle.includes(normalizedTitle);
    });
    if (matched && matched.id) {
      localStorage.setItem('checkout_tour_id', matched.id);
    }
  } catch (e) {}
}

function validateCheckoutEmail(email) {
  var feedbackEl = document.getElementById('checkoutEmailFeedback');
  if (!feedbackEl) return false;
  var val = String(email || '').trim();
  if (!val) {
    feedbackEl.style.display = 'none';
    return false;
  }
  var regex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  if (!regex.test(val)) {
    feedbackEl.style.display = 'block';
    feedbackEl.style.backgroundColor = '#fef2f2';
    feedbackEl.style.color = '#dc2626';
    feedbackEl.style.border = '1px solid #fecaca';
    feedbackEl.innerHTML = '<i class="bx bx-error-circle"></i> Định dạng email chưa đúng (ví dụ: hoten@gmail.com)';
    return false;
  }
  var lower = val.toLowerCase();
  var isGmail = lower.endsWith('@gmail.com');
  feedbackEl.style.display = 'block';
  if (isGmail) {
    feedbackEl.style.backgroundColor = '#ecfdf5';
    feedbackEl.style.color = '#059669';
    feedbackEl.style.border = '1px solid #a7f3d0';
    feedbackEl.innerHTML = '<i class="bx bx-check-circle"></i> Gmail chính xác. Hợp đồng du lịch và lịch trình chi tiết sẽ tự động gửi về địa chỉ này.';
  } else {
    feedbackEl.style.backgroundColor = '#eff6ff';
    feedbackEl.style.color = '#2563eb';
    feedbackEl.style.border = '1px solid #bfdbfe';
    feedbackEl.innerHTML = '<i class="bx bx-check-circle"></i> Email hợp lệ để nhận hợp đồng du lịch điện tử.';
  }
  return true;
}

function buildComboBookingPayload() {
  var raw = localStorage.getItem('checkout_combo_items');
  var comboItems = [];
  try {
    comboItems = JSON.parse(raw || '[]');
  } catch (e) {
    comboItems = [];
  }
  if (!Array.isArray(comboItems) || comboItems.length === 0) {
    showToast('Combo chưa có chuyến đi nào, vui lòng chọn lại tour', 'warning');
    return null;
  }

  var travelDate = document.getElementById('checkoutTravelDate') ? document.getElementById('checkoutTravelDate').value : '';
  var adults = getPassengerCount(document.getElementById('checkoutAdults'), 2);
  var children = getPassengerCount(document.getElementById('checkoutChildren'), 0);
  var insurance = document.getElementById('checkoutInsurance') ? document.getElementById('checkoutInsurance').checked : false;
  var phone = document.getElementById('checkoutContactPhone') ? document.getElementById('checkoutContactPhone').value.trim() : '';
  var contactName = document.getElementById('checkoutContactName') ? document.getElementById('checkoutContactName').value.trim() : '';
  var contactEmail = document.getElementById('checkoutContactEmail') ? document.getElementById('checkoutContactEmail').value.trim() : '';
  var note = document.getElementById('checkoutNote') ? document.getElementById('checkoutNote').value.trim() : '';
  var voucherCode = document.getElementById('checkoutVoucher') ? document.getElementById('checkoutVoucher').value.trim().toUpperCase() : '';

  var selectedOption = document.querySelector('.payment-option.selected');
  var paymentMethod = selectedOption ? selectedOption.getAttribute('data-method') : 'credit_card';
  if (paymentMethod === 'qr') {
    paymentMethod = 'bank_transfer';
  }

  if (!contactEmail || !/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(contactEmail)) {
    showToast('Vui lòng nhập Email / Gmail chính xác để nhận hợp đồng chuyến đi', 'warning');
    if (document.getElementById('checkoutContactEmail')) {
      document.getElementById('checkoutContactEmail').focus();
    }
    return null;
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
    items: comboItems.map(function(item) {
      return {
        tour_id: item.tour_id,
        travel_date: travelDate
      };
    }),
    adults: adults,
    children: children,
    insurance: insurance,
    coupon_code: voucherCode || null,
    payment_method: paymentMethod,
    contact_name: contactName || null,
    contact_email: contactEmail,
    contact_phone: phone,
    note: note || null
  };
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
  var contactName = document.getElementById('checkoutContactName') ? document.getElementById('checkoutContactName').value.trim() : '';
  var contactEmail = document.getElementById('checkoutContactEmail') ? document.getElementById('checkoutContactEmail').value.trim() : '';
  var note = document.getElementById('checkoutNote') ? document.getElementById('checkoutNote').value.trim() : '';
  var voucherCode = document.getElementById('checkoutVoucher') ? document.getElementById('checkoutVoucher').value.trim().toUpperCase() : '';

  var selectedOption = document.querySelector('.payment-option.selected');
  var paymentMethod = selectedOption ? selectedOption.getAttribute('data-method') : 'credit_card';
  if (paymentMethod === 'qr') {
    paymentMethod = 'bank_transfer';
  }

  if (!contactEmail || !/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(contactEmail)) {
    showToast('Vui lòng nhập Email / Gmail chính xác để nhận hợp đồng chuyến đi', 'warning');
    if (document.getElementById('checkoutContactEmail')) {
      document.getElementById('checkoutContactEmail').focus();
    }
    return null;
  }
  if (!travelDate) {
    showToast('Vui lòng chọn ngày khởi hành', 'warning');
    return null;
  }
  if (!phone) {
    showToast('Vui lòng nhập số điện thoại liên hệ', 'warning');
    return null;
  }

  var guideSelect = document.getElementById('checkoutGuideSelect');
  var guideId = guideSelect && guideSelect.value ? guideSelect.value : null;
  var guideNote = document.getElementById('checkoutGuideNote') ? document.getElementById('checkoutGuideNote').value.trim() : null;

  return {
    tour_id: tourId,
    travel_date: travelDate,
    adults: adults,
    children: children,
    insurance: insurance,
    coupon_code: voucherCode || null,
    payment_method: paymentMethod,
    contact_name: contactName || null,
    contact_email: contactEmail,
    contact_phone: phone,
    note: note || null,
    guide_id: guideId,
    guide_note: guideNote
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

function renderTourCardHTML(tour, showReason) {
  var img = (tour.images && tour.images.length > 0) ? tour.images[0] : 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=960&q=80';
  var priceVal = Number(tour.discount_price || tour.price || 0);
  var hasDiscount = tour.discount_price && Number(tour.discount_price) < Number(tour.price);
  var oldPriceHTML = hasDiscount ? '<span class="tour-price-old">' + formatCurrency(tour.price) + '</span>' : '';
  
  var badgesHTML = '';
  var tags = tour.tags || [];
  if (tags.indexOf('hot') !== -1) {
    badgesHTML += '<span class="tour-badge tour-badge-hot"><i class="bx bxs-hot"></i> HOT</span>';
  }
  if (tags.indexOf('best-seller') !== -1) {
    badgesHTML += '<span class="tour-badge tour-badge-bestseller"><i class="bx bxs-award"></i> Bán chạy</span>';
  } else if (tags.indexOf('luxury') !== -1) {
    badgesHTML += '<span class="tour-badge tour-badge-luxury"><i class="bx bxs-crown"></i> Cao cấp</span>';
  }

  var reasonHTML = '';
  if (showReason && tour.match_reason) {
    var matchPct = tour.match_percentage ? ' (' + tour.match_percentage + '%)' : '';
    reasonHTML = '<div class="tour-reason-badge"><i class="bx bx-sparkles"></i> ' + escapeHtml(tour.match_reason) + matchPct + '</div>';
  }

  var durationText = '';
  if (tour.duration_days) {
    durationText = tour.duration_days + 'N' + (tour.duration_nights !== undefined ? tour.duration_nights + 'Đ' : '');
  }

  return (
    '<div class="tour-card-item">' +
      '<div class="tour-card-thumb">' +
        '<img src="' + escapeHtml(img) + '" alt="' + escapeHtml(tour.title) + '" loading="lazy" onerror="this.onerror=null;this.src=\'https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=960&q=80\';">' +
        '<div class="tour-badge-stack">' + badgesHTML + '</div>' +
      '</div>' +
      '<div class="tour-card-body">' +
        '<div class="tour-meta-row">' +
          '<span class="tour-meta-loc"><i class="bx bx-map"></i> ' + escapeHtml(tour.location || 'Việt Nam') + '</span>' +
          (durationText ? '<span><i class="bx bx-time-five"></i> ' + escapeHtml(durationText) + '</span>' : '') +
        '</div>' +
        '<h3 class="tour-card-title" title="' + escapeHtml(tour.title) + '">' + escapeHtml(tour.title) + '</h3>' +
        reasonHTML +
        '<div class="tour-stats-row">' +
          '<div class="tour-rating"><i class="bx bxs-star"></i> ' + (tour.rating || 4.8).toFixed(1) + ' <span class="tour-rating-count">(' + (tour.review_count || 100) + ')</span></div>' +
        '</div>' +
        '<div class="tour-card-footer">' +
          '<div class="tour-price-box">' +
            oldPriceHTML +
            '<span class="tour-price-current">' + formatCurrency(priceVal) + '</span>' +
          '</div>' +
          '<a href="checkout.html?tour_id=' + escapeHtml(tour.id) + '&title=' + encodeURIComponent(tour.title || '') + '&price=' + encodeURIComponent(priceVal) + '&duration=' + encodeURIComponent(durationText) + '&img=' + encodeURIComponent(img) + '&location=' + encodeURIComponent(tour.location || '') + '" class="btn-book-card"><i class="bx bx-calendar-check"></i> Đặt tour</a>' +
        '</div>' +
      '</div>' +
    '</div>'
  );
}

async function initTrendingTours() {
  var grid = document.getElementById('trendingToursGrid');
  if (!grid) return;

  try {
    var res = await fetchApi('/api/tours/hot?limit=8');
    if (!res.ok) throw new Error('Không thể tải tour');
    var tours = await res.json();
    if (!tours || tours.length === 0) {
      grid.innerHTML = '<div class="card p-6 text-center text-muted w-full">Chưa có tour thịnh hành nào.</div>';
      return;
    }
    grid.innerHTML = tours.map(function(t) {
      return renderTourCardHTML(t, false);
    }).join('');
  } catch (e) {
    grid.innerHTML = '<div class="card p-6 text-center text-muted w-full">Tạm thời không tải được danh sách tour thịnh hành.</div>';
  }
}

async function initPersonalizedRecommendations() {
  var grid = document.getElementById('recommendationsToursGrid');
  if (!grid) return;

  var currentBudget = 'all';
  var currentCategory = 'all';

  var budgetPills = document.querySelectorAll('#recBudgetFilter .filter-pill');
  var categoryPills = document.querySelectorAll('#recCategoryFilter .filter-pill');

  async function fetchAndRenderRecommendations() {
    grid.innerHTML = '<div class="card p-6 text-center text-muted w-full"><i class="bx bx-loader-alt bx-spin"></i> Đang chọn lọc các hành trình phù hợp nhất...</div>';
    try {
      var query = '/api/tours/recommendations?limit=8';
      if (currentBudget !== 'all') {
        query += '&max_budget=' + encodeURIComponent(currentBudget);
      }
      if (currentCategory !== 'all') {
        query += '&category=' + encodeURIComponent(currentCategory);
      }

      var res = await fetchApi(query);
      if (!res.ok) throw new Error('Lỗi khi lấy gợi ý');
      var tours = await res.json();
      if (!tours || tours.length === 0) {
        grid.innerHTML = '<div class="card p-6 text-center text-muted w-full">Không tìm thấy tour nào phù hợp với tiêu chí lọc hiện tại. Hãy thử mở rộng ngân sách hoặc đổi danh mục.</div>';
        return;
      }
      grid.innerHTML = tours.map(function(t) {
        return renderTourCardHTML(t, true);
      }).join('');
    } catch (err) {
      grid.innerHTML = '<div class="card p-6 text-center text-muted w-full">Không thể tải gợi ý du lịch vào lúc này.</div>';
    }
  }

  budgetPills.forEach(function(btn) {
    btn.addEventListener('click', function() {
      budgetPills.forEach(function(b) { b.classList.remove('active'); });
      btn.classList.add('active');
      currentBudget = btn.getAttribute('data-budget') || 'all';
      fetchAndRenderRecommendations();
    });
  });

  categoryPills.forEach(function(btn) {
    btn.addEventListener('click', function() {
      categoryPills.forEach(function(c) { c.classList.remove('active'); });
      btn.classList.add('active');
      currentCategory = btn.getAttribute('data-category') || 'all';
      fetchAndRenderRecommendations();
    });
  });

  try {
    var userRes = await fetchApi('/api/users/me');
    if (userRes.ok) {
      var userData = await userRes.json();
      var subtitleEl = document.getElementById('recSubtitle');
      if (subtitleEl && userData.full_name) {
        var userPrefs = userData.preferences && userData.preferences.length > 0 ? ' (' + userData.preferences.join(', ') + ')' : '';
        subtitleEl.textContent = 'Chào ' + userData.full_name + '! Hệ thống đã tối ưu gợi ý theo gu' + userPrefs + ' và lịch sử du lịch của bạn.';
      }
    }
  } catch (ignored) {}

  await fetchAndRenderRecommendations();
}

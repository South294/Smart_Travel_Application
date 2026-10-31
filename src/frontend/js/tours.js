var tourCatalog = [];
var showingAllTours = false;

document.addEventListener('DOMContentLoaded', function() {
  initTourFilters();
});

async function initTourFilters() {
  var grid = document.getElementById('toursListGrid');
  if (!grid) return;

  var destinationInput = document.getElementById('tourFilterDestination');
  var categoryWrap = document.getElementById('tourFilterCategories');
  var priceMinInput = document.getElementById('tourFilterPriceMin');
  var priceMaxInput = document.getElementById('tourFilterPriceMax');
  var durationSelect = document.getElementById('tourFilterDuration');
  var ratingsWrap = document.getElementById('tourFilterRatings');
  var applyBtn = document.getElementById('tourFilterApply');
  var resetBtn = document.getElementById('tourFilterReset');
  var sortSelect = document.querySelector('.sort-select');
  var showAllBtn = document.getElementById('showAllToursBtn');
  var showHotBtn = document.getElementById('showHotToursBtn');

  try {
    var response = await fetchApi('/api/tours');
    if (!response.ok) throw new Error('Không thể tải danh sách tour');
    tourCatalog = await response.json();
    if (!Array.isArray(tourCatalog)) tourCatalog = [];
    renderHotTours(tourCatalog);
    renderCurrentView();
  } catch (error) {
    document.getElementById('toursHotGrid').innerHTML = '<div class="tour-empty-state">Tạm thời chưa tải được danh sách tour.</div>';
    document.getElementById('toursResultCount').textContent = '0';
  }

  function getSelectedCategory() {
    var activeChip = categoryWrap ? categoryWrap.querySelector('.filter-chip.active') : null;
    return activeChip ? activeChip.getAttribute('data-value') || 'Tất cả' : 'Tất cả';
  }

  function getSelectedRatings() {
    var ratings = [];
    if (!ratingsWrap) return ratings;
    ratingsWrap.querySelectorAll('input[type="checkbox"]').forEach(function(input) {
      if (input.checked) ratings.push(parseInt(input.value, 10));
    });
    return ratings;
  }

  function getFilteredTours() {
    var query = destinationInput ? destinationInput.value.trim().toLowerCase() : '';
    var category = getSelectedCategory();
    var minPrice = priceMinInput && priceMinInput.value ? Number(priceMinInput.value) : null;
    var maxPrice = priceMaxInput && priceMaxInput.value ? Number(priceMaxInput.value) : null;
    var durationFilter = durationSelect ? durationSelect.value : 'all';
    var selectedRatings = getSelectedRatings();

    return tourCatalog.filter(function(tour) {
      var title = String(tour.title || '').toLowerCase();
      var location = String(tour.location || '').toLowerCase();
      var price = Number(tour.discount_price || tour.price || 0);
      var rating = Number(tour.rating || 0);
      var duration = Number(tour.duration_days || 0);
      var categoryMatch = category === 'Tất cả' || categoryMatches(tour.category, category);
      var durationMatch = durationFilter === 'all' ||
        (durationFilter === '1-2' && duration >= 1 && duration <= 2) ||
        (durationFilter === '3-4' && duration >= 3 && duration <= 4) ||
        (durationFilter === '5-7' && duration >= 5 && duration <= 7) ||
        (durationFilter === '7+' && duration >= 8);
      var ratingMatch = selectedRatings.length === 0 || rating >= Math.min.apply(null, selectedRatings);
      return (!query || title.includes(query) || location.includes(query)) &&
        categoryMatch &&
        (minPrice === null || price >= minPrice) &&
        (maxPrice === null || price <= maxPrice) &&
        durationMatch &&
        ratingMatch;
    });
  }

  function renderCurrentView() {
    var filteredTours = sortTours(getFilteredTours(), sortSelect ? sortSelect.value : 'Đánh giá tốt nhất');
    if (showingAllTours) {
      document.getElementById('toursResultCount').textContent = String(filteredTours.length);
      renderGroupedTours(filteredTours);
    } else {
      renderHotTours(filteredTours);
    }
  }

  function applyFilters() {
    renderCurrentView();
  }

  function resetFilters() {
    if (destinationInput) destinationInput.value = '';
    if (priceMinInput) priceMinInput.value = '';
    if (priceMaxInput) priceMaxInput.value = '';
    if (durationSelect) durationSelect.value = 'all';
    if (categoryWrap) {
      categoryWrap.querySelectorAll('.filter-chip').forEach(function(chip) {
        chip.classList.toggle('active', chip.getAttribute('data-value') === 'Tất cả');
      });
    }
    if (ratingsWrap) {
      ratingsWrap.querySelectorAll('input[type="checkbox"]').forEach(function(input) {
        input.checked = false;
      });
    }
    applyFilters();
  }

  function showAllTours() {
    showingAllTours = true;
    document.getElementById('toursHotSection').hidden = true;
    document.getElementById('toursAllSection').hidden = false;
    renderCurrentView();
  }

  function showHotTours() {
    showingAllTours = false;
    document.getElementById('toursHotSection').hidden = false;
    document.getElementById('toursAllSection').hidden = true;
    renderHotTours(getFilteredTours());
  }

  if (categoryWrap) {
    categoryWrap.querySelectorAll('.filter-chip').forEach(function(chip) {
      chip.addEventListener('click', function() {
        categoryWrap.querySelectorAll('.filter-chip').forEach(function(other) { other.classList.remove('active'); });
        chip.classList.add('active');
        applyFilters();
      });
    });
  }
  if (applyBtn) applyBtn.addEventListener('click', applyFilters);
  if (resetBtn) resetBtn.addEventListener('click', resetFilters);
  if (showAllBtn) showAllBtn.addEventListener('click', showAllTours);
  if (showHotBtn) showHotBtn.addEventListener('click', showHotTours);
  if (destinationInput) destinationInput.addEventListener('input', applyFilters);
  if (priceMinInput) priceMinInput.addEventListener('input', applyFilters);
  if (priceMaxInput) priceMaxInput.addEventListener('input', applyFilters);
  if (durationSelect) durationSelect.addEventListener('change', applyFilters);
  if (ratingsWrap) ratingsWrap.addEventListener('change', applyFilters);
  if (sortSelect) sortSelect.addEventListener('change', applyFilters);
}

function categoryMatches(category, selectedCategory) {
  var aliases = {
    'Biển đảo': ['sea'],
    'Núi rừng': ['mountain'],
    'Văn hóa': ['sight', 'cultural'],
    'Ẩm thực': ['sight'],
    'Phiêu lưu': ['mountain']
  };
  return (aliases[selectedCategory] || []).indexOf(String(category || '').toLowerCase()) !== -1;
}

function getHotTours(tours) {
  return tours.filter(function(tour) {
    var tags = (tour.tags || []).map(function(tag) { return String(tag).toLowerCase(); });
    return tags.indexOf('hot') !== -1 || tags.indexOf('best-seller') !== -1 || Number(tour.rating || 0) >= 4.8;
  }).sort(function(first, second) {
    return Number(second.rating || 0) - Number(first.rating || 0) || Number(second.review_count || 0) - Number(first.review_count || 0);
  }).slice(0, 8);
}

function renderHotTours(tours) {
  var grid = document.getElementById('toursHotGrid');
  var hotTours = getHotTours(tours);
  grid.innerHTML = hotTours.length ? hotTours.map(renderTourCard).join('') : '<div class="tour-empty-state">Chưa có tour hot.</div>';
  document.getElementById('toursResultCount').textContent = String(hotTours.length);
}

function renderGroupedTours(tours) {
  var container = document.getElementById('toursRegionList');
  var groups = {};
  tours.forEach(function(tour) {
    var province = String(tour.location || 'Việt Nam').split(',')[0].trim();
    if (!groups[province]) groups[province] = [];
    groups[province].push(tour);
  });
  var provinces = Object.keys(groups).sort(function(first, second) { return first.localeCompare(second, 'vi'); });
  container.innerHTML = provinces.length ? provinces.map(function(province) {
    return '<section class="tour-region-group"><div class="tour-region-heading"><h3><i class="bx bx-map-pin"></i> ' + escapeTourHTML(province) + '</h3><span>' + groups[province].length + ' tour</span></div><div class="tour-region-grid">' + groups[province].map(renderTourCard).join('') + '</div></section>';
  }).join('') : '<div class="tour-empty-state">Không tìm thấy tour phù hợp.</div>';
}

function renderTourCard(tour) {
  var image = tour.images && tour.images[0] ? tour.images[0] : 'https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=960&q=80';
  var duration = tour.duration || ((tour.duration_days ? tour.duration_days + 'N' : '1N') + (tour.duration_nights !== undefined ? tour.duration_nights + 'Đ' : '0Đ'));
  var tags = (tour.tags || []).map(function(tag) { return String(tag).toLowerCase(); });
  var price = Number(tour.discount_price || tour.price || 0);
  var oldPrice = tour.discount_price && Number(tour.discount_price) < Number(tour.price) ? '<span class="tour-card-old-price">' + formatTourCurrency(tour.price) + '</span>' : '';
  var badge = tags.indexOf('hot') !== -1 || tags.indexOf('best-seller') !== -1 ? '<span class="tour-card-badge"><i class="bx bxs-hot"></i> HOT</span>' : '';
  var bookingUrl = 'checkout.html?tour_id=' + encodeURIComponent(tour.id || '') +
    '&title=' + encodeURIComponent(tour.title || '') +
    '&price=' + encodeURIComponent(price) +
    '&duration=' + encodeURIComponent(duration) +
    '&img=' + encodeURIComponent(image) +
    '&location=' + encodeURIComponent(tour.location || '');
  return '<article class="tour-api-card" data-id="' + escapeTourHTML(tour.id || '') + '"><div class="tour-api-image" onclick="openTourDetailModal(\'' + escapeTourHTML(tour.id || '') + '\')" style="cursor:pointer;"><img src="' + escapeTourHTML(image) + '" alt="' + escapeTourHTML(tour.title) + '" loading="lazy" onerror="this.onerror=null;this.src=\'https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=960&q=80\';">' + badge + '</div><div class="tour-api-body"><div class="tour-api-meta"><span><i class="bx bx-map"></i> ' + escapeTourHTML(tour.location || 'Việt Nam') + '</span><span><i class="bx bx-time-five"></i> ' + duration + '</span></div><h3 onclick="openTourDetailModal(\'' + escapeTourHTML(tour.id || '') + '\')" style="cursor:pointer;">' + escapeTourHTML(tour.title) + '</h3><div class="tour-api-rating" onclick="openTourDetailModal(\'' + escapeTourHTML(tour.id || '') + '\')" style="cursor:pointer;"><i class="bx bxs-star"></i> ' + Number(tour.rating || 0).toFixed(1) + ' <span>(' + Number(tour.review_count || 0) + ' đánh giá)</span></div><div class="tour-api-footer"><div>' + oldPrice + '<strong>' + formatTourCurrency(price) + '</strong><small>/ khách</small></div><div class="flex gap-2 items-center"><button type="button" class="btn btn-outline btn-sm" onclick="openTourDetailModal(\'' + escapeTourHTML(tour.id || '') + '\')"><i class="bx bx-show"></i> Chi tiết</button><a href="' + bookingUrl + '" class="btn-book-tour"><i class="bx bx-calendar-check"></i> Đặt tour</a></div></div></div></article>';
}

function sortTours(tours, sortValue) {
  return tours.slice().sort(function(first, second) {
    if (sortValue === 'Giá thấp đến cao') return Number(first.discount_price || first.price) - Number(second.discount_price || second.price);
    if (sortValue === 'Giá cao đến thấp') return Number(second.discount_price || second.price) - Number(first.discount_price || first.price);
    if (sortValue === 'Mới nhất') return String(second.created_at || '').localeCompare(String(first.created_at || ''));
    return Number(second.rating || 0) - Number(first.rating || 0) || Number(second.review_count || 0) - Number(first.review_count || 0);
  });
}

function formatTourCurrency(value) {
  return new Intl.NumberFormat('vi-VN').format(Number(value || 0)) + '₫';
}

function escapeTourHTML(value) {
  return String(value || '').replace(/[&<>'"]/g, function(character) {
    return {'&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'}[character];
  });
}

var currentViewingTourId = null;

async function openTourDetailModal(tourId) {
  if (!tourId) return;
  var tour = tourCatalog.find(function(item) { return String(item.id) === String(tourId); });
  if (!tour) {
    try {
      var res = await fetchApi('/api/tours/' + tourId);
      if (res.ok) tour = await res.json();
    } catch (e) {}
  }
  if (!tour) return;
  currentViewingTourId = tour.id;

  var modal = document.getElementById('tourDetailModal');
  var titleEl = document.getElementById('tourDetailTitle');
  var imgEl = document.getElementById('tourDetailImage');
  var locEl = document.getElementById('tourDetailLocation');
  var durEl = document.getElementById('tourDetailDuration');
  var catEl = document.getElementById('tourDetailCategory');
  var priceEl = document.getElementById('tourDetailPrice');
  var ratingEl = document.getElementById('tourDetailRating');
  var reviewCountEl = document.getElementById('tourDetailReviewCount');
  var descEl = document.getElementById('tourDetailDesc');
  var bookBtn = document.getElementById('tourDetailBookBtn');

  var image = tour.images && tour.images[0] ? tour.images[0] : 'https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=960&q=80';
  var duration = tour.duration || ((tour.duration_days ? tour.duration_days + ' ngày ' : '') + (tour.duration_nights !== undefined ? tour.duration_nights + ' đêm' : ''));
  var price = Number(tour.discount_price || tour.price || 0);

  if (titleEl) titleEl.textContent = tour.title || 'Chi tiết tour';
  if (imgEl) {
    imgEl.src = image;
    imgEl.onerror = function() { this.onerror = null; this.src = 'https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=960&q=80'; };
  }
  if (locEl) locEl.textContent = tour.location || 'Việt Nam';
  if (durEl) durEl.textContent = duration || 'Theo lịch trình';
  if (catEl) catEl.textContent = tour.category === 'sea' ? 'Biển đảo' : (tour.category === 'mountain' ? 'Vùng núi & Trekking' : (tour.category === 'cultural' ? 'Di sản văn hóa' : (tour.category || 'Du lịch trải nghiệm')));
  if (priceEl) priceEl.textContent = formatTourCurrency(price);
  if (ratingEl) ratingEl.textContent = Number(tour.rating || 5.0).toFixed(1);
  if (reviewCountEl) reviewCountEl.textContent = '(' + Number(tour.review_count || 0) + ' đánh giá)';
  if (descEl) descEl.textContent = tour.description || 'Chuyến đi chất lượng cao được thiết kế trọn gói, mang lại cho bạn những phút giây thư giãn tuyệt đối cùng hướng dẫn viên chuyên nghiệp và nhiều điểm check-in hấp dẫn.';

  if (bookBtn) {
    bookBtn.href = 'checkout.html?tour_id=' + encodeURIComponent(tour.id || '') +
      '&title=' + encodeURIComponent(tour.title || '') +
      '&price=' + encodeURIComponent(price) +
      '&duration=' + encodeURIComponent(duration) +
      '&img=' + encodeURIComponent(image) +
      '&location=' + encodeURIComponent(tour.location || '');
  }

  await loadTourReviews(currentViewingTourId);
  if (modal) modal.classList.add('is-active');
}

function closeTourDetailModal() {
  var modal = document.getElementById('tourDetailModal');
  if (modal) modal.classList.remove('is-active');
  currentViewingTourId = null;
}

async function loadTourReviews(tourId) {
  var list = document.getElementById('tourReviewsList');
  if (!list) return;
  list.innerHTML = '<div class="text-muted text-sm">Đang tải danh sách đánh giá...</div>';
  try {
    var res = await fetchApi('/api/tours/' + tourId + '/reviews');
    if (!res.ok) throw new Error();
    var reviews = await res.json();
    if (!Array.isArray(reviews) || reviews.length === 0) {
      list.innerHTML = '<div class="text-muted text-sm">Chưa có đánh giá nào cho chuyến đi này. Hãy là người đầu tiên chia sẻ cảm nhận!</div>';
      return;
    }
    list.innerHTML = reviews.map(function(r) {
      var stars = '⭐'.repeat(Math.max(1, Math.min(5, Number(r.rating) || 5)));
      var dateStr = r.created_at ? new Date(r.created_at).toLocaleDateString('vi-VN') : '';
      return '<div class="card p-3" style="background:#fff; border:1px solid #e2e8f0; border-radius:8px;">' +
        '<div class="flex justify-between items-center mb-1">' +
        '<strong class="text-main">' + escapeTourHTML(r.user_name || 'Du khách') + '</strong>' +
        '<span class="text-xs text-muted">' + dateStr + '</span>' +
        '</div>' +
        '<div class="text-warning text-sm mb-1">' + stars + '</div>' +
        '<p class="text-sm text-muted mb-0" style="white-space:pre-wrap;">' + escapeTourHTML(r.comment || '') + '</p>' +
        '</div>';
    }).join('');
  } catch (err) {
    list.innerHTML = '<div class="text-muted text-sm">Không thể tải danh sách đánh giá lúc này.</div>';
  }
}

document.addEventListener('DOMContentLoaded', function() {
  var closeBtn1 = document.getElementById('closeTourDetailBtn');
  var closeBtn2 = document.getElementById('closeTourDetailBtn2');
  var reviewForm = document.getElementById('tourReviewForm');

  if (closeBtn1) closeBtn1.addEventListener('click', closeTourDetailModal);
  if (closeBtn2) closeBtn2.addEventListener('click', closeTourDetailModal);

  if (reviewForm) {
    reviewForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      var token = localStorage.getItem('token');
      if (!token) {
        alert('Vui lòng đăng nhập để gửi đánh giá chuyến đi.');
        window.location.href = 'auth.html';
        return;
      }
      if (!currentViewingTourId) return;

      var ratingVal = Number(document.getElementById('reviewRatingSelect').value) || 5;
      var commentVal = document.getElementById('reviewCommentInput').value.trim();
      if (!commentVal) {
        alert('Vui lòng nhập nhận xét của bạn.');
        return;
      }

      var submitBtn = document.getElementById('submitTourReviewBtn');
      var originalBtnText = submitBtn ? submitBtn.innerHTML : '';
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="bx bx-loader-alt"></i> Đang gửi...';
      }

      try {
        var res = await fetchApi('/api/tours/' + currentViewingTourId + '/reviews', {
          method: 'POST',
          body: JSON.stringify({ rating: ratingVal, comment: commentVal })
        });
        if (res.ok) {
          var updatedTour = await res.json();
          document.getElementById('reviewCommentInput').value = '';
          alert('Gửi đánh giá thành công! Cảm ơn nhận xét của bạn.');
          if (updatedTour && updatedTour.rating !== undefined) {
            var ratingEl = document.getElementById('tourDetailRating');
            var countEl = document.getElementById('tourDetailReviewCount');
            if (ratingEl) ratingEl.textContent = Number(updatedTour.rating).toFixed(1);
            if (countEl) countEl.textContent = '(' + Number(updatedTour.review_count || 0) + ' đánh giá)';
          }
          await loadTourReviews(currentViewingTourId);
        } else {
          var err = await res.json();
          alert(err.detail || 'Không thể gửi đánh giá');
        }
      } catch (err) {
        alert('Lỗi kết nối khi gửi đánh giá');
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = originalBtnText;
        }
      }
    });
  }

  var params = new URLSearchParams(window.location.search);
  var targetId = params.get('id') || params.get('tour_id');
  if (targetId) {
    setTimeout(function() {
      openTourDetailModal(targetId);
    }, 600);
  }
});

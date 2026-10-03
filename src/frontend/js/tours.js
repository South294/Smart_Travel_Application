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
  var tags = (tour.tags || []).map(function(tag) { return String(tag).toLowerCase(); });
  var price = Number(tour.discount_price || tour.price || 0);
  var oldPrice = tour.discount_price && Number(tour.discount_price) < Number(tour.price) ? '<span class="tour-card-old-price">' + formatTourCurrency(tour.price) + '</span>' : '';
  var badge = tags.indexOf('hot') !== -1 || tags.indexOf('best-seller') !== -1 ? '<span class="tour-card-badge"><i class="bx bxs-hot"></i> HOT</span>' : '';
  var duration = tour.duration_days ? tour.duration_days + 'N' + (tour.duration_nights || 0) + 'Đ' : '';
  return '<article class="tour-api-card"><div class="tour-api-image"><img src="' + escapeTourHTML(image) + '" alt="' + escapeTourHTML(tour.title) + '" loading="lazy">' + badge + '</div><div class="tour-api-body"><div class="tour-api-meta"><span><i class="bx bx-map"></i> ' + escapeTourHTML(tour.location || 'Việt Nam') + '</span><span><i class="bx bx-time-five"></i> ' + duration + '</span></div><h3>' + escapeTourHTML(tour.title) + '</h3><div class="tour-api-rating"><i class="bx bxs-star"></i> ' + Number(tour.rating || 0).toFixed(1) + ' <span>(' + Number(tour.review_count || 0) + ' đánh giá)</span></div><div class="tour-api-footer"><div>' + oldPrice + '<strong>' + formatTourCurrency(price) + '</strong><small>/ khách</small></div><a href="checkout.html?tour_id=' + encodeURIComponent(tour.id || '') + '" class="btn-book-tour"><i class="bx bx-calendar-check"></i> Đặt tour</a></div></div></article>';
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

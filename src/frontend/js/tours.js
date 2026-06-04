document.addEventListener('DOMContentLoaded', function() {
  initTourFilters();
});

function initTourFilters() {
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
  var resultCount = document.getElementById('toursResultCount');

  var cards = Array.prototype.slice.call(grid.querySelectorAll('.tour-card'));
  if (cards.length === 0) return;

  function getSelectedCategory() {
    var activeChip = categoryWrap ? categoryWrap.querySelector('.filter-chip.active') : null;
    return activeChip ? activeChip.getAttribute('data-value') || activeChip.textContent.trim() : 'Tất cả';
  }

  function getSelectedRatings() {
    if (!ratingsWrap) return [];
    var list = [];
    ratingsWrap.querySelectorAll('input[type="checkbox"]').forEach(function(cb) {
      if (cb.checked) list.push(parseInt(cb.value, 10));
    });
    return list;
  }

  function getDurationFilter() {
    return durationSelect ? durationSelect.value : 'all';
  }

  function parseNumberInput(input) {
    if (!input || input.value.trim() === '') return null;
    var value = Number(input.value);
    return Number.isFinite(value) ? value : null;
  }

  function matchDuration(days, filterValue) {
    if (!filterValue || filterValue === 'all') return true;
    if (!Number.isFinite(days)) return false;
    if (filterValue === '1-2') return days >= 1 && days <= 2;
    if (filterValue === '3-4') return days >= 3 && days <= 4;
    if (filterValue === '5-7') return days >= 5 && days <= 7;
    if (filterValue === '7+') return days >= 8;
    return true;
  }

  function matchRating(rating, selectedRatings) {
    if (selectedRatings.length === 0) return true;
    var minRating = Math.min.apply(null, selectedRatings);
    return rating >= minRating;
  }

  function applyFilters() {
    var query = destinationInput ? destinationInput.value.trim().toLowerCase() : '';
    var category = getSelectedCategory();
    var minPrice = parseNumberInput(priceMinInput);
    var maxPrice = parseNumberInput(priceMaxInput);
    var durationFilter = getDurationFilter();
    var selectedRatings = getSelectedRatings();

    var visibleCount = 0;
    cards.forEach(function(card) {
      var title = (card.getAttribute('data-title') || '').toLowerCase();
      var location = (card.getAttribute('data-location') || '').toLowerCase();
      var categoryValue = card.getAttribute('data-category') || '';
      var duration = Number(card.getAttribute('data-duration'));
      var price = Number(card.getAttribute('data-price'));
      var rating = Number(card.getAttribute('data-rating'));

      var matchQuery = !query || title.indexOf(query) !== -1 || location.indexOf(query) !== -1;
      var matchCategory = category === 'Tất cả' || categoryValue === category;
      var matchMinPrice = minPrice == null || (Number.isFinite(price) && price >= minPrice);
      var matchMaxPrice = maxPrice == null || (Number.isFinite(price) && price <= maxPrice);
      var matchDurationValue = matchDuration(duration, durationFilter);
      var matchRatingValue = matchRating(rating, selectedRatings);

      var isVisible = matchQuery && matchCategory && matchMinPrice && matchMaxPrice && matchDurationValue && matchRatingValue;
      card.style.display = isVisible ? '' : 'none';
      if (isVisible) visibleCount += 1;
    });

    if (resultCount) resultCount.textContent = String(visibleCount);
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
      ratingsWrap.querySelectorAll('input[type="checkbox"]').forEach(function(cb) {
        cb.checked = false;
      });
    }

    applyFilters();
  }

  if (categoryWrap) {
    categoryWrap.querySelectorAll('.filter-chip').forEach(function(chip) {
      chip.addEventListener('click', function() {
        categoryWrap.querySelectorAll('.filter-chip').forEach(function(other) {
          other.classList.remove('active');
        });
        chip.classList.add('active');
      });
    });
  }

  if (applyBtn) applyBtn.addEventListener('click', applyFilters);
  if (resetBtn) resetBtn.addEventListener('click', resetFilters);

  if (destinationInput) destinationInput.addEventListener('input', applyFilters);
  if (priceMinInput) priceMinInput.addEventListener('input', applyFilters);
  if (priceMaxInput) priceMaxInput.addEventListener('input', applyFilters);
  if (durationSelect) durationSelect.addEventListener('change', applyFilters);
  if (ratingsWrap) ratingsWrap.addEventListener('change', applyFilters);

  applyFilters();
}

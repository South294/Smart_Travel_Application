(function () {
  var API_BASE = window.SMART_TRAVEL_API_URL || 'http://localhost:8000';
  var sessionKey = 'smart_travel_chat_session';
  var historyKey = 'smart_travel_chat_history';

  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function formatCurrency(value) {
    return new Intl.NumberFormat('vi-VN').format(Number(value) || 0) + '₫';
  }

  function getSessionId() {
    var existing = localStorage.getItem(sessionKey);
    if (existing) return existing;
    var id = 'st-' + Date.now() + '-' + Math.random().toString(36).slice(2, 10);
    localStorage.setItem(sessionKey, id);
    return id;
  }

  function addMessage(container, content, type) {
    var message = document.createElement('div');
    message.className = 'chat-message chat-message-' + type;
    message.innerHTML = '<div class="chat-avatar"><i class="bx ' + (type === 'bot' ? 'bx-sparkles' : 'bx-user') + '"></i></div>' +
      '<div class="chat-bubble">' + escapeHtml(content).replace(/\n/g, '<br>') + '</div>';
    container.appendChild(message);
    container.scrollTop = container.scrollHeight;
    return message;
  }

  function saveChatMessage(content, type) {
    saveChatEntry({ content: content, type: type });
  }

  function saveChatEntry(entry) {
    try {
      var history = JSON.parse(localStorage.getItem(historyKey) || '[]');
      history.push(entry);
      localStorage.setItem(historyKey, JSON.stringify(history.slice(-30)));
    } catch (error) {
    }
  }

  function restoreChatHistory(container) {
    try {
      var history = JSON.parse(localStorage.getItem(historyKey) || '[]');
      if (!Array.isArray(history) || history.length === 0) return;
      container.innerHTML = '';
      history.forEach(function (item) {
        if (item && item.content && (item.type === 'user' || item.type === 'bot')) {
          addMessage(container, item.content, item.type);
        }
        if (item && item.kind === 'itinerary') renderItinerary(container, item.data);
        if (item && item.kind === 'recommendations') renderRecommendations(container, item.data);
      });
    } catch (error) {
    }
  }

  function renderRecommendations(container, recommendations) {
    if (!Array.isArray(recommendations) || recommendations.length === 0) return;
    var section = document.createElement('div');
    section.className = 'chat-recommendations';
    section.innerHTML = recommendations.map(function (item) {
      var image = item.image_url || 'https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=800&q=80';
      return '<article class="recommendation-card">' +
        '<img src="' + escapeHtml(image) + '" alt="' + escapeHtml(item.title) + '">' +
        '<div class="recommendation-content">' +
        '<span class="recommendation-location"><i class="bx bx-map-pin"></i> ' + escapeHtml(item.location) + '</span>' +
        '<h3>' + escapeHtml(item.title) + '</h3>' +
        '<p>' + escapeHtml(item.reason) + '</p>' +
        '<div class="recommendation-footer"><strong>' + formatCurrency(item.estimated_price) + '</strong>' +
        '<button type="button" class="btn btn-primary btn-small chat-tour-detail" data-tour-id="' + escapeHtml(item.tour_id) + '">Xem chi tiết</button></div>' +
        '</div></article>';
    }).join('');
    container.appendChild(section);
    section.querySelectorAll('.chat-tour-detail').forEach(function (button) {
      button.addEventListener('click', function () {
        openTourDetail(button.getAttribute('data-tour-id'));
      });
    });
    container.scrollTop = container.scrollHeight;
  }

  function setTourDetailText(id, value) {
    var element = document.getElementById(id);
    if (element) element.textContent = value || '';
  }

  function openTourDetail(tourId) {
    var modal = document.getElementById('chatTourDetailModal');
    var loading = document.getElementById('chatTourDetailLoading');
    var content = document.getElementById('chatTourDetailContent');
    if (!modal || !tourId) return;
    modal.classList.add('is-active');
    modal.setAttribute('aria-hidden', 'false');
    if (loading) loading.hidden = false;
    if (content) content.hidden = true;

    fetch(API_BASE + '/api/tours/' + encodeURIComponent(tourId))
      .then(function (response) {
        if (!response.ok) throw new Error('Không thể tải thông tin tour.');
        return response.json();
      })
      .then(function (tour) {
        var image = (tour.images && tour.images[0]) || 'https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=1000&q=80';
        var price = tour.discount_price || tour.price || 0;
        var bookingUrl = 'checkout.html?title=' + encodeURIComponent(tour.title || 'Tour du lịch') +
          '&price=' + encodeURIComponent(price) + '&img=' + encodeURIComponent(image) +
          '&tourId=' + encodeURIComponent(tour.id);
        var imageElement = document.getElementById('chatTourDetailImage');
        var bookingLink = document.getElementById('chatTourBookLink');
        var map = document.getElementById('chatTourDetailMap');
        if (imageElement) {
          imageElement.src = image;
          imageElement.alt = tour.title || 'Hình ảnh tour';
        }
        setTourDetailText('chatTourDetailTitle', tour.title);
        setTourDetailText('chatTourDetailLocation', tour.location);
        setTourDetailText('chatTourDetailDuration', (tour.duration_days || 0) + ' ngày ' + (tour.duration_nights || 0) + ' đêm');
        setTourDetailText('chatTourDetailRating', (tour.rating || 0) + ' (' + (tour.review_count || 0) + ' đánh giá)');
        setTourDetailText('chatTourDetailPrice', formatCurrency(price) + ' / khách');
        setTourDetailText('chatTourDetailTags', (tour.tags || []).join(' • '));
        setTourDetailText('chatTourDetailDescription', tour.description || ('Khám phá ' + (tour.location || 'điểm đến tuyệt đẹp') + ' với hành trình được lựa chọn từ dữ liệu tour đang hoạt động của SmartTravel.'));
        if (bookingLink) bookingLink.href = bookingUrl;
        if (map && Number.isFinite(Number(tour.lat)) && Number.isFinite(Number(tour.lng))) {
          var lat = Number(tour.lat);
          var lng = Number(tour.lng);
          map.src = 'https://www.openstreetmap.org/export/embed.html?bbox=' + (lng - 0.08) + '%2C' + (lat - 0.06) + '%2C' + (lng + 0.08) + '%2C' + (lat + 0.06) + '&layer=mapnik&marker=' + lat + '%2C' + lng;
          map.hidden = false;
        } else if (map) {
          map.hidden = true;
        }
        var googleMapLink = document.getElementById('chatTourGoogleMap');
        if (googleMapLink) {
          var mapQuery = Number.isFinite(Number(tour.lat)) && Number.isFinite(Number(tour.lng)) ? tour.lat + ',' + tour.lng : tour.location || tour.title;
          googleMapLink.href = 'https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(mapQuery);
        }
        if (loading) loading.hidden = true;
        if (content) content.hidden = false;
      })
      .catch(function (error) {
        if (loading) loading.textContent = error.message;
      });
  }

  function closeTourDetail() {
    var modal = document.getElementById('chatTourDetailModal');
    if (!modal) return;
    modal.classList.remove('is-active');
    modal.setAttribute('aria-hidden', 'true');
  }

  function renderItinerary(container, itinerary) {
    if (!Array.isArray(itinerary) || itinerary.length === 0) return;
    var section = document.createElement('section');
    section.className = 'chat-itinerary';
    section.innerHTML = '<strong><i class="bx bx-calendar-event"></i> Lịch trình gợi ý</strong>' + itinerary.map(function (day) {
      var activities = Array.isArray(day.activities) ? day.activities : [];
      return '<div class="chat-itinerary-day"><b>Ngày ' + escapeHtml(day.day) + ': ' + escapeHtml(day.title) + '</b>' +
        (activities.length ? '<ul>' + activities.map(function (activity) {
          return '<li>' + escapeHtml(activity) + '</li>';
        }).join('') + '</ul>' : '') + '</div>';
    }).join('');
    container.appendChild(section);
    container.scrollTop = container.scrollHeight;
  }

  function updateWeather(weather) {
    var element = document.getElementById('chatWeather');
    if (!element || !weather) return;
    var label = weather.condition === 'rain' ? 'Có mưa' :
      weather.condition === 'hot' ? 'Trời nóng' :
      weather.condition === 'clear' ? 'Trời quang' : 'Đang cập nhật';
    element.innerHTML = '<i class="bx bx-cloud"></i><span>' + escapeHtml(weather.city) + '</span><strong>' +
      (weather.temperature == null ? '--' : Math.round(weather.temperature) + '°C') + '</strong><small>' + label + '</small>';
  }

  async function loadWeather(cityInput) {
    var city = cityInput.value.trim() || 'Hà Nội';
    try {
      var response = await fetch(API_BASE + '/api/ai/weather?city=' + encodeURIComponent(city));
      if (response.ok) updateWeather(await response.json());
    } catch (error) {
      updateWeather({ city: city, condition: 'unknown' });
    }
  }

  async function sendMessage(input, cityInput, messages, sendButton) {
    var text = input.value.trim();
    if (!text || sendButton.disabled) return;
    input.value = '';
    sendButton.disabled = true;
    addMessage(messages, text, 'user');
    saveChatMessage(text, 'user');
    var loading = addMessage(messages, 'Đang đọc tin nhắn của bạn...', 'bot');
    loading.classList.add('is-loading');

    try {
      var response = await fetch(API_BASE + '/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          session_id: getSessionId(),
          city: cityInput.value.trim() || null
        })
      });
      var data = await response.json();
      loading.remove();
      if (!response.ok) {
        throw new Error(data.detail || 'Không thể kết nối với trợ lý AI.');
      }
      addMessage(messages, data.message, 'bot');
      saveChatMessage(data.message, 'bot');
      renderItinerary(messages, data.itinerary);
      if (Array.isArray(data.itinerary) && data.itinerary.length) {
        saveChatEntry({ kind: 'itinerary', data: data.itinerary });
      }
      renderRecommendations(messages, data.recommendations);
      if (Array.isArray(data.recommendations) && data.recommendations.length) {
        saveChatEntry({ kind: 'recommendations', data: data.recommendations });
      }
      updateWeather(data.weather);
    } catch (error) {
      loading.remove();
      addMessage(messages, error.message || 'Có lỗi xảy ra. Vui lòng thử lại.', 'bot');
    } finally {
      sendButton.disabled = false;
      input.focus();
    }
  }

  function initTravelChat() {
    var form = document.getElementById('travelChatForm');
    var input = document.getElementById('travelChatInput');
    var cityInput = document.getElementById('chatCity');
    var messages = document.getElementById('travelChatMessages');
    var sendButton = document.getElementById('travelChatSend');
    if (!form || !input || !messages || !sendButton) return;

    restoreChatHistory(messages);

    var tourModal = document.getElementById('chatTourDetailModal');
    if (tourModal) {
      tourModal.addEventListener('click', function (event) {
        if (event.target === tourModal || event.target.closest('[data-tour-modal-close]')) closeTourDetail();
      });
    }

    loadWeather(cityInput);
    if (cityInput) {
      cityInput.addEventListener('change', function () {
        loadWeather(cityInput);
      });
    }

    var widget = document.getElementById('chatFloatingWidget');
    var triggerBtn = document.getElementById('chatFloatingBtn');
    var closeBtn = document.getElementById('chatWidgetClose');
    var heroOpenBtn = document.getElementById('heroOpenChatBtn');

    function openChat() {
      if (!widget) return;
      widget.classList.add('is-open');
      widget.setAttribute('aria-hidden', 'false');
      if (triggerBtn) triggerBtn.classList.add('is-active');
      input.focus();
    }

    function closeChat() {
      if (!widget) return;
      widget.classList.remove('is-open');
      widget.setAttribute('aria-hidden', 'true');
      if (triggerBtn) triggerBtn.classList.remove('is-active');
    }

    function toggleChat() {
      if (!widget) return;
      if (widget.classList.contains('is-open')) {
        closeChat();
      } else {
        openChat();
      }
    }

    if (triggerBtn) {
      triggerBtn.addEventListener('click', toggleChat);
    }
    if (closeBtn) {
      closeBtn.addEventListener('click', closeChat);
    }
    if (heroOpenBtn) {
      heroOpenBtn.addEventListener('click', openChat);
    }
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') closeTourDetail();
      if (event.key === 'Escape' && widget && widget.classList.contains('is-open')) {
        closeChat();
      }
    });

    document.querySelectorAll('[data-chat-prompt]').forEach(function (button) {
      button.addEventListener('click', function () {
        input.value = button.getAttribute('data-chat-prompt') || '';
        input.focus();
      });
    });

    form.addEventListener('submit', function (event) {
      event.preventDefault();
      sendMessage(input, cityInput, messages, sendButton);
    });
  }

  document.addEventListener('DOMContentLoaded', initTravelChat);
}());

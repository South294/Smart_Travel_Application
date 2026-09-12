(function () {
  var API_BASE = window.SMART_TRAVEL_API_URL || 'http://localhost:8000';
  var sessionKey = 'smart_travel_chat_session';

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

  function renderRecommendations(container, recommendations) {
    if (!Array.isArray(recommendations) || recommendations.length === 0) return;
    var section = document.createElement('div');
    section.className = 'chat-recommendations';
    section.innerHTML = recommendations.map(function (item) {
      var image = item.image_url || 'https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=800&q=80';
      var checkout = 'checkout.html?title=' + encodeURIComponent(item.title) +
        '&price=' + encodeURIComponent(item.estimated_price || 0) +
        '&img=' + encodeURIComponent(image) + '&tourId=' + encodeURIComponent(item.tour_id);
      return '<article class="recommendation-card">' +
        '<img src="' + escapeHtml(image) + '" alt="' + escapeHtml(item.title) + '">' +
        '<div class="recommendation-content">' +
        '<span class="recommendation-location"><i class="bx bx-map-pin"></i> ' + escapeHtml(item.location) + '</span>' +
        '<h3>' + escapeHtml(item.title) + '</h3>' +
        '<p>' + escapeHtml(item.reason) + '</p>' +
        '<div class="recommendation-footer"><strong>' + formatCurrency(item.estimated_price) + '</strong>' +
        '<a class="btn btn-primary btn-small" href="' + checkout + '">Xem tour</a></div>' +
        '</div></article>';
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

  async function sendMessage(input, cityInput, messages, sendButton) {
    var text = input.value.trim();
    if (!text || sendButton.disabled) return;
    input.value = '';
    sendButton.disabled = true;
    addMessage(messages, text, 'user');
    var loading = addMessage(messages, 'Đang tìm hành trình phù hợp...', 'bot');
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
      renderRecommendations(messages, data.recommendations);
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

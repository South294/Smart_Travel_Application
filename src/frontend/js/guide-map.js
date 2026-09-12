(function() {
  var guideMap;
  var guideMarker;
  var accuracyCircle;
  var watchId;
  var defaultCenter = [16.0471, 108.2068];

  function setLocationStatus(message, isError) {
    var status = document.getElementById('guideLocationStatus');
    if (!status) return;
    status.className = 'guide-location-status' + (isError ? ' is-error' : '');
    status.innerHTML = '<i class="bx ' + (isError ? 'bx-error-circle' : 'bx-info-circle') + '"></i> ' + message;
  }

  function showLocationGate(show) {
    var gate = document.getElementById('guideLocationGate');
    if (gate) gate.style.display = show ? 'flex' : 'none';
  }

  function updateGuidePosition(position) {
    var latitude = position.coords.latitude;
    var longitude = position.coords.longitude;
    var accuracy = position.coords.accuracy;
    var location = [latitude, longitude];

    if (!guideMarker) {
      guideMarker = L.marker(location).addTo(guideMap).bindPopup('Vị trí hiện tại của bạn');
      guideMarker.openPopup();
      guideMap.setView(location, 15);
    } else {
      guideMarker.setLatLng(location);
    }

    if (!accuracyCircle) {
      accuracyCircle = L.circle(location, { radius: accuracy, color: '#0aa982', fillColor: '#0aa982', fillOpacity: 0.12 }).addTo(guideMap);
    } else {
      accuracyCircle.setLatLng(location).setRadius(accuracy);
    }

    showLocationGate(false);
    var mapEmpty = document.getElementById('guideMapEmpty');
    if (mapEmpty) mapEmpty.style.display = 'none';
    setLocationStatus('Đã bật định vị. Vị trí đang được cập nhật.', false);
  }

  function handleLocationError(error) {
    var message = 'Không thể lấy vị trí hiện tại.';
    if (error && error.code === 1) message = 'Bạn đã từ chối quyền định vị. Hãy cấp lại quyền trong trình duyệt để sử dụng bản đồ.';
    if (error && error.code === 2) message = 'Không xác định được vị trí. Hãy kiểm tra GPS hoặc kết nối mạng.';
    if (error && error.code === 3) message = 'Lấy vị trí quá lâu. Hãy thử bật định vị lại.';
    showLocationGate(true);
    setLocationStatus(message, true);
  }

  function requestGuideLocation() {
    if (!navigator.geolocation) {
      handleLocationError({ code: 2 });
      return;
    }
    setLocationStatus('Đang xin quyền và xác định vị trí...', false);
    navigator.geolocation.getCurrentPosition(updateGuidePosition, handleLocationError, {
      enableHighAccuracy: true,
      timeout: 15000,
      maximumAge: 30000
    });

    if (watchId === undefined) {
      watchId = navigator.geolocation.watchPosition(updateGuidePosition, handleLocationError, {
        enableHighAccuracy: true,
        timeout: 20000,
        maximumAge: 10000
      });
    }
  }

  function initGuideMap() {
    var mapElement = document.getElementById('guideLeafletMap');
    if (!mapElement || typeof L === 'undefined') return;

    guideMap = L.map(mapElement, { zoomControl: true }).setView(defaultCenter, 5);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(guideMap);

    var enableButton = document.getElementById('guideEnableLocation');
    if (enableButton) enableButton.addEventListener('click', requestGuideLocation);
    setLocationStatus('Chưa bật định vị. Vị trí của bạn chưa được chia sẻ.', false);
  }

  document.addEventListener('DOMContentLoaded', initGuideMap);
})();

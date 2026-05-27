var userLatLng = null;
var activeCategory = 'all';
var isLoggedIn = false;
var hasActiveBooking = false;
var locationRequired = false;
var hasLocationPermission = false;
var wasSkipped = false;
var selectedPlaceId = null;

var PLACES_DATA = [
    {
        id: 'ethnology-museum',
        name: "Bảo tàng Dân tộc học",
        category: "culture",
        lat: 21.0412,
        lng: 105.8007,
        rating: 4.7,
        reviews: 1800,
        address: "Nguyễn Văn Huyên, Cầu Giấy, Hà Nội",
        image: "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1d/Vietnam_Museum_of_Ethnology.jpg/640px-Vietnam_Museum_of_Ethnology.jpg",
        desc: "Không gian văn hóa 54 dân tộc, kiến trúc độc đáo",
        bestMonths: "Tháng 9 - 4",
        tip: "Nên ghé sáng sớm để tránh đông và nắng." 
    },
    {
        id: 'temple-literature',
        name: "Văn Miếu - Quốc Tử Giám",
        category: "culture",
        lat: 21.0294,
        lng: 105.8355,
        rating: 4.8,
        reviews: 4500,
        address: "58 Quốc Tử Giám, Đống Đa, Hà Nội",
        image: "https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Hanoi_Temple_of_Literature_%28cropped%29.jpg/640px-Hanoi_Temple_of_Literature_%28cropped%29.jpg",
        desc: "Trường đại học đầu tiên của Việt Nam",
        bestMonths: "Tháng 10 - 3",
        tip: "Nên mang theo máy ảnh, góc chụp rất đẹp." 
    },
    {
        id: 'thang-long-citadel',
        name: "Hoàng Thành Thăng Long",
        category: "culture",
        lat: 21.0358,
        lng: 105.8400,
        rating: 4.6,
        reviews: 3400,
        address: "19C Hoàng Diệu, Ba Đình, Hà Nội",
        image: "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Doan_Mon_Gate.jpg/640px-Doan_Mon_Gate.jpg",
        desc: "Di sản Văn hóa Thế giới UNESCO",
        bestMonths: "Tháng 9 - 2",
        tip: "Dành 2-3 giờ để khám phá trọn vẹn." 
    },
    {
        id: 'st-joseph-cathedral',
        name: "Nhà Thờ Lớn Hà Nội",
        category: "culture",
        lat: 21.0288,
        lng: 105.8490,
        rating: 4.5,
        reviews: 2100,
        address: "40 Nhà Chung, Hoàn Kiếm, Hà Nội",
        image: "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Cathedral_of_Hanoi.jpg/640px-Cathedral_of_Hanoi.jpg",
        desc: "Nhà thờ kiến trúc Gothic giữa lòng Hà Nội",
        bestMonths: "Tháng 11 - 2",
        tip: "Buổi tối lên đèn rất đẹp, thích hợp dạo bộ." 
    },
    {
        id: 'hoan-kiem-lake',
        name: "Hồ Hoàn Kiếm",
        category: "fun",
        lat: 21.0285,
        lng: 105.8542,
        rating: 4.9,
        reviews: 5200,
        address: "Q. Hoàn Kiếm, Hà Nội",
        image: "https://upload.wikimedia.org/wikipedia/commons/thumb/7/79/Thap_Rua.jpg/640px-Thap_Rua.jpg",
        desc: "Phố đi bộ cuối tuần, không gian thư giãn",
        bestMonths: "Tháng 9 - 4",
        tip: "Đi chiều tối để cảm nhận nhịp sống Hà Nội." 
    },
    {
        id: 'vinke-aquarium',
        name: "VinKE & Vinpearl Aquarium",
        category: "fun",
        lat: 21.0008,
        lng: 105.8179,
        rating: 4.6,
        reviews: 2600,
        address: "Time City, Hai Bà Trưng, Hà Nội",
        image: "https://images.unsplash.com/photo-1526336024174-e58f5cdd8e13?auto=format&fit=crop&w=900&q=80",
        desc: "Khu vui chơi trong nhà, thủy cung lớn",
        bestMonths: "Tháng 5 - 9",
        tip: "Phù hợp gia đình, tránh nắng nóng." 
    },
    {
        id: 'thu-le-park',
        name: "Công viên Thủ Lệ",
        category: "fun",
        lat: 21.0349,
        lng: 105.8108,
        rating: 4.4,
        reviews: 1900,
        address: "Bưởi, Ba Đình, Hà Nội",
        image: "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=900&q=80",
        desc: "Công viên xanh, vườn thú, khu vui chơi gia đình",
        bestMonths: "Tháng 9 - 4",
        tip: "Cuối tuần nên đi sớm để tránh đông." 
    },
    {
        id: 'old-quarter',
        name: "Phố cổ Hà Nội",
        category: "fun",
        lat: 21.0333,
        lng: 105.8500,
        rating: 4.7,
        reviews: 3100,
        address: "Q. Hoàn Kiếm, Hà Nội",
        image: "https://upload.wikimedia.org/wikipedia/commons/thumb/d/da/Old_Quarter_Street_Scene_-_Hanoi_-_Vietnam_%2848256301206%29.jpg/640px-Old_Quarter_Street_Scene_-_Hanoi_-_Vietnam_%2848256301206%29.jpg",
        desc: "Nhiều hoạt động vui chơi, ẩm thực, mua sắm",
        bestMonths: "Tháng 10 - 3",
        tip: "Buổi tối có phố đi bộ và chợ đêm." 
    },
    {
        id: 'cha-ca-la-vong',
        name: "Chả cá Lã Vọng",
        category: "food",
        lat: 21.0340,
        lng: 105.8490,
        rating: 4.4,
        reviews: 1500,
        address: "14 Chả Cá, Hoàn Kiếm, Hà Nội",
        image: "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/Cha_Ca_La_Vong.jpg/640px-Cha_Ca_La_Vong.jpg",
        desc: "Món chả cá đặc sản nổi tiếng nhất Hà Nội",
        bestMonths: "Tháng 10 - 2",
        tip: "Đi nhóm đông để thưởng thức trọn vẹn." 
    },
    {
        id: 'pho-thin',
        name: "Phở Thìn Bờ Hồ",
        category: "food",
        lat: 21.0290,
        lng: 105.8525,
        rating: 4.6,
        reviews: 1800,
        address: "61 Đinh Tiên Hoàng, Hoàn Kiếm, Hà Nội",
        image: "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Pho-Beef-Noodles-2008.jpg/640px-Pho-Beef-Noodles-2008.jpg",
        desc: "Phở bò truyền thống nổi tiếng Hà Nội",
        bestMonths: "Tháng 11 - 2",
        tip: "Buổi sáng sớm là ngon nhất." 
    },
    {
        id: 'bun-cha-huong-lien',
        name: "Bún chả Hương Liên",
        category: "food",
        lat: 21.0132,
        lng: 105.8523,
        rating: 4.5,
        reviews: 2400,
        address: "24 Lê Văn Hưu, Hai Bà Trưng, Hà Nội",
        image: "https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/Bun_cha_in_Hanoi.jpg/640px-Bun_cha_in_Hanoi.jpg",
        desc: "Quán Obama từng ghé thăm năm 2016",
        bestMonths: "Tháng 9 - 4",
        tip: "Nên đặt bàn trước giờ trưa." 
    },
    {
        id: 'banh-cuon-ba-hoanh',
        name: "Bánh cuốn Bà Hoành",
        category: "food",
        lat: 21.0352,
        lng: 105.8515,
        rating: 4.3,
        reviews: 980,
        address: "66 Tô Hiến Thành, Hai Bà Trưng, Hà Nội",
        image: "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Banh_cuon_Viet_Nam.jpg/640px-Banh_cuon_Viet_Nam.jpg",
        desc: "Bánh cuốn nóng truyền thống gia truyền",
        bestMonths: "Tháng 10 - 2",
        tip: "Hợp đi buổi sáng hoặc chiều mát." 
    }
];

var CATEGORY_LABELS = {
    food: 'Ăn uống',
    culture: 'Tham quan văn hóa',
    fun: 'Vui chơi'
};

var CATEGORY_COLORS = {
    food: '#f97316',
    culture: '#0ea5a4',
    fun: '#2563eb'
};

function calculateDistance(lat1, lng1, lat2, lng2) {
    var R = 6371;
    var dLat = (lat2 - lat1) * Math.PI / 180;
    var dLng = (lng2 - lng1) * Math.PI / 180;
    var a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
        Math.sin(dLng / 2) * Math.sin(dLng / 2);
    var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

function formatDistance(km) {
    if (km < 1) return Math.round(km * 1000) + 'm';
    return km.toFixed(1) + 'km';
}

function initMapPage() {
    isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
    hasActiveBooking = localStorage.getItem('hasActiveBooking') === 'true';
    locationRequired = isLoggedIn || hasActiveBooking;

    var btnAllow = document.getElementById('btnAllowLocation');
    var btnSkip = document.getElementById('btnSkipLocation');

    updateGateContent();
    updateSkipVisibility();

    if (btnAllow) {
        btnAllow.addEventListener('click', function() {
            requestGeolocation();
        });
    }

    if (btnSkip) {
        btnSkip.addEventListener('click', function() {
            wasSkipped = true;
            updateLocationStatus('Bạn đang xem gợi ý nổi bật');
            hideLocationGate();
            addAllPlaces();
        });
    }

    setupCategoryTabs();
    setupSearch();
    if (locationRequired) {
        showPermissionRequiredMessage();
        updateLocationStatus('Cần bật định vị để tiếp tục');
    } else {
        updateLocationStatus('Bạn có thể bật định vị hoặc bỏ qua');
    }
    addAllPlaces();
}

function requestGeolocation() {
    if (locationRequired && !navigator.geolocation) {
        updateLocationStatus('Thiết bị không hỗ trợ định vị');
        showPermissionRequiredMessage();
        return;
    }

    updateLocationStatus('Đang xác định vị trí...');

    if (!navigator.geolocation) {
        userLatLng = [21.0285, 105.8542];
        updateLocationStatus('Trình duyệt không hỗ trợ. Gợi ý theo Hà Nội');
        addAllPlaces();
        hideLocationGate();
        return;
    }

    navigator.geolocation.getCurrentPosition(
        function(position) {
            userLatLng = [position.coords.latitude, position.coords.longitude];
            hasLocationPermission = true;
            updateLocationStatus('Đang hiển thị gợi ý quanh bạn');
            addAllPlaces();
            hideLocationGate();
        },
        function() {
            userLatLng = [21.0285, 105.8542];
            if (locationRequired) {
                updateLocationStatus('Cần bật định vị để tiếp tục');
                showPermissionRequiredMessage();
                return;
            }
            updateLocationStatus('Không thể xác định. Gợi ý theo Hà Nội');
            addAllPlaces();
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 }
    );
}

function updateLocationStatus(text) {
    var el = document.getElementById('locationStatus');
    if (el) el.textContent = text;
}

function hideLocationGate() {
    var gate = document.getElementById('locationGate');
    if (gate) gate.style.display = 'none';
}

function showPermissionRequiredMessage() {
    var gate = document.getElementById('locationGate');
    if (!gate) return;
    gate.style.display = 'flex';
}

function updateGateContent() {
    var title = document.getElementById('gateTitle');
    var desc = document.getElementById('gateDesc');
    if (!title || !desc) return;

    if (locationRequired) {
        title.textContent = 'Bắt buộc bật định vị để tiếp tục';
        desc.textContent = 'Tài khoản đang đăng nhập hoặc có lịch trình đang đặt cần định vị để gợi ý chính xác.';
    } else {
        title.textContent = 'Cho phép dùng định vị';
        desc.textContent = 'Để gợi ý điểm ăn uống, tham quan văn hóa, vui chơi quanh bạn.';
    }
}

function updateSkipVisibility() {
    var btnSkip = document.getElementById('btnSkipLocation');
    if (!btnSkip) return;
    btnSkip.style.display = locationRequired ? 'none' : 'inline-flex';
}

function addAllPlaces() {
    var container = document.getElementById('placesList');
    if (container) container.innerHTML = '';

    var filtered = PLACES_DATA.filter(function(place) {
        return activeCategory === 'all' || place.category === activeCategory;
    });

    var searchTerm = '';
    var searchInput = document.getElementById('mapSearchInput');
    if (searchInput) searchTerm = searchInput.value.trim().toLowerCase();
    if (searchTerm) {
        filtered = filtered.filter(function(place) {
            return place.name.toLowerCase().indexOf(searchTerm) !== -1 ||
                   place.address.toLowerCase().indexOf(searchTerm) !== -1 ||
                   place.desc.toLowerCase().indexOf(searchTerm) !== -1;
        });
    }

    if (userLatLng) {
        filtered.sort(function(a, b) {
            var distA = calculateDistance(userLatLng[0], userLatLng[1], a.lat, a.lng);
            var distB = calculateDistance(userLatLng[0], userLatLng[1], b.lat, b.lng);
            return distA - distB;
        });
    }

    if (!userLatLng && !locationRequired && !wasSkipped) {
        updateLocationStatus('Đang chờ bạn bật định vị hoặc bỏ qua');
    }

    filtered.forEach(function(place) {
        addPlaceRow(place);
    });

    if (filtered.length === 0 && container) {
        container.innerHTML = '<div class="empty-places"><i class="bx bx-search-alt"></i><p>Không tìm thấy địa điểm nào</p></div>';
    }

    if (!selectedPlaceId && filtered.length > 0) {
        selectPlace(filtered[0]);
    }

    updateSelectedRow();
}

function addPlaceRow(place) {
    var container = document.getElementById('placesList');
    if (!container) return;

    var catColor = CATEGORY_COLORS[place.category] || '#059669';
    var catLabel = CATEGORY_LABELS[place.category] || place.category;
    var distanceText = '';
    if (userLatLng) {
        var km = calculateDistance(userLatLng[0], userLatLng[1], place.lat, place.lng);
        distanceText = '<span class="place-distance"><i class="bx bx-walk"></i> ' + formatDistance(km) + '</span>';
    }

    var html = '<button class="place-row" data-place-id="' + place.id + '">' +
        '<img src="' + place.image + '" alt="' + place.name + '" class="place-row-thumb">' +
        '<div class="place-row-body">' +
        '<div class="place-row-meta">' +
        '<span class="place-tag" style="background:' + catColor + '; color: #fff;">' + catLabel + '</span>' +
        '<span class="place-row-rating"><i class="bx bxs-star"></i> ' + place.rating + '</span>' +
        '</div>' +
        '<h4 class="font-bold">' + place.name + '</h4>' +
        '<p class="text-muted text-sm">' + place.address + '</p>' +
        '</div>' +
        '<div class="place-row-foot">' + distanceText + '</div>' +
        '</button>';

    container.insertAdjacentHTML('beforeend', html);

    var row = container.lastElementChild;
    row.addEventListener('click', function() {
        selectPlace(place);
    });
}

function setupCategoryTabs() {
    var tabs = document.querySelectorAll('#categoryTabs .map-tab');
    tabs.forEach(function(tab) {
        tab.addEventListener('click', function() {
            tabs.forEach(function(t) { t.classList.remove('active'); });
            this.classList.add('active');
            activeCategory = this.getAttribute('data-category');
            selectedPlaceId = null;
            addAllPlaces();
        });
    });
}

function setupSearch() {
    var input = document.getElementById('mapSearchInput');
    if (!input) return;

    var debounceTimer;
    input.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(function() {
            selectedPlaceId = null;
            addAllPlaces();
        }, 300);
    });
}

function openGoogleMaps(place) {
    if (!place || !place.lat || !place.lng) return;

    var openDirections = function(originLatLng) {
        var baseUrl = 'https://www.google.com/maps/dir/?api=1';
        var destination = place.lat + ',' + place.lng;
        var origin = originLatLng ? (originLatLng[0] + ',' + originLatLng[1]) : '';
        var url = baseUrl +
            '&destination=' + encodeURIComponent(destination) +
            (origin ? '&origin=' + encodeURIComponent(origin) : '') +
            '&travelmode=driving';
        window.open(url, '_blank');
    };

    if (userLatLng && userLatLng.length === 2) {
        openDirections(userLatLng);
        return;
    }

    if (!navigator.geolocation) {
        openDirections(null);
        return;
    }

    navigator.geolocation.getCurrentPosition(
        function(position) {
            var originLatLng = [position.coords.latitude, position.coords.longitude];
            openDirections(originLatLng);
        },
        function() {
            openDirections(null);
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 }
    );
}

function selectPlace(place) {
    if (!place || !place.id) return;
    selectedPlaceId = place.id;
    var detail = document.getElementById('placeDetail');
    if (!detail) return;

    var bestMonths = place.bestMonths || 'Quanh năm';
    var tip = place.tip || 'Nên đi vào buổi sáng để tránh đông.';

    detail.innerHTML = '<div class="detail-cover">' +
        '<img src="' + place.image + '" alt="' + place.name + '">' +
        '<span class="detail-badge">' + (CATEGORY_LABELS[place.category] || place.category) + '</span>' +
        '</div>' +
        '<div class="detail-body">' +
        '<h2 class="font-bold">' + place.name + '</h2>' +
        '<p class="text-muted"><i class="bx bx-map"></i> ' + place.address + '</p>' +
        '<p class="detail-desc">' + place.desc + '</p>' +
        '<div class="detail-info">' +
        '<div>' +
        '<p class="detail-label">Thời điểm nên đi</p>' +
        '<p class="detail-value">' + bestMonths + '</p>' +
        '</div>' +
        '<div>' +
        '<p class="detail-label">Lời khuyên</p>' +
        '<p class="detail-value">' + tip + '</p>' +
        '</div>' +
        '</div>' +
        '<div class="detail-actions">' +
        '<button class="btn btn-primary" id="btnOpenMap">Định hướng trên Google Maps</button>' +
        '</div>' +
        '</div>';

    var btn = document.getElementById('btnOpenMap');
    if (btn) {
        btn.addEventListener('click', function() {
            openGoogleMaps(place);
        });
    }

    updateSelectedRow();
}

function updateSelectedRow() {
    var rows = document.querySelectorAll('.place-row');
    rows.forEach(function(row) {
        var id = row.getAttribute('data-place-id');
        if (id === selectedPlaceId) {
            row.classList.add('is-active');
        } else {
            row.classList.remove('is-active');
        }
    });
}

document.addEventListener('DOMContentLoaded', initMapPage);

document.addEventListener('DOMContentLoaded', function() {
    var map = L.map('map').setView([21.0285, 105.8542], 14);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

    var markers = L.markerClusterGroup({
        maxClusterRadius: 50,
        disableClusteringAtZoom: 16
    });

    var locations = [
        { lat: 21.0285, lng: 105.8542, name: "Hồ Hoàn Kiếm", desc: "Điểm tham quan", icon: "bx-camera" },
        { lat: 21.0333, lng: 105.8500, name: "Phố cổ Hà Nội", desc: "Khu vực sầm uất", icon: "bx-walk" },
        { lat: 21.0294, lng: 105.8355, name: "Văn Miếu Quốc Tử Giám", desc: "Di tích lịch sử", icon: "bx-book" },
        { lat: 21.0369, lng: 105.8342, name: "Lăng Chủ tịch Hồ Chí Minh", desc: "Điểm tham quan", icon: "bx-camera" },
        { lat: 21.0560, lng: 105.8190, name: "Hồ Tây", desc: "Điểm thư giãn", icon: "bx-water" }
    ];

    var leafMarkers = {};

    locations.forEach(function(loc) {
        var customIcon = L.divIcon({
            html: '<i class="bx ' + loc.icon + '"></i>',
            className: 'custom-marker',
            iconSize: [40, 40]
        });

        var marker = L.marker([loc.lat, loc.lng], { icon: customIcon });

        marker.bindPopup(
            '<h3>' + loc.name + '</h3>' +
            '<p>' + loc.desc + '</p>'
        );

        markers.addLayer(marker);
        leafMarkers[loc.lat + ',' + loc.lng] = marker;
    });

    map.addLayer(markers);

    var places = document.querySelectorAll('.place-item');

    places.forEach(function(place) {
        place.addEventListener('click', function() {
            places.forEach(function(p) { p.classList.remove('place-active'); });
            this.classList.add('place-active');

            var lat = parseFloat(this.getAttribute('data-lat'));
            var lng = parseFloat(this.getAttribute('data-lng'));

            map.flyTo([lat, lng], 16, {
                animate: true,
                duration: 1.5
            });

            var key = lat + ',' + lng;
            if (leafMarkers[key]) {
                setTimeout(function() {
                    leafMarkers[key].openPopup();
                }, 1500);
            }
        });
    });

    var mapTabs = document.querySelectorAll('.map-tab');

    mapTabs.forEach(function(tab) {
        tab.addEventListener('click', function() {
            mapTabs.forEach(function(t) { t.classList.remove('active'); });
            this.classList.add('active');
        });
    });
});

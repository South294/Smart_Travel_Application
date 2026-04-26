document.addEventListener('DOMContentLoaded', function() {
    var map = L.map('map').setView([10.7766, 106.6984], 14);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

    var markers = L.markerClusterGroup({
        maxClusterRadius: 50,
        disableClusteringAtZoom: 16
    });

    var locations = [
        { lat: 10.7766, lng: 106.6984, name: "Nhà hàng Phố Xưa", desc: "Ẩm thực truyền thống", icon: "bx-restaurant" },
        { lat: 10.7735, lng: 106.7011, name: "Khách sạn Biển Đảo", desc: "Khách sạn 4 sao", icon: "bx-hotel" },
        { lat: 10.7800, lng: 106.6950, name: "Nhà thờ Đức Bà", desc: "Điểm tham quan", icon: "bx-camera" },
        { lat: 10.7745, lng: 106.7031, name: "Phố đi bộ Nguyễn Huệ", desc: "Điểm tham quan", icon: "bx-walk" },
        { lat: 10.7780, lng: 106.6900, name: "Nhà hàng chay Loving Hut", desc: "Ẩm thực chay", icon: "bx-restaurant" }
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

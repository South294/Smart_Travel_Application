document.addEventListener('DOMContentLoaded', () => {
    const map = L.map('map').setView([10.7766, 106.6984], 14);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    const markers = L.markerClusterGroup({
        maxClusterRadius: 50,
        disableClusteringAtZoom: 16
    });

    const locations = [
        { id: 1, lat: 10.7766, lng: 106.6984, name: "Nhà hàng Phố Xưa", desc: "Dinh Độc Lập", icon: "bx-restaurant" },
        { id: 2, lat: 10.7735, lng: 106.7011, name: "Khách sạn Biển Đảo", desc: "Chợ Bến Thành", icon: "bx-hotel" },
        { id: 3, lat: 10.7800, lng: 106.6950, name: "Nhà thờ Đức Bà", desc: "Điểm tham quan", icon: "bx-camera" },
        { id: 4, lat: 10.7745, lng: 106.7031, name: "Phố đi bộ Nguyễn Huệ", desc: "Điểm tham quan", icon: "bx-walk" },
        { id: 5, lat: 10.7780, lng: 106.6900, name: "Nhà hàng chay", desc: "Quận 3", icon: "bx-restaurant" }
    ];

    const leafMarkers = {};

    locations.forEach(loc => {
        const customIcon = L.divIcon({
            html: `<i class='bx ${loc.icon}'></i>`,
            className: 'custom-marker',
            iconSize: [40, 40]
        });

        const marker = L.marker([loc.lat, loc.lng], { icon: customIcon });
        
        marker.bindPopup(`
            <h3>${loc.name}</h3>
            <p>${loc.desc}</p>
        `);
        
        markers.addLayer(marker);
        leafMarkers[`${loc.lat},${loc.lng}`] = marker;
    });

    map.addLayer(markers);

    const places = document.querySelectorAll('.place-item');
    
    places.forEach(place => {
        place.addEventListener('click', function() {
            places.forEach(p => p.classList.remove('place-active'));
            this.classList.add('place-active');
            
            const lat = parseFloat(this.getAttribute('data-lat'));
            const lng = parseFloat(this.getAttribute('data-lng'));
            
            map.flyTo([lat, lng], 16, {
                animate: true,
                duration: 1.5
            });

            const key = `${lat},${lng}`;
            if (leafMarkers[key]) {
                setTimeout(() => {
                    leafMarkers[key].openPopup();
                }, 1500);
            }
        });
    });

    const subTabs = document.querySelectorAll('.map-sidebar .category-tabs .badge');
    
    subTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            subTabs.forEach(t => t.classList.remove('badge-primary', 'active-tab'));
            this.classList.add('badge-primary', 'active-tab');
        });
    });
});

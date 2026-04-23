document.addEventListener('DOMContentLoaded', () => {
    const places = document.querySelectorAll('.place-item');
    
    places.forEach(place => {
        place.addEventListener('click', function() {
            places.forEach(p => p.classList.remove('place-active'));
            this.classList.add('place-active');
            
            const locationName = this.querySelector('h4')?.innerText || 'Không rõ';
            console.log(`[Google Maps API] Chuẩn bị di chuyển bản đồ tới: ${locationName}`);
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

// Map Javascript

document.addEventListener('DOMContentLoaded', () => {
    // Handling Place clicks
    const places = document.querySelectorAll('.place-item');
    places.forEach(place => {
        place.addEventListener('click', function() {
            // Remove active style from all
            places.forEach(p => p.style.backgroundColor = 'transparent');
            // Add to current
            this.style.backgroundColor = 'var(--primary-light)';
            
            // Here you would typically center the map instance to the place's coordinates.
            console.log('Centering map to selected location.');
        });
    });

    // Sub tabs
    const subTabs = document.querySelectorAll('.map-sidebar .category-tabs .badge');
    subTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            subTabs.forEach(t => {
                t.classList.remove('badge-primary');
                t.style.background = 'var(--bg-color)';
                t.style.color = 'var(--text-muted)';
            });
            this.classList.add('badge-primary');
            this.style.background = 'var(--primary-light)';
            this.style.color = 'var(--primary-color)';
        });
    });
});

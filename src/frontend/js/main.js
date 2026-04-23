document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initPaymentOptions();
});

function initNavigation() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        link.classList.remove('active');
        
        const isHomePage = (currentPath.endsWith('/') || currentPath.endsWith('index.html')) && href === 'index.html';
        const isCurrentPage = currentPath.endsWith(href) && href !== 'index.html';
        
        if (isHomePage || isCurrentPage) {
            link.classList.add('active');
        }
    });
}

function initPaymentOptions() {
    const paymentOptions = document.querySelectorAll('.payment-option');
    
    if (paymentOptions.length === 0) return;

    paymentOptions.forEach(option => {
        option.addEventListener('click', function() {
            paymentOptions.forEach(opt => opt.classList.remove('selected'));
            this.classList.add('selected');
            
            const radio = this.querySelector('input[type="radio"]');
            if (radio) {
                radio.checked = true;
            }
        });
    });
}

// Main Javascript file for Smart Travel App

document.addEventListener('DOMContentLoaded', () => {
    // 1. Navbar active state based on current URL
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    // Very basic active state setter
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (currentPath.endsWith(href) && href !== 'index.html') {
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            link.classList.add('active');
        } else if (currentPath.endsWith('/') && href === 'index.html') {
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            link.classList.add('active');
        }
    });

    // 2. Buttons interaction feedback
    const buttons = document.querySelectorAll('.btn-primary');
    buttons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            // Ripple effect or micro-animation logic can be added here
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = 'translateY(-2px)';
            }, 100);
        });
    });

    // 3. Payment Method Selection (Checkout Page)
    const paymentOptions = document.querySelectorAll('.payment-option');
    if (paymentOptions.length > 0) {
        paymentOptions.forEach(option => {
            option.addEventListener('click', function() {
                // Remove selected from all
                paymentOptions.forEach(opt => opt.classList.remove('selected'));
                // Add selected to clicked
                this.classList.add('selected');
                const radio = this.querySelector('input[type="radio"]');
                if (radio) radio.checked = true;
            });
        });
    }
});

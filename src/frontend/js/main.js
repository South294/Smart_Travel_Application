document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initPaymentOptions();
    initAuthState();
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

function initAuthState() {
    const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
    const navActions = document.querySelectorAll('.nav-actions');
    
    navActions.forEach(container => {

        const hasSearch = container.innerHTML.includes('bx-search');
        
        if (isLoggedIn) {
            container.innerHTML = (hasSearch ? `<button class="btn btn-icon"><i class='bx bx-search'></i></button>` : '') + `
                <div class="user-avatar" title="Trang cá nhân" style="width: 40px; height: 40px; background-color: var(--primary-light); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: var(--primary-color); font-weight: bold; cursor: pointer; border: 2px solid var(--primary-color);" onclick="window.location.href='profile.html'">ST</div>
            `;
        } else {
            container.innerHTML = (hasSearch ? `<button class="btn btn-icon"><i class='bx bx-search'></i></button>` : '') + `
                <a href="auth.html" class="btn btn-outline">Đăng nhập</a>
                <a href="auth.html" class="btn btn-primary">Đăng ký</a>
            `;
        }
    });
}

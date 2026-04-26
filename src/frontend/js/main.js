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
                <div class="user-avatar" title="Nhấn để đăng xuất" style="width: 40px; height: 40px; background-color: var(--primary-light); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: var(--primary-color); font-weight: bold; cursor: pointer; border: 2px solid var(--primary-color);" onclick="toggleLogin()">ST</div>
            `;
        } else {
            container.innerHTML = (hasSearch ? `<button class="btn btn-icon"><i class='bx bx-search'></i></button>` : '') + `
                <a href="auth.html" class="btn btn-outline">Đăng nhập</a>
                <a href="auth.html" class="btn btn-primary">Đăng ký</a>
            `;
        }
    });

    if (!document.getElementById('test-login-toggle')) {
        const btn = document.createElement('button');
        btn.id = 'test-login-toggle';
        btn.textContent = isLoggedIn ? 'Đang Đăng Nhập (Bấm để Đăng Xuất)' : 'Đang Đăng Xuất (Bấm để Đăng Nhập)';
        btn.style.position = 'fixed';
        btn.style.bottom = '20px';
        btn.style.right = '20px';
        btn.style.zIndex = '9999';
        btn.style.padding = '12px 20px';
        btn.style.background = isLoggedIn ? '#dc3545' : '#10b981';
        btn.style.color = 'white';
        btn.style.border = 'none';
        btn.style.borderRadius = '30px';
        btn.style.fontWeight = 'bold';
        btn.style.cursor = 'pointer';
        btn.style.boxShadow = '0 4px 15px rgba(0,0,0,0.3)';
        
        btn.onclick = toggleLogin;
        document.body.appendChild(btn);
    }
}

function toggleLogin() {
    const current = localStorage.getItem('isLoggedIn') === 'true';
    localStorage.setItem('isLoggedIn', !current);
    location.reload();
}

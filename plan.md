# Smart Travel Project - Optimization Roadmap

## Priority 1: Guide Driver Separate Page & Admin Features

### Current State Analysis
- `guides.html` currently shows general guide list (approved only) and a "become guide" register form
- Backend has guide routes: apply, approve/reject by admin, get my profile, dashboard, requests
- Missing: Admin assigning tours to guides, guide stats showing tour assignments

### Required Changes

#### 1.1 Backend Enhancements (`src/backend/app/routers/guides.py`)
- Add endpoint: `GET /api/admin/guides` - list all guides with full info (for admin)
- Add endpoint: `PATCH /api/guides/{id}/assign-tour` - assign a tour to a guide
- Add endpoint: `GET /api/admin/tours/unassigned` - list tours not assigned to any guide
- Enhance `guide_dashboard` to show assigned tours and booking stats
- Add guide assignment tracking in `bookings` collection or new `guide_assignments` collection

#### 1.2 Frontend - New Standalone Guide Page
- Create `guide.html` - trang hướng dẫn viên riêng lẻ, tương tự cấu trúc admin/index.html
  - Có navigation riêng, hero section, danh sách HDV nổi bật
  - Section "Thuê HDV" với modal form
  - Phân tách hoàn toàn khỏi `guides.html` (trong khi `guides.html` dùng cho đăng ký HDV)
- Cập nhật `index.html` thêm link vào `guide.html`
- Cập nhật `guides.html` tập trung vào form đăng ký become guide

#### 1.3 Frontend - JS Updates
- `js/main.js` - add routing giữa guide.html và guides.html
- `js/tours.js` - integrate với guide assignment cho guide.html
- `js/pages/guide.css` - CSS riêng cho pageguide.html

#### 1.4 Frontend - Navigation Updates
- `index.html`: Thêm link nav đến `guide.html` (hiển thị "HĐV riêng")
- `guides.html`: Tập trung vào form đăng ký, có link đến `guide-register.html`
- `guide-dashboard.html`: Giữ nguyên cho hướng dẫn viên đã đăng nhập

#### 1.4 Database Considerations
- Ensure `guides` collection has: `is_active`, `specializations`, `languages`, `rating`
- Add `guide_assignments` collection or extend `bookings` with `guide_id` field
- Create indexes on `guides.status`, `guides.user_id`, `guides.areas`

---

## Priority 2: Security Optimization

### Current Vulnerabilities
- Deprecation warning: `on_event` used instead of `lifespan`
- CORS allows localhost:5500, 5501, 127.0.0.1 - should restrict in production
- No rate limiting on auth endpoints
- Passwords stored with bcrypt but no complexity policy
- JWT secret is hardcoded in config (`9a3f2d8c7b6a5e4d3c2b1a0f9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0`)
- No input validation beyond pydantic basics
- No HTTPS enforcement
- No authentication on data exposure endpoints

### Security Fixes

#### 2.1 Backend Security (`src/backend/app/core/security.py`)
- Replace `on_event` with `lifespan` context manager in `main.py`
- Move `SECRET_KEY` to environment variable
- Add rate limiting (using slowapi or manual tracking)
- Add password complexity validation

#### 2.2 CORS Configuration
- Restrict to specific origins in production
- Add `allow_methods` and `allow_headers` more selectively

#### 2.3 Error Handling
- Generic error messages for production (don't expose stack traces)
- Add request validation error handlers

#### 2.4 Frontend Security
- Add CSRF tokens for forms
- Secure API call patterns
- Store JWT securely in httpOnly cookies or localStorage with proper handling

---

## Priority 3: Code Quality & Bug Fixes

### 3.1 Deprecation Fix
- Replace `@app.on_event("startup")` and `@app.on_event("shutdown")` with FastAPI `lifespan` handler
- Move MongoDB index creation to lifespan

### 3.2 Helper Functions Optimization
- `serialize_guide` should include more fields consistently
- Add proper error handling for ObjectId validation
- Add connection error handling for MongoDB

### 3.3 API Response Consistency
- Standardize response format across all endpoints
- Add proper `response_model` to all routes
- Add summary/description to router tags

---

## Priority 4: Data & Seed Improvements

### 4.1 Seed Database Enhancement
- `seed_db.py` should create guides with proper data
- Create sample bookings with guide assignments
- Add voucher codes and test data

### 4.2 Demo Account Expansion
- Add more test users with different roles
- Create test guides with various specializations

---

## Execution Timeline

### Week 1: Foundation & Security
- [ ] Fix DeprecationWarning: implement `lifespan` in `main.py`
- [ ] Move SECRET_KEY to `.env` environment variable
- [ ] Create `lifespan` context manager for MongoDB connection and index creation
- [ ] Basic security headers middleware

### Week 2: Guide System Enhancement
- [ ] Add admin endpoints for guide management
- [ ] Add tour assignment endpoint
- [ ] Create `guide.html` - trang hướng dẫn viên riêng lẻ (dựng như admin page)
- [ ] Cập nhật navigation: index.html link vào guide.html
- [ ] Update `guides.html` tập trung vào form đăng ký become guide
- [ ] Tạo `js/pages/guide.css` cho pageguide.html mới

### Week 3: Frontend Integration
- [ ] Update `guide-dashboard.html` với dữ liệu thật
- [ ] Add JS đến `js/tours.js` cho guide-integration cho guide.html
- [ ] Tạo API service layer cho guide operations cho guide.html
- [ ] Cập nhật navigation và routing giữa guide.html, guides.html, guide-dashboard.html

### Week 4: Testing & polish
- [ ] Manual test all guide flows
- [ ] Security testing
- [ ] Cross-page navigation verification
- [ ] Bug fixes and edge case handling

### Week 5: Deployment Preparation
- [ ] Final `.env` configuration
- [ ] Production CORS settings
- [ ] Performance optimization
- [ ] Documentation update
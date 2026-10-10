var SmartTravelGuide = (function() {
  function renderGuideBadge(status) {
    if (status === 'approved') return '<span class="badge badge-success">Đã xác minh</span>';
    if (status === 'pending') return '<span class="badge badge-warning">Đang chờ duyệt</span>';
    if (status === 'rejected') return '<span class="badge badge-danger">Đã từ chối</span>';
    return '<span class="badge badge-secondary">Chưa đăng ký</span>';
  }

  return {
    renderGuideBadge: renderGuideBadge
  };
})();

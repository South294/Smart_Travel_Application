var SmartTravelCheckout = (function() {
  function formatCurrency(amount) {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(amount || 0);
  }

  function generateOrderCode() {
    var random = Math.floor(100000 + Math.random() * 900000);
    return 'ST-' + random;
  }

  return {
    formatCurrency: formatCurrency,
    generateOrderCode: generateOrderCode
  };
})();

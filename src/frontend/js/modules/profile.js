var SmartTravelProfile = (function() {
  function initUploadAreas() {
    var areas = document.querySelectorAll('.upload-area');
    if (!areas || areas.length === 0) return;

    areas.forEach(function(area) {
      var fileInput = area.querySelector('input[type="file"]');
      var hiddenInput = area.querySelector('input[type="hidden"]');
      var previewBox = area.querySelector('.upload-preview-box');
      var previewImg = area.querySelector('.upload-preview');
      var titleEl = area.querySelector('p');
      var iconEl = area.querySelector('i');

      if (!fileInput) return;

      area.addEventListener('click', function(e) {
        if (e.target !== fileInput && !e.target.closest('.btn-remove-preview')) {
          fileInput.click();
        }
      });

      fileInput.addEventListener('click', function(e) {
        e.stopPropagation();
      });

      ['dragenter', 'dragover'].forEach(function(eventName) {
        area.addEventListener(eventName, function(e) {
          e.preventDefault();
          e.stopPropagation();
          area.style.borderColor = 'var(--primary-color, #0aa982)';
          area.style.background = 'rgba(10, 169, 130, 0.08)';
        });
      });

      ['dragleave', 'drop'].forEach(function(eventName) {
        area.addEventListener(eventName, function(e) {
          e.preventDefault();
          e.stopPropagation();
          if (!area.classList.contains('has-file')) {
            area.style.borderColor = '';
            area.style.background = '';
          }
        });
      });

      area.addEventListener('drop', function(e) {
        var dt = e.dataTransfer;
        if (dt && dt.files && dt.files.length > 0) {
          processUploadedImage(dt.files[0], area, hiddenInput, previewBox, previewImg, titleEl, iconEl);
        }
      });

      fileInput.addEventListener('change', function() {
        if (!fileInput.files || fileInput.files.length === 0) return;
        processUploadedImage(fileInput.files[0], area, hiddenInput, previewBox, previewImg, titleEl, iconEl);
      });
    });

    initAvatarUpload();
  }

  function processUploadedImage(file, area, hiddenInput, previewBox, previewImg, titleEl, iconEl) {
    if (!file.type.match(/^image\//)) {
      showToast('Vui lòng chọn tệp hình ảnh hợp lệ (JPG, PNG, WebP)', 'error');
      return;
    }
    if (file.size > 8 * 1024 * 1024) {
      showToast('Kích thước ảnh không được vượt quá 8MB', 'error');
      return;
    }

    var reader = new FileReader();
    reader.onload = function(evt) {
      var base64Data = evt.target.result;
      if (hiddenInput) hiddenInput.value = base64Data;
      if (previewImg) previewImg.src = base64Data;
      if (previewBox) previewBox.style.display = 'block';
      area.classList.add('has-file');
      area.style.borderColor = '#10b981';
      area.style.background = 'rgba(16, 185, 129, 0.04)';
      if (titleEl) titleEl.textContent = file.name;
      if (iconEl) iconEl.className = 'bx bx-check-circle text-success';
      showToast('Tải ảnh thành công: ' + file.name, 'success');
    };
    reader.readAsDataURL(file);
  }

  function initAvatarUpload() {
    var avatarInput = document.getElementById('avatar-file-input');
    var avatarImg = document.querySelector('.profile-avatar-img, .profile-avatar');
    if (!avatarInput) return;

    avatarInput.addEventListener('change', async function() {
      if (!this.files || !this.files[0]) return;
      var file = this.files[0];
      if (!file.type.match(/^image\//)) {
        showToast('Vui lòng chọn file ảnh hợp lệ', 'error');
        return;
      }
      var reader = new FileReader();
      reader.onload = async function(e) {
        var base64 = e.target.result;
        if (avatarImg) {
          if (avatarImg.tagName === 'IMG') {
            avatarImg.src = base64;
          } else {
            avatarImg.style.backgroundImage = 'url(' + base64 + ')';
            avatarImg.style.backgroundSize = 'cover';
          }
        }
        try {
          var res = await fetchApi('/api/users/me', {
            method: 'PUT',
            body: JSON.stringify({ avatar_url: base64 })
          });
          if (res.ok) {
            showToast('Cập nhật ảnh đại diện thành công!', 'success');
            localStorage.removeItem('userProfile');
          }
        } catch(err) {
          showToast('Không thể lưu ảnh đại diện lên máy chủ', 'error');
        }
      };
      reader.readAsDataURL(file);
    });
  }

  return {
    initUploadAreas: initUploadAreas,
    processUploadedImage: processUploadedImage
  };
})();

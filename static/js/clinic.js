/* ============================================
   CLINIC DASHBOARD - JavaScript Module
   Modern AJAX/Fetch Implementation
   ============================================ */

/**
 * Clinic API - JavaScript Utility Module
 * Handles AJAX requests, form submissions, toasts, and UI interactions
 */
const ClinicAPI = (function() {
  'use strict';

  // ============================================
  // CONFIGURATION
  // ============================================
  const config = {
    csrfToken: document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
    loadingDelay: 300,
    toastDuration: 4000,
    confirmTitle: 'Xác nhận',
    confirmMessage: 'Bạn có chắc chắn muốn thực hiện hành động này?',
  };

  // ============================================
  // CSRF TOKEN HELPER
  // ============================================
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  // ============================================
  // TOAST NOTIFICATIONS
  // ============================================
  let toastContainer = null;

  function createToastContainer() {
    if (!toastContainer) {
      toastContainer = document.createElement('div');
      toastContainer.className = 'toast-container';
      toastContainer.setAttribute('aria-live', 'polite');
      toastContainer.setAttribute('aria-atomic', 'true');
      document.body.appendChild(toastContainer);
    }
    return toastContainer;
  }

  function showToast(type, title, message, duration = config.toastDuration) {
    const container = createToastContainer();
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');

    const icons = {
      success: 'fa-check-circle',
      error: 'fa-exclamation-circle',
      warning: 'fa-exclamation-triangle',
      info: 'fa-info-circle'
    };

    toast.innerHTML = `
      <div class="toast-icon">
        <i class="fas ${icons[type] || icons.info}"></i>
      </div>
      <div class="toast-content">
        <div class="toast-title">${title}</div>
        ${message ? `<div class="toast-message">${message}</div>` : ''}
      </div>
      <button type="button" class="toast-close" aria-label="Đóng">
        <i class="fas fa-times"></i>
      </button>
    `;

    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => removeToast(toast));

    container.appendChild(toast);

    // Auto remove
    if (duration > 0) {
      setTimeout(() => removeToast(toast), duration);
    }

    return toast;
  }

  function removeToast(toast) {
    toast.style.animation = 'slideInRight 0.3s ease-out reverse';
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    }, 300);
  }

  // Convenience methods
  const toast = {
    success: (title, message) => showToast('success', title, message),
    error: (title, message) => showToast('error', title, message),
    warning: (title, message) => showToast('warning', title, message),
    info: (title, message) => showToast('info', title, message)
  };

  // ============================================
  // ALERT NOTIFICATIONS
  // ============================================
  function showAlert(type, title, message, dismissible = true) {
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.setAttribute('role', 'alert');

    const icons = {
      success: 'fa-check-circle',
      error: 'fa-exclamation-circle',
      warning: 'fa-exclamation-triangle',
      info: 'fa-info-circle'
    };

    alert.innerHTML = `
      <div class="alert-icon">
        <i class="fas ${icons[type] || icons.info}"></i>
      </div>
      <div class="alert-content">
        ${title ? `<div class="alert-title">${title}</div>` : ''}
        ${message ? `<div>${message}</div>` : ''}
      </div>
      ${dismissible ? `
        <button type="button" class="btn-close" aria-label="Đóng" style="margin-left: auto;">
          <i class="fas fa-times"></i>
        </button>
      ` : ''}
    `;

    if (dismissible) {
      const closeBtn = alert.querySelector('.btn-close');
      closeBtn.addEventListener('click', () => {
        alert.style.animation = 'fadeIn 0.3s ease-out reverse';
        setTimeout(() => alert.remove(), 300);
      });
    }

    return alert;
  }

  // ============================================
  // LOADING STATES
  // ============================================
  function showLoading(element) {
    if (!element) return null;
    
    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.innerHTML = '<div class="spinner" style="width: 32px; height: 32px; border-width: 3px;"></div>';
    element.style.position = 'relative';
    element.appendChild(overlay);
    
    return overlay;
  }

  function hideLoading(overlay) {
    if (overlay && overlay.parentNode) {
      overlay.parentNode.removeChild(overlay);
    }
  }

  // ============================================
  // AJAX/FETCH API
  // ============================================
  async function request(url, options = {}) {
    const defaultOptions = {
      headers: {
        'X-CSRFToken': getCookie('csrftoken') || config.csrfToken,
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json',
      },
      credentials: 'same-origin',
    };

    const mergedOptions = {
      ...defaultOptions,
      ...options,
      headers: {
        ...defaultOptions.headers,
        ...options.headers,
      },
    };

    // Handle FormData
    if (mergedOptions.body instanceof FormData) {
      delete mergedOptions.headers['Content-Type'];
    }

    try {
      const response = await fetch(url, mergedOptions);
      
      // Handle no content response
      if (response.status === 204) {
        return { success: true, noContent: true };
      }

      const contentType = response.headers.get('content-type');
      let data;
      
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        data = await response.text();
      }

      if (!response.ok) {
        const error = new Error(data.message || data.error || 'Đã xảy ra lỗi');
        error.status = response.status;
        error.data = data;
        throw error;
      }

      return { success: true, data, status: response.status };
    } catch (error) {
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        error.message = 'Không thể kết nối đến máy chủ';
      }
      return { success: false, error: error };
    }
  }

  // Convenience methods
  const api = {
    get: (url, options = {}) => request(url, { ...options, method: 'GET' }),
    post: (url, data, options = {}) => request(url, { ...options, method: 'POST', body: JSON.stringify(data) }),
    postForm: (url, formData, options = {}) => request(url, { ...options, method: 'POST', body: formData }),
    put: (url, data, options = {}) => request(url, { ...options, method: 'PUT', body: JSON.stringify(data) }),
    delete: (url, options = {}) => request(url, { ...options, method: 'DELETE' }),
  };

  // ============================================
  // FORM HANDLING
  // ============================================
  function handleFormSubmit(form, options = {}) {
    const {
      onSuccess = () => {},
      onError = () => {},
      onFinally = () => {},
      redirectUrl = null,
      showToastNotification = true,
      validateBeforeSubmit = null,
    } = options;

    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      // Custom validation
      if (validateBeforeSubmit && !validateBeforeSubmit(form)) {
        return;
      }

      const submitBtn = form.querySelector('[type="submit"]');
      const originalBtnText = submitBtn?.innerHTML;
      
      // Disable button and show loading
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner"></span> Đang xử lý...';
      }

      const formData = new FormData(form);
      const url = form.action || window.location.href;

      const result = await api.postForm(url, formData);

      // Restore button
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnText;
      }

      if (result.success) {
        if (showToastNotification) {
          toast.success('Thành công', 'Thao tác đã được thực hiện thành công!');
        }
        
        if (redirectUrl) {
          window.location.href = redirectUrl;
        } else if (result.data.redirect) {
          window.location.href = result.data.redirect;
        } else if (result.data.reload) {
          window.location.reload();
        }
        
        onSuccess(result.data);
      } else {
        if (showToastNotification) {
          toast.error('Lỗi', result.error.message || 'Đã xảy ra lỗi khi xử lý');
        }
        onError(result.error);
      }

      onFinally(result);
    });
  }

  // ============================================
  // CONFIRM DIALOG
  // ============================================
  function confirm(message = config.confirmMessage, title = config.confirmTitle) {
    return new Promise((resolve) => {
      const overlay = document.createElement('div');
      overlay.className = 'modal-overlay active';
      
      overlay.innerHTML = `
        <div class="modal" style="max-width: 400px;">
          <div class="modal-header">
            <h3 class="modal-title">${title}</h3>
            <button type="button" class="modal-close" aria-label="Đóng">
              <i class="fas fa-times"></i>
            </button>
          </div>
          <div class="modal-body">
            <p style="margin: 0; color: var(--text-secondary);">${message}</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-action="cancel">Hủy</button>
            <button type="button" class="btn btn-danger" data-action="confirm">Xác nhận</button>
          </div>
        </div>
      `;

      document.body.appendChild(overlay);

      const closeModal = (result) => {
        overlay.classList.remove('active');
        setTimeout(() => overlay.remove(), 200);
        resolve(result);
      };

      overlay.querySelector('[data-action="cancel"]').addEventListener('click', () => closeModal(false));
      overlay.querySelector('[data-action="confirm"]').addEventListener('click', () => closeModal(true));
      overlay.querySelector('.modal-close').addEventListener('click', () => closeModal(false));
      
      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) closeModal(false);
      });
    });
  }

  // ============================================
  // DELETE ACTION
  // ============================================
  async function handleDelete(url, message, redirectUrl = null) {
    const confirmed = await confirm(message);
    
    if (confirmed) {
      const result = await api.delete(url);
      
      if (result.success) {
        toast.success('Đã xóa', 'Dữ liệu đã được xóa thành công!');
        
        if (redirectUrl) {
          setTimeout(() => window.location.href = redirectUrl, 500);
        } else {
          // Remove row from table
          const row = document.querySelector(`tr[data-url="${url}"]`) || 
                      event?.target?.closest('tr');
          if (row) {
            row.style.animation = 'fadeIn 0.3s ease-out reverse';
            setTimeout(() => row.remove(), 300);
          } else {
            window.location.reload();
          }
        }
      } else {
        toast.error('Lỗi', result.error.message || 'Không thể xóa dữ liệu');
      }
    }
  }

  // ============================================
  // MODAL MANAGEMENT
  // ============================================
  function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add('active');
      document.body.style.overflow = 'hidden';
    }
  }

  function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove('active');
      document.body.style.overflow = '';
    }
  }

  function initModals() {
    // Close modal on overlay click
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
          overlay.classList.remove('active');
          document.body.style.overflow = '';
        }
      });
    });

    // Close modal on close button click
    document.querySelectorAll('.modal-close').forEach(btn => {
      btn.addEventListener('click', () => {
        const modal = btn.closest('.modal-overlay');
        if (modal) {
          modal.classList.remove('active');
          document.body.style.overflow = '';
        }
      });
    });

    // Close modal on Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        const activeModal = document.querySelector('.modal-overlay.active');
        if (activeModal) {
          activeModal.classList.remove('active');
          document.body.style.overflow = '';
        }
      }
    });
  }

  // ============================================
  // MOBILE SIDEBAR
  // ============================================
  function initSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.querySelector('.topbar-toggle');
    const overlay = document.querySelector('.sidebar-overlay') || createSidebarOverlay();

    if (!sidebar) return;

    function openSidebar() {
      sidebar.classList.add('active');
      overlay.classList.add('active');
    }

    function closeSidebar() {
      sidebar.classList.remove('active');
      overlay.classList.remove('active');
    }

    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => {
        if (sidebar.classList.contains('active')) {
          closeSidebar();
        } else {
          openSidebar();
        }
      });
    }

    overlay.addEventListener('click', closeSidebar);

    // Close sidebar on nav item click (mobile)
    sidebar.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', () => {
        if (window.innerWidth < 768) {
          closeSidebar();
        }
      });
    });
  }

  function createSidebarOverlay() {
    const overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    document.body.appendChild(overlay);
    return overlay;
  }

  // ============================================
  // DROPZONE (File Upload)
  // ============================================
  function initDropzones() {
    document.querySelectorAll('.form-file').forEach(dropzone => {
      const input = dropzone.querySelector('input[type="file"]');
      const text = dropzone.querySelector('.form-file-text');

      if (!input || !text) return;

      ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
          e.preventDefault();
          e.stopPropagation();
        });
      });

      ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => {
          dropzone.classList.add('dragover');
        });
      });

      ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => {
          dropzone.classList.remove('dragover');
        });
      });

      dropzone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
          input.files = files;
          updateFileName(dropzone, files[0]);
        }
      });

      input.addEventListener('change', () => {
        if (input.files.length > 0) {
          updateFileName(dropzone, input.files[0]);
        }
      });
    });
  }

  function updateFileName(dropzone, file) {
    let textEl = dropzone.querySelector('.form-file-text');
    if (!textEl) {
      textEl = document.createElement('div');
      textEl.className = 'form-file-text';
      dropzone.appendChild(textEl);
    }
    textEl.innerHTML = `<i class="fas fa-check-circle" style="color: var(--success-500);"></i> ${file.name}`;
  }

  // ============================================
  // SEARCH & FILTER
  // ============================================
  function initSearch(inputSelector, tableSelector, columns = []) {
    const input = document.querySelector(inputSelector);
    const table = document.querySelector(tableSelector);
    
    if (!input || !table) return;

    input.addEventListener('input', debounce(() => {
      const query = input.value.toLowerCase().trim();
      const rows = table.querySelectorAll('tbody tr');

      rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
      });
    }, 300));
  }

  // ============================================
  // TABS
  // ============================================
  function initTabs() {
    document.querySelectorAll('.tabs').forEach(tabsContainer => {
      const tabs = tabsContainer.querySelectorAll('.tab');
      const tabId = tabsContainer.dataset.tabGroup;

      tabs.forEach(tab => {
        tab.addEventListener('click', () => {
          tabs.forEach(t => t.classList.remove('active'));
          tab.classList.add('active');

          // Hide all tab content
          document.querySelectorAll(`[data-tab-group="${tabId}"]`).forEach(content => {
            content.style.display = 'none';
          });

          // Show selected tab content
          const targetId = tab.dataset.tab;
          const target = document.getElementById(targetId);
          if (target) {
            target.style.display = '';
          }
        });
      });
    });
  }

  // ============================================
  // DROPDOWN
  // ============================================
  function initDropdowns() {
    document.querySelectorAll('.dropdown').forEach(dropdown => {
      const trigger = dropdown.querySelector('[data-dropdown-trigger]') || dropdown;
      
      trigger.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('active');
      });
    });

    document.addEventListener('click', () => {
      document.querySelectorAll('.dropdown.active').forEach(d => {
        d.classList.remove('active');
      });
    });
  }

  // ============================================
  // DATA TABLE HELPERS
  // ============================================
  function updateTableContent(tableId, html) {
    const tbody = document.querySelector(`#${tableId} tbody`);
    if (tbody) {
      tbody.innerHTML = html;
    }
  }

  function reloadTable(tableId, url) {
    return new Promise(async (resolve, reject) => {
      const tbody = document.querySelector(`#${tableId} tbody`);
      if (!tbody) {
        reject(new Error('Table not found'));
        return;
      }

      const overlay = showLoading(tbody.parentElement);

      const result = await api.get(url);

      hideLoading(overlay);

      if (result.success) {
        if (typeof result.data === 'string') {
          tbody.innerHTML = result.data;
        } else if (result.data.html) {
          tbody.innerHTML = result.data.html;
        }
        resolve(result.data);
      } else {
        toast.error('Lỗi', 'Không thể tải dữ liệu');
        reject(result.error);
      }
    });
  }

  // ============================================
  // UTILITY FUNCTIONS
  // ============================================
  function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  function formatDate(date, locale = 'vi-VN') {
    return new Date(date).toLocaleDateString(locale, {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }

  function formatCurrency(amount, locale = 'vi-VN', currency = 'VND') {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency: currency
    }).format(amount);
  }

  // ============================================
  // INITIALIZATION
  // ============================================
  function init() {
    initModals();
    initSidebar();
    initDropzones();
    initTabs();
    initDropdowns();

    // Initialize form handlers
    document.querySelectorAll('form[data-ajax]').forEach(form => {
      handleFormSubmit(form, {
        showToastNotification: true,
        redirectUrl: form.dataset.redirect || null,
      });
    });

    // Initialize delete handlers
    document.querySelectorAll('[data-delete-url]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const url = btn.dataset.deleteUrl;
        const message = btn.dataset.deleteMessage || config.confirmMessage;
        const redirectUrl = btn.dataset.redirect || null;
        handleDelete(url, message, redirectUrl);
      });
    });
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // ============================================
  // PUBLIC API
  // ============================================
  return {
    // API
    api,
    
    // Toast
    toast,
    showAlert,
    
    // Loading
    showLoading,
    hideLoading,
    
    // Forms
    handleFormSubmit,
    
    // Dialogs
    confirm,
    handleDelete,
    
    // Modal
    openModal,
    closeModal,
    
    // Tables
    updateTableContent,
    reloadTable,
    
    // Search
    initSearch,
    
    // Utilities
    debounce,
    formatDate,
    formatCurrency,
    
    // Config
    config,
  };
})();

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ClinicAPI;
}

// Make available globally
window.ClinicAPI = ClinicAPI;

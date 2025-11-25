/**
 * Klar - Toast Notifications
 */

const Toast = (function() {
  const DURATION = 3000; // ms

  /**
   * Show a toast notification
   * @param {string} message - Message to display
   * @param {string} type - Type: 'info' | 'success' | 'error' | 'warning'
   */
  function show(message, type = 'info') {
    const container = $('#toasts');
    if (!container) return;

    const iconMap = {
      info: 'info',
      success: 'check-circle',
      error: 'alert-circle',
      warning: 'alert-triangle'
    };

    const toast = html(`
      <div class="toast toast-${type}" role="alert">
        <i data-feather="${iconMap[type] || 'info'}" class="w-5 h-5 flex-shrink-0"></i>
        <span class="text-sm">${escapeHtml(message)}</span>
      </div>
    `);

    container.appendChild(toast);

    // Update feather icons
    if (window.feather) {
      feather.replace();
    }

    // Auto-remove after duration
    setTimeout(() => {
      toast.classList.add('hiding');
      setTimeout(() => {
        toast.remove();
      }, 250);
    }, DURATION);
  }

  /**
   * Show success toast
   */
  function success(message) {
    show(message, 'success');
  }

  /**
   * Show error toast
   */
  function error(message) {
    show(message, 'error');
  }

  /**
   * Show warning toast
   */
  function warning(message) {
    show(message, 'warning');
  }

  /**
   * Show info toast
   */
  function info(message) {
    show(message, 'info');
  }

  // Public API
  return {
    show,
    success,
    error,
    warning,
    info
  };
})();

/**
 * Klar - Tabs Component
 * (Tab rendering is handled by Router, this provides additional tab utilities)
 */

const Tabs = (function() {
  /**
   * Create a sub-tab navigation component
   * @param {Array} tabs - Array of { id, label } objects
   * @param {string} activeId - Currently active tab ID
   * @param {function} onChange - Callback when tab changes
   * @returns {HTMLElement}
   */
  function createSubTabs(tabs, activeId, onChange) {
    const container = document.createElement('div');
    container.className = 'flex gap-1 p-1 bg-secondary-50/50 dark:bg-secondary-600/50 rounded-lg';

    tabs.forEach(tab => {
      const button = document.createElement('button');
      button.className = `px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
        tab.id === activeId
          ? 'bg-white dark:bg-secondary-500 text-secondary dark:text-white shadow-sm'
          : 'text-secondary/60 dark:text-white/60 hover:text-secondary dark:hover:text-white'
      }`;
      button.textContent = tab.label;
      button.dataset.tab = tab.id;

      button.addEventListener('click', () => {
        // Update active state
        container.querySelectorAll('button').forEach(btn => {
          const isActive = btn.dataset.tab === tab.id;
          btn.className = `px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
            isActive
              ? 'bg-white dark:bg-secondary-500 text-secondary dark:text-white shadow-sm'
              : 'text-secondary/60 dark:text-white/60 hover:text-secondary dark:hover:text-white'
          }`;
        });

        // Call onChange
        if (onChange) {
          onChange(tab.id);
        }
      });

      container.appendChild(button);
    });

    return container;
  }

  /**
   * Create a pill/button style tab group
   */
  function createPillTabs(tabs, activeId, onChange) {
    const container = document.createElement('div');
    container.className = 'inline-flex gap-2';

    tabs.forEach(tab => {
      const button = document.createElement('button');
      const isActive = tab.id === activeId;

      button.className = `px-4 py-2 text-sm font-medium rounded-full transition-colors ${
        isActive
          ? 'bg-primary text-secondary'
          : 'bg-secondary/10 dark:bg-white/10 text-secondary/70 dark:text-white/70 hover:bg-secondary/20 dark:hover:bg-white/20'
      }`;
      button.textContent = tab.label;
      button.dataset.tab = tab.id;

      button.addEventListener('click', () => {
        // Update all buttons
        container.querySelectorAll('button').forEach(btn => {
          const isNowActive = btn.dataset.tab === tab.id;
          btn.className = `px-4 py-2 text-sm font-medium rounded-full transition-colors ${
            isNowActive
              ? 'bg-primary text-secondary'
              : 'bg-secondary/10 dark:bg-white/10 text-secondary/70 dark:text-white/70 hover:bg-secondary/20 dark:hover:bg-white/20'
          }`;
        });

        if (onChange) {
          onChange(tab.id);
        }
      });

      container.appendChild(button);
    });

    return container;
  }

  // Public API
  return {
    createSubTabs,
    createPillTabs
  };
})();

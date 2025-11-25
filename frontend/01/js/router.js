/**
 * Klar - Tab Router
 * Handles navigation between tabs
 */

const Router = (function() {
  // Tab definitions
  const TABS = [
    { id: 'dashboard', label: 'Dashboard', icon: 'home' },
    { id: 'list', label: 'Investors', icon: 'users' },
    { id: 'map', label: 'Map', icon: 'map' },
    { id: 'charts', label: 'Charts', icon: 'bar-chart-2' },
    { id: 'saved', label: 'Saved', icon: 'bookmark' },
    { id: 'chat', label: 'Chat', icon: 'message-circle' },
    { id: 'settings', label: 'Settings', icon: 'settings' }
  ];

  // Page render functions (populated by page modules)
  const pages = {};

  /**
   * Register a page renderer
   */
  function registerPage(id, renderFn) {
    pages[id] = renderFn;
  }

  /**
   * Navigate to a tab
   */
  function navigate(tabId) {
    const tab = TABS.find(t => t.id === tabId);
    if (!tab) {
      console.warn(`Unknown tab: ${tabId}`);
      return;
    }

    // Update state
    State.set('activeTab', tabId);

    // Update URL hash
    setHash(tabId);

    // Update tab bar
    updateTabBar(tabId);

    // Render page content
    renderPage(tabId);
  }

  /**
   * Update tab bar active state
   */
  function updateTabBar(activeId) {
    const tabButtons = $$('.tab-btn');
    tabButtons.forEach(btn => {
      const isActive = btn.dataset.tab === activeId;
      btn.classList.toggle('active', isActive);
      btn.setAttribute('aria-selected', isActive);
    });
  }

  /**
   * Render page content
   */
  function renderPage(tabId) {
    const content = $('#content');
    if (!content) return;

    // Clear content
    content.innerHTML = '';

    // Call page renderer
    const render = pages[tabId];
    if (render) {
      render(content);
    } else {
      // Placeholder for unimplemented pages
      content.innerHTML = `
        <div class="empty-state">
          <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <circle cx="12" cy="12" r="10"></circle>
            <path d="M12 16v-4"></path>
            <path d="M12 8h.01"></path>
          </svg>
          <p class="text-lg font-medium mt-2">${TABS.find(t => t.id === tabId)?.label || tabId}</p>
          <p class="text-sm opacity-60">Coming soon</p>
        </div>
      `;
    }

    // Update feather icons
    if (window.feather) {
      feather.replace();
    }
  }

  /**
   * Render tab bar
   */
  function renderTabs() {
    const tabsContainer = $('#tabs');
    if (!tabsContainer) return;

    const activeTab = State.get('activeTab') || 'dashboard';

    tabsContainer.innerHTML = `
      <div class="flex overflow-x-auto scrollbar-hide px-2 sm:px-4">
        ${TABS.map(tab => `
          <button
            class="tab-btn ${tab.id === activeTab ? 'active' : ''}"
            data-tab="${tab.id}"
            role="tab"
            aria-selected="${tab.id === activeTab}"
            aria-controls="content"
          >
            <i data-feather="${tab.icon}" class="w-4 h-4"></i>
            <span class="hide-mobile">${tab.label}</span>
          </button>
        `).join('')}
      </div>
    `;

    // Add click handlers
    $$('.tab-btn', tabsContainer).forEach(btn => {
      btn.addEventListener('click', () => {
        navigate(btn.dataset.tab);
      });
    });

    // Update feather icons
    if (window.feather) {
      feather.replace();
    }
  }

  /**
   * Initialize router
   */
  function init() {
    // Render tab bar
    renderTabs();

    // Listen for hash changes
    window.addEventListener('hashchange', () => {
      const { tab } = parseHash();
      if (tab && TABS.some(t => t.id === tab)) {
        navigate(tab);
      }
    });

    // Navigate to initial tab from hash or default
    const { tab } = parseHash();
    const initialTab = TABS.some(t => t.id === tab) ? tab : 'dashboard';
    navigate(initialTab);
  }

  /**
   * Get all tab definitions
   */
  function getTabs() {
    return [...TABS];
  }

  // Public API
  return {
    TABS,
    registerPage,
    navigate,
    init,
    getTabs,
    renderPage
  };
})();

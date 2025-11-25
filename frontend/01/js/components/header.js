/**
 * Klar - Header Component
 */

const Header = (function() {
  let searchInput = null;

  /**
   * Render header
   */
  function render() {
    const header = $('#header');
    if (!header) return;

    header.innerHTML = `
      <div class="flex items-center justify-between px-4 py-3">
        <!-- Logo -->
        <a href="#dashboard" class="flex items-center gap-2 flex-shrink-0">
          <img src="/assets/logo.svg" alt="Klar" class="w-8 h-8">
          <span class="font-semibold text-lg hidden sm:inline">Klar</span>
        </a>

        <!-- Search -->
        <div class="flex-1 max-w-md mx-4">
          <div class="relative">
            <input
              type="search"
              id="global-search"
              class="input pl-10 pr-4 w-full"
              placeholder="Search investors, funds..."
              autocomplete="off"
            >
            <i data-feather="search" class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 opacity-40"></i>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex items-center gap-2">
          <button
            id="theme-toggle"
            class="btn btn-icon btn-ghost"
            title="Toggle theme"
            aria-label="Toggle theme"
          >
            <i data-feather="moon" class="w-5 h-5 dark:hidden"></i>
            <i data-feather="sun" class="w-5 h-5 hidden dark:block"></i>
          </button>
        </div>
      </div>
    `;

    // Update feather icons
    if (window.feather) {
      feather.replace();
    }

    // Setup search
    setupSearch();

    // Setup theme toggle
    setupThemeToggle();
  }

  /**
   * Setup search functionality
   */
  function setupSearch() {
    searchInput = $('#global-search');
    if (!searchInput) return;

    const debouncedSearch = debounce((value) => {
      State.set('searchQuery', value);

      // Navigate to list tab if not already there and has query
      if (value && State.get('activeTab') !== 'list') {
        Router.navigate('list');
      }
    }, 300);

    searchInput.addEventListener('input', (e) => {
      debouncedSearch(e.target.value);
    });

    // Clear search on Escape
    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        searchInput.value = '';
        State.set('searchQuery', '');
        searchInput.blur();
      }
    });

    // Keyboard shortcut: Cmd/Ctrl + K to focus search
    document.addEventListener('keydown', (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        searchInput.focus();
        searchInput.select();
      }
    });
  }

  /**
   * Setup theme toggle
   */
  function setupThemeToggle() {
    const toggle = $('#theme-toggle');
    if (!toggle) return;

    toggle.addEventListener('click', async () => {
      const html = document.documentElement;
      const isDark = html.classList.contains('dark');
      const newTheme = isDark ? 'light' : 'dark';

      // Update DOM
      State.applyTheme(newTheme);

      // Persist
      await Store.updateSettings({ theme: newTheme });

      // Update feather icons (for the toggle icon swap)
      if (window.feather) {
        feather.replace();
      }
    });
  }

  /**
   * Update search input value (e.g., from state)
   */
  function setSearchValue(value) {
    if (searchInput) {
      searchInput.value = value;
    }
  }

  /**
   * Focus search input
   */
  function focusSearch() {
    if (searchInput) {
      searchInput.focus();
    }
  }

  // Public API
  return {
    render,
    setSearchValue,
    focusSearch
  };
})();

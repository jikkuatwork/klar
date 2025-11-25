/**
 * Klar - Header Component
 */

const Header = (function() {
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

        <!-- Actions -->
        <div class="flex items-center gap-2">
          <button
            id="add-investor-btn"
            class="btn btn-sm btn-primary hidden sm:flex"
            title="Add new investor"
          >
            <i data-feather="plus" class="w-4 h-4"></i>
            <span class="hidden md:inline">Add</span>
          </button>
          <button
            id="add-investor-btn-mobile"
            class="btn btn-icon btn-primary sm:hidden"
            title="Add new investor"
          >
            <i data-feather="plus" class="w-5 h-5"></i>
          </button>
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

    // Setup theme toggle
    setupThemeToggle();

    // Setup add investor button
    setupAddButton();

    // Setup search shortcut (Cmd/Ctrl+K)
    setupSearchShortcut();
  }

  /**
   * Setup keyboard shortcut for search focus
   */
  function setupSearchShortcut() {
    // Keyboard shortcut: Cmd/Ctrl + K to focus search in filter bar
    document.addEventListener('keydown', (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        const filterSearch = $('#filter-search');
        if (filterSearch) {
          filterSearch.focus();
          filterSearch.select();
        }
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
   * Setup add investor button
   */
  function setupAddButton() {
    const addBtn = $('#add-investor-btn');
    const addBtnMobile = $('#add-investor-btn-mobile');

    const handleAdd = () => {
      AddRecord.open();
    };

    addBtn?.addEventListener('click', handleAdd);
    addBtnMobile?.addEventListener('click', handleAdd);
  }

  // Public API
  return {
    render
  };
})();

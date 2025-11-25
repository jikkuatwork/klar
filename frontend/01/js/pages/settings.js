/**
 * Klar - Settings Page
 */

(function() {
  function render(container) {
    const settings = State.get('userData')?.settings || {};
    const stats = State.getStats();

    container.innerHTML = `
      <div class="p-4 sm:p-6 max-w-2xl mx-auto">
        <h1 class="text-2xl font-semibold mb-6">Settings</h1>

        <!-- Appearance -->
        <section class="mb-8">
          <h2 class="text-lg font-medium mb-4">Appearance</h2>
          <div class="card space-y-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="font-medium">Theme</p>
                <p class="text-sm text-secondary/60 dark:text-white/60">Choose your preferred color scheme</p>
              </div>
              <select id="theme-select" class="input w-auto">
                <option value="light" ${settings.theme === 'light' ? 'selected' : ''}>Light</option>
                <option value="dark" ${settings.theme === 'dark' ? 'selected' : ''}>Dark</option>
                <option value="system" ${settings.theme === 'system' ? 'selected' : ''}>System</option>
              </select>
            </div>

            <div class="flex items-center justify-between">
              <div>
                <p class="font-medium">Default List View</p>
                <p class="text-sm text-secondary/60 dark:text-white/60">Table or card layout for investors</p>
              </div>
              <select id="view-select" class="input w-auto">
                <option value="table" ${settings.listView === 'table' ? 'selected' : ''}>Table</option>
                <option value="cards" ${settings.listView === 'cards' ? 'selected' : ''}>Cards</option>
              </select>
            </div>
          </div>
        </section>

        <!-- Data -->
        <section class="mb-8">
          <h2 class="text-lg font-medium mb-4">Data</h2>
          <div class="card space-y-4">
            <div class="flex items-center justify-between">
              <div>
                <p class="font-medium">Export All Data</p>
                <p class="text-sm text-secondary/60 dark:text-white/60">Download all investor data as CSV</p>
              </div>
              <button id="export-all" class="btn btn-secondary btn-sm">
                <i data-feather="download" class="w-4 h-4"></i>
                Export
              </button>
            </div>

            <div class="border-t border-secondary/10 dark:border-white/10 pt-4">
              <div class="flex items-center justify-between">
                <div>
                  <p class="font-medium text-red-600">Clear All User Data</p>
                  <p class="text-sm text-secondary/60 dark:text-white/60">Remove notes, stars, saved lists, and settings</p>
                </div>
                <button id="clear-data" class="btn btn-sm bg-red-600 text-white hover:bg-red-700">
                  <i data-feather="trash-2" class="w-4 h-4"></i>
                  Clear
                </button>
              </div>
            </div>
          </div>
        </section>

        <!-- About -->
        <section class="mb-8">
          <h2 class="text-lg font-medium mb-4">About</h2>
          <div class="card">
            <div class="flex items-center gap-4 mb-4">
              <img src="/assets/logo.svg" alt="Klar" class="w-12 h-12">
              <div>
                <p class="font-semibold text-lg">Klar</p>
                <p class="text-sm text-secondary/60 dark:text-white/60">Capital, Clarified.</p>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p class="text-secondary/60 dark:text-white/60">Total Records</p>
                <p class="font-medium">${stats.totalRecords}</p>
              </div>
              <div>
                <p class="text-secondary/60 dark:text-white/60">Unique Funds</p>
                <p class="font-medium">${stats.uniqueFunds}</p>
              </div>
              <div>
                <p class="text-secondary/60 dark:text-white/60">Your Notes</p>
                <p class="font-medium">${stats.withNotes}</p>
              </div>
              <div>
                <p class="text-secondary/60 dark:text-white/60">Starred</p>
                <p class="font-medium">${stats.starred}</p>
              </div>
            </div>

            <div class="mt-4 pt-4 border-t border-secondary/10 dark:border-white/10">
              <p class="text-xs text-secondary/40 dark:text-white/40">
                Built for Silversky Capital
              </p>
            </div>
          </div>
        </section>
      </div>
    `;

    // Theme select
    $('#theme-select', container)?.addEventListener('change', async (e) => {
      const theme = e.target.value;
      State.applyTheme(theme);
      await Store.updateSettings({ theme });
      Toast.success('Theme updated');

      // Re-render header for icon update
      Header.render();
    });

    // View select
    $('#view-select', container)?.addEventListener('change', async (e) => {
      const listView = e.target.value;
      State.set('listView', listView);
      await Store.updateSettings({ listView });
      Toast.success('Default view updated');
    });

    // Export all
    $('#export-all', container)?.addEventListener('click', () => {
      const records = State.get('records');
      CSV.download(records, 'klar-full-export');
      Toast.success('Export downloaded');
    });

    // Clear data
    $('#clear-data', container)?.addEventListener('click', async () => {
      if (confirm('Are you sure you want to clear all user data? This cannot be undone.')) {
        await Store.clearAllData();

        // Reload user data
        const userData = await Store.loadUserData();
        State.set('userData', userData);

        // Re-render
        Router.renderPage('settings');
        Toast.success('User data cleared');
      }
    });

    // Update feather icons
    if (window.feather) {
      feather.replace();
    }
  }

  // Register page
  Router.registerPage('settings', render);
})();

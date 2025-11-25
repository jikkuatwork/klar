/**
 * Klar - Main Application Entry Point
 */

(async function() {
  'use strict';

  const loadingEl = $('#loading');

  try {
    console.log('Klar: Initializing...');

    // 1. Load user data from IndexedDB
    console.log('Klar: Loading user data...');
    const userData = await Store.loadUserData();

    // 2. Apply theme immediately
    State.applyTheme(userData.settings.theme);

    // 3. Load CSV data
    console.log('Klar: Loading CSV data...');
    const csvRecords = await CSV.load('/data.csv');
    console.log(`Klar: Loaded ${csvRecords.length} records from CSV`);

    // 4. Merge with user-added records
    const addedRecords = userData.addedRecords || [];
    const allRecords = [...csvRecords, ...addedRecords];
    console.log(`Klar: Total records: ${allRecords.length} (${addedRecords.length} user-added)`);

    // 5. Enrich records with user data
    const enrichedRecords = allRecords.map(record => {
      const pocId = record['poc.id'];
      return {
        ...record,
        _note: userData.notes[pocId] || null,
        _starred: userData.starred.includes(pocId),
        _isUserAdded: record._isUserAdded || false
      };
    });

    // 6. Initialize state
    State.initialize(enrichedRecords, userData);

    // 7. Render header
    Header.render();

    // 8. Initialize router (renders tabs and first page)
    Router.init();

    // 9. Hide loading overlay
    if (loadingEl) {
      loadingEl.classList.add('animate-fade-out');
      setTimeout(() => {
        loadingEl.style.display = 'none';
      }, 250);
    }

    console.log('Klar: Initialization complete');

    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      const theme = State.get('userData')?.settings?.theme;
      if (theme === 'system') {
        State.applyTheme('system');
      }
    });

  } catch (error) {
    console.error('Klar: Initialization failed', error);

    // Show error state
    if (loadingEl) {
      loadingEl.innerHTML = `
        <div class="text-center text-white">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-16 h-16 mx-auto mb-4 text-red-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <circle cx="12" cy="12" r="10"></circle>
            <path d="M12 8v4"></path>
            <path d="M12 16h.01"></path>
          </svg>
          <p class="text-lg font-medium mb-2">Failed to load</p>
          <p class="text-sm text-white/60 mb-4">${escapeHtml(error.message)}</p>
          <button onclick="location.reload()" class="btn btn-primary">
            Retry
          </button>
        </div>
      `;
    }
  }
})();

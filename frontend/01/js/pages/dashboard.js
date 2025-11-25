/**
 * Klar - Dashboard Page
 */

(function() {
  function render(container) {
    const stats = State.getStats();

    container.innerHTML = `
      <div class="p-4 sm:p-6 max-w-6xl mx-auto">
        <h1 class="text-2xl font-semibold mb-6">Dashboard</h1>

        <!-- Stats Grid -->
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
          ${statCard('Total Contacts', stats.totalRecords, 'users')}
          ${statCard('Unique Funds', stats.uniqueFunds, 'briefcase')}
          ${statCard('Countries', stats.uniqueCountries, 'globe')}
          ${statCard('Total AUM', Format.currency(stats.totalAUM), 'dollar-sign')}
          ${statCard('With Email', stats.withEmail, 'mail')}
        </div>

        <!-- User Activity -->
        <h2 class="text-lg font-semibold mb-4">Your Activity</h2>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
          ${activityCard('Starred', stats.starred, 'star', 'starred')}
          ${activityCard('With Notes', stats.withNotes, 'file-text', 'notes')}
          ${activityCard('Saved Lists', stats.savedLists, 'bookmark', 'saved')}
          ${activityCard('Recently Viewed', State.get('userData')?.recent?.length || 0, 'clock', 'recent')}
        </div>

        <!-- Quick Actions -->
        <h2 class="text-lg font-semibold mb-4">Quick Filters</h2>
        <div class="flex flex-wrap gap-3">
          ${quickFilterButton('Family Offices', { fundType: ['Family Office'] })}
          ${quickFilterButton('US Funds', { country: ['US'] })}
          ${quickFilterButton('Europe', { country: ['UK', 'DE', 'FR', 'CH', 'NL'] })}
          ${quickFilterButton('Large Funds (>$1B)', { aumMin: 1000000000 })}
          ${quickFilterButton('Venture Capital', { sector: ['venture-capital'] })}
          ${quickFilterButton('Has Email', { hasEmail: true })}
        </div>
      </div>
    `;

    // Setup quick filter buttons
    $$('[data-quick-filter]', container).forEach(btn => {
      btn.addEventListener('click', () => {
        const filters = JSON.parse(btn.dataset.quickFilter);
        State.clearFilters();
        State.update({ filters: { ...State.get('filters'), ...filters } });
        Router.navigate('list');
      });
    });

    // Setup activity card clicks
    $$('[data-activity]', container).forEach(card => {
      card.addEventListener('click', () => {
        const activity = card.dataset.activity;
        if (activity === 'starred' || activity === 'notes' || activity === 'recent') {
          State.set('savedSubTab', activity === 'notes' ? 'notes' : activity);
          Router.navigate('saved');
        } else if (activity === 'saved') {
          State.set('savedSubTab', 'saved');
          Router.navigate('saved');
        }
      });
    });

    // Update feather icons
    if (window.feather) {
      feather.replace();
    }
  }

  function statCard(label, value, icon) {
    return `
      <div class="card">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
            <i data-feather="${icon}" class="w-5 h-5 text-primary-600"></i>
          </div>
          <div>
            <p class="text-2xl font-semibold">${value}</p>
            <p class="text-xs text-secondary/60 dark:text-white/60">${label}</p>
          </div>
        </div>
      </div>
    `;
  }

  function activityCard(label, count, icon, activity) {
    return `
      <div class="card cursor-pointer hover:border-primary/50" data-activity="${activity}">
        <div class="flex items-center gap-3">
          <i data-feather="${icon}" class="w-5 h-5 text-primary"></i>
          <div>
            <p class="text-xl font-semibold">${count}</p>
            <p class="text-xs text-secondary/60 dark:text-white/60">${label}</p>
          </div>
        </div>
      </div>
    `;
  }

  function quickFilterButton(label, filters) {
    return `
      <button
        class="btn btn-ghost border border-secondary/10 dark:border-white/10 hover:border-primary"
        data-quick-filter='${JSON.stringify(filters)}'
      >
        ${label}
      </button>
    `;
  }

  // Register page
  Router.registerPage('dashboard', render);
})();

/**
 * Klar - List Page (Investors)
 * Placeholder - Full implementation in Phase 2
 */

(function() {
  function render(container) {
    const records = State.getFilteredRecords();
    const totalRecords = State.get('records').length;
    const listView = State.get('listView');

    container.innerHTML = `
      <div class="h-full flex flex-col">
        <!-- Toolbar -->
        <div class="flex-shrink-0 p-4 border-b border-secondary/10 dark:border-white/10">
          <div class="flex items-center justify-between gap-4">
            <div class="flex items-center gap-2">
              <span class="text-sm text-secondary/60 dark:text-white/60">
                Showing <strong>${records.length}</strong> of ${totalRecords}
              </span>
            </div>
            <div class="flex items-center gap-2">
              <button class="btn btn-sm btn-ghost" id="view-table" title="Table view">
                <i data-feather="list" class="w-4 h-4"></i>
              </button>
              <button class="btn btn-sm btn-ghost" id="view-cards" title="Card view">
                <i data-feather="grid" class="w-4 h-4"></i>
              </button>
              <button class="btn btn-sm btn-primary" id="export-btn">
                <i data-feather="download" class="w-4 h-4"></i>
                <span class="hidden sm:inline">Export</span>
              </button>
            </div>
          </div>
        </div>

        <!-- List Content -->
        <div class="flex-1 overflow-y-auto p-4">
          ${listView === 'table' ? renderTable(records) : renderCards(records)}
        </div>
      </div>
    `;

    // Setup view toggles
    $('#view-table', container)?.addEventListener('click', () => {
      State.set('listView', 'table');
      Router.renderPage('list');
    });

    $('#view-cards', container)?.addEventListener('click', () => {
      State.set('listView', 'cards');
      Router.renderPage('list');
    });

    // Setup export
    $('#export-btn', container)?.addEventListener('click', () => {
      CSV.download(records, 'klar-export');
      Toast.success('Export downloaded');
    });

    // Setup row clicks
    $$('[data-poc-id]', container).forEach(el => {
      el.addEventListener('click', () => {
        const pocId = el.dataset.pocId;
        // TODO: Open detail modal (Phase 3)
        Toast.info(`Detail view coming soon: ${pocId}`);
      });
    });

    // Update feather icons
    if (window.feather) {
      feather.replace();
    }
  }

  function renderTable(records) {
    if (records.length === 0) {
      return `
        <div class="empty-state">
          <i data-feather="users" class="w-12 h-12"></i>
          <p class="text-lg font-medium mt-2">No investors found</p>
          <p class="text-sm">Try adjusting your search or filters</p>
        </div>
      `;
    }

    return `
      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Role</th>
              <th>Fund</th>
              <th>Type</th>
              <th>Location</th>
              <th>AUM</th>
            </tr>
          </thead>
          <tbody>
            ${records.slice(0, 100).map(r => `
              <tr class="clickable" data-poc-id="${r['poc.id']}">
                <td>
                  <div class="flex items-center gap-2">
                    ${State.isStarred(r['poc.id']) ? '<i data-feather="star" class="w-4 h-4 text-primary fill-current"></i>' : ''}
                    <span class="font-medium">${escapeHtml(Format.name(r['poc.first_name'], r['poc.last_name']))}</span>
                  </div>
                </td>
                <td class="text-secondary/70 dark:text-white/70">${escapeHtml(r['poc.role'] || '-')}</td>
                <td>${escapeHtml(r['fund.title'] || '-')}</td>
                <td>
                  <span class="badge">${escapeHtml(r['fund.type'] || '-')}</span>
                </td>
                <td>
                  <div class="flex items-center gap-2">
                    ${Format.flag(r['fund.country'])}
                    <span>${escapeHtml(r['fund.city'] || '')}</span>
                  </div>
                </td>
                <td class="font-medium">${Format.currency(r['fund.aum.value'])}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
        ${records.length > 100 ? `
          <p class="text-center text-sm text-secondary/60 dark:text-white/60 py-4">
            Showing first 100 of ${records.length} results
          </p>
        ` : ''}
      </div>
    `;
  }

  function renderCards(records) {
    if (records.length === 0) {
      return `
        <div class="empty-state">
          <i data-feather="users" class="w-12 h-12"></i>
          <p class="text-lg font-medium mt-2">No investors found</p>
          <p class="text-sm">Try adjusting your search or filters</p>
        </div>
      `;
    }

    return `
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        ${records.slice(0, 60).map(r => `
          <div class="card cursor-pointer" data-poc-id="${r['poc.id']}">
            <div class="flex items-start justify-between mb-3">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center font-medium text-primary-700">
                  ${Format.initials(r['poc.first_name'], r['poc.last_name'])}
                </div>
                <div>
                  <p class="font-medium">${escapeHtml(Format.name(r['poc.first_name'], r['poc.last_name']))}</p>
                  <p class="text-sm text-secondary/60 dark:text-white/60">${escapeHtml(r['poc.role'] || '-')}</p>
                </div>
              </div>
              ${State.isStarred(r['poc.id']) ? '<i data-feather="star" class="w-4 h-4 text-primary fill-current"></i>' : ''}
            </div>
            <p class="text-sm font-medium mb-2">${escapeHtml(r['fund.title'] || '-')}</p>
            <div class="flex items-center gap-2 text-sm text-secondary/60 dark:text-white/60 mb-2">
              ${Format.flag(r['fund.country'])}
              <span>${Format.location(r['fund.country'], r['fund.city'])}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="badge">${escapeHtml(r['fund.type'] || '-')}</span>
              <span class="font-medium">${Format.currency(r['fund.aum.value'])}</span>
            </div>
          </div>
        `).join('')}
      </div>
      ${records.length > 60 ? `
        <p class="text-center text-sm text-secondary/60 dark:text-white/60 py-4">
          Showing first 60 of ${records.length} results
        </p>
      ` : ''}
    `;
  }

  // Register page
  Router.registerPage('list', render);
})();

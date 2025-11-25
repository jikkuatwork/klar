/**
 * Klar - List Page (Investors)
 * Full implementation with filters, sorting, pagination
 */

(function() {
  let displayCount = 50;
  const INCREMENT = 50;

  function render(container) {
    const records = State.getFilteredRecords();
    const totalRecords = State.get('records').length;
    const listView = State.get('listView');
    const sort = State.get('sort');
    const searchQuery = State.get('searchQuery');

    // Reset display count when filters change
    displayCount = 50;

    container.innerHTML = `
      <div class="h-full flex flex-col">
        <!-- Filters -->
        <div id="filters-container" class="flex-shrink-0"></div>

        <!-- Toolbar -->
        <div class="flex-shrink-0 px-4 py-3 border-b border-secondary/10 dark:border-white/10 bg-white dark:bg-secondary">
          <div class="flex items-center justify-between gap-4">
            <div class="flex items-center gap-3">
              <span class="text-sm text-secondary/60 dark:text-white/60">
                Showing <strong>${Math.min(displayCount, records.length)}</strong> of <strong>${records.length}</strong>
                ${records.length !== totalRecords ? `<span class="text-xs">(filtered from ${totalRecords})</span>` : ''}
              </span>
              ${searchQuery ? `
                <span class="badge badge-primary">
                  Search: "${escapeHtml(Format.truncate(searchQuery, 20))}"
                </span>
              ` : ''}
            </div>
            <div class="flex items-center gap-2">
              <!-- View Toggle -->
              <div class="flex bg-secondary/5 dark:bg-white/5 rounded-lg p-0.5">
                <button class="btn btn-sm ${listView === 'table' ? 'bg-white dark:bg-secondary-500 shadow-sm' : 'btn-ghost'}" id="view-table" title="Table view">
                  <i data-feather="list" class="w-4 h-4"></i>
                </button>
                <button class="btn btn-sm ${listView === 'cards' ? 'bg-white dark:bg-secondary-500 shadow-sm' : 'btn-ghost'}" id="view-cards" title="Card view">
                  <i data-feather="grid" class="w-4 h-4"></i>
                </button>
              </div>

              <!-- Save List -->
              <button class="btn btn-sm btn-ghost hidden sm:flex" id="save-list-btn" title="Save current list" ${records.length === 0 ? 'disabled' : ''}>
                <i data-feather="bookmark" class="w-4 h-4"></i>
              </button>

              <!-- Export -->
              <button class="btn btn-sm btn-primary" id="export-btn" ${records.length === 0 ? 'disabled' : ''}>
                <i data-feather="download" class="w-4 h-4"></i>
                <span class="hidden sm:inline">Export</span>
              </button>
            </div>
          </div>
        </div>

        <!-- List Content -->
        <div class="flex-1 overflow-y-auto" id="list-content">
          <div class="p-4">
            ${listView === 'table' ? renderTable(records, sort) : renderCards(records)}
          </div>
        </div>
      </div>
    `;

    // Render filters
    const filtersContainer = $('#filters-container', container);
    if (filtersContainer) {
      Filters.render(filtersContainer);
    }

    // Setup view toggles
    $('#view-table', container)?.addEventListener('click', () => {
      State.set('listView', 'table');
      Store.updateSettings({ listView: 'table' });
      Router.renderPage('list');
    });

    $('#view-cards', container)?.addEventListener('click', () => {
      State.set('listView', 'cards');
      Store.updateSettings({ listView: 'cards' });
      Router.renderPage('list');
    });

    // Setup save list
    $('#save-list-btn', container)?.addEventListener('click', () => {
      openSaveListModal(records);
    });

    // Setup export
    $('#export-btn', container)?.addEventListener('click', () => {
      CSV.download(records, 'klar-export');
      Toast.success(`Exported ${records.length} records`);
    });

    // Setup row/card clicks
    $$('[data-poc-id]', container).forEach(el => {
      el.addEventListener('click', () => {
        const pocId = el.dataset.pocId;
        Modal.openDetail(pocId);
      });
    });

    // Setup sort headers
    $$('[data-sort]', container).forEach(th => {
      th.addEventListener('click', () => {
        const field = th.dataset.sort;
        const currentSort = State.get('sort');

        let newDirection = 'asc';
        if (currentSort.field === field) {
          newDirection = currentSort.direction === 'asc' ? 'desc' : 'asc';
        }

        State.set('sort', { field, direction: newDirection });
        Router.renderPage('list');
      });
    });

    // Setup load more
    $('#load-more-btn', container)?.addEventListener('click', () => {
      displayCount += INCREMENT;
      updateListContent(container, records);
    });

    // Listen for filter changes
    document.addEventListener('filtersChanged', () => {
      Router.renderPage('list');
    });

    // Setup infinite scroll
    const listContent = $('#list-content', container);
    if (listContent) {
      listContent.addEventListener('scroll', throttle(() => {
        const { scrollTop, scrollHeight, clientHeight } = listContent;
        if (scrollTop + clientHeight >= scrollHeight - 200) {
          if (displayCount < records.length) {
            displayCount += INCREMENT;
            updateListContent(container, records);
          }
        }
      }, 200));
    }

    // Update feather icons
    if (window.feather) {
      feather.replace();
    }
  }

  function updateListContent(container, records) {
    const listView = State.get('listView');
    const sort = State.get('sort');
    const contentArea = $('#list-content .p-4', container);

    if (contentArea) {
      contentArea.innerHTML = listView === 'table' ? renderTable(records, sort) : renderCards(records);

      // Re-attach click handlers
      $$('[data-poc-id]', contentArea).forEach(el => {
        el.addEventListener('click', () => {
          Modal.openDetail(el.dataset.pocId);
        });
      });

      // Re-attach sort handlers
      $$('[data-sort]', contentArea).forEach(th => {
        th.addEventListener('click', () => {
          const field = th.dataset.sort;
          const currentSort = State.get('sort');
          const newDirection = currentSort.field === field && currentSort.direction === 'asc' ? 'desc' : 'asc';
          State.set('sort', { field, direction: newDirection });
          Router.renderPage('list');
        });
      });

      if (window.feather) {
        feather.replace();
      }
    }
  }

  function renderTable(records, sort) {
    if (records.length === 0) {
      return `
        <div class="empty-state">
          <i data-feather="users" class="w-12 h-12"></i>
          <p class="text-lg font-medium mt-2">No investors found</p>
          <p class="text-sm">Try adjusting your search or filters</p>
          <button class="btn btn-primary mt-4" onclick="State.clearFilters(); Router.renderPage('list');">
            Clear Filters
          </button>
        </div>
      `;
    }

    const sortIcon = (field) => {
      if (sort.field !== field) return '';
      return sort.direction === 'asc'
        ? '<i data-feather="chevron-up" class="w-3 h-3 inline ml-1"></i>'
        : '<i data-feather="chevron-down" class="w-3 h-3 inline ml-1"></i>';
    };

    const displayRecords = records.slice(0, displayCount);

    return `
      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th class="sortable" data-sort="poc.last_name">Name ${sortIcon('poc.last_name')}</th>
              <th class="hide-mobile">Role</th>
              <th class="sortable" data-sort="fund.title">Fund ${sortIcon('fund.title')}</th>
              <th class="sortable" data-sort="fund.type">Type ${sortIcon('fund.type')}</th>
              <th class="sortable" data-sort="fund.country">Location ${sortIcon('fund.country')}</th>
              <th class="sortable text-right" data-sort="fund.aum.value">AUM ${sortIcon('fund.aum.value')}</th>
            </tr>
          </thead>
          <tbody>
            ${displayRecords.map(r => `
              <tr class="clickable" data-poc-id="${r['poc.id']}">
                <td>
                  <div class="flex items-center gap-2">
                    <div class="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-xs font-medium text-primary-700 flex-shrink-0">
                      ${Format.initials(r['poc.first_name'], r['poc.last_name'])}
                    </div>
                    <div class="min-w-0">
                      <div class="flex items-center gap-1">
                        ${State.isStarred(r['poc.id']) ? '<i data-feather="star" class="w-3 h-3 text-primary fill-current flex-shrink-0"></i>' : ''}
                        ${State.getNote(r['poc.id']) ? '<i data-feather="file-text" class="w-3 h-3 text-secondary/40 dark:text-white/40 flex-shrink-0"></i>' : ''}
                        <span class="font-medium truncate">${escapeHtml(Format.name(r['poc.first_name'], r['poc.last_name']))}</span>
                      </div>
                      ${r['poc.email'] ? `<p class="text-xs text-secondary/50 dark:text-white/50 truncate">${escapeHtml(r['poc.email'])}</p>` : ''}
                    </div>
                  </div>
                </td>
                <td class="text-secondary/70 dark:text-white/70 hide-mobile">
                  <span class="truncate block max-w-[150px]">${escapeHtml(Format.truncate(r['poc.role'], 30) || '-')}</span>
                </td>
                <td>
                  <span class="truncate block max-w-[180px]">${escapeHtml(r['fund.title'] || '-')}</span>
                </td>
                <td>
                  <span class="badge text-xs">${escapeHtml(r['fund.type'] || '-')}</span>
                </td>
                <td>
                  <div class="flex items-center gap-2">
                    ${Format.flag(r['fund.country'])}
                    <span class="text-sm">${escapeHtml(r['fund.city'] || Format.countryName(r['fund.country']) || '-')}</span>
                  </div>
                </td>
                <td class="text-right font-medium tabular-nums">${Format.currency(r['fund.aum.value'])}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
      ${records.length > displayCount ? `
        <div class="text-center py-4">
          <button id="load-more-btn" class="btn btn-ghost">
            Load more (${records.length - displayCount} remaining)
          </button>
        </div>
      ` : ''}
    `;
  }

  function renderCards(records) {
    if (records.length === 0) {
      return `
        <div class="empty-state">
          <i data-feather="users" class="w-12 h-12"></i>
          <p class="text-lg font-medium mt-2">No investors found</p>
          <p class="text-sm">Try adjusting your search or filters</p>
          <button class="btn btn-primary mt-4" onclick="State.clearFilters(); Router.renderPage('list');">
            Clear Filters
          </button>
        </div>
      `;
    }

    const displayRecords = records.slice(0, displayCount);

    return `
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        ${displayRecords.map(r => `
          <div class="card cursor-pointer hover:shadow-lg transition-shadow" data-poc-id="${r['poc.id']}">
            <div class="flex items-start justify-between mb-3">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center font-medium text-primary-700 flex-shrink-0">
                  ${Format.initials(r['poc.first_name'], r['poc.last_name'])}
                </div>
                <div class="min-w-0">
                  <p class="font-medium truncate">${escapeHtml(Format.name(r['poc.first_name'], r['poc.last_name']))}</p>
                  <p class="text-sm text-secondary/60 dark:text-white/60 truncate">${escapeHtml(Format.truncate(r['poc.role'], 25) || '-')}</p>
                </div>
              </div>
              <div class="flex items-center gap-1 flex-shrink-0">
                ${State.getNote(r['poc.id']) ? '<i data-feather="file-text" class="w-3 h-3 text-secondary/40 dark:text-white/40"></i>' : ''}
                ${State.isStarred(r['poc.id']) ? '<i data-feather="star" class="w-4 h-4 text-primary fill-current"></i>' : ''}
              </div>
            </div>
            <p class="text-sm font-medium mb-2 truncate">${escapeHtml(r['fund.title'] || '-')}</p>
            <div class="flex items-center gap-2 text-sm text-secondary/60 dark:text-white/60 mb-3">
              ${Format.flag(r['fund.country'])}
              <span class="truncate">${Format.location(r['fund.country'], r['fund.city'])}</span>
            </div>
            <div class="flex items-center justify-between pt-2 border-t border-secondary/5 dark:border-white/5">
              <span class="badge text-xs">${escapeHtml(r['fund.type'] || '-')}</span>
              <span class="font-medium text-sm">${Format.currency(r['fund.aum.value'])}</span>
            </div>
            ${r['poc.email'] ? `
              <div class="mt-2 pt-2 border-t border-secondary/5 dark:border-white/5">
                <p class="text-xs text-secondary/50 dark:text-white/50 truncate">
                  <i data-feather="mail" class="w-3 h-3 inline mr-1"></i>
                  ${escapeHtml(r['poc.email'])}
                </p>
              </div>
            ` : ''}
          </div>
        `).join('')}
      </div>
      ${records.length > displayCount ? `
        <div class="text-center py-4">
          <button id="load-more-btn" class="btn btn-ghost">
            Load more (${records.length - displayCount} remaining)
          </button>
        </div>
      ` : ''}
    `;
  }

  function openSaveListModal(records) {
    const content = `
      <div class="space-y-4">
        <p class="text-sm text-secondary/60 dark:text-white/60">
          Save ${records.length} investors to a new list
        </p>
        <input
          type="text"
          id="save-list-name"
          class="input"
          placeholder="List name (e.g., 'US Family Offices')"
          autofocus
        >
        <div class="flex justify-end gap-2">
          <button id="cancel-save" class="btn btn-ghost">Cancel</button>
          <button id="confirm-save" class="btn btn-primary">Save List</button>
        </div>
      </div>
    `;

    Modal.open({ title: 'Save List', content, size: 'sm' });

    const nameInput = $('#save-list-name');
    const cancelBtn = $('#cancel-save');
    const confirmBtn = $('#confirm-save');

    cancelBtn?.addEventListener('click', Modal.close);

    confirmBtn?.addEventListener('click', async () => {
      const name = nameInput?.value?.trim();
      if (!name) {
        Toast.error('Please enter a name');
        nameInput?.focus();
        return;
      }

      const recordIds = records.map(r => r['poc.id']);
      await Store.saveList(name, recordIds);

      // Refresh user data
      const userData = await Store.loadUserData();
      State.set('userData', userData);

      Modal.close();
      Toast.success(`Saved "${name}" with ${recordIds.length} investors`);
    });

    // Enter key to save
    nameInput?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        confirmBtn?.click();
      }
    });
  }

  // Register page
  Router.registerPage('list', render);
})();

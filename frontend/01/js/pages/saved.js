/**
 * Klar - Saved Lists Page
 * Placeholder - Full implementation in Phase 4
 */

(function() {
  function render(container) {
    const subTab = State.get('savedSubTab') || 'saved';

    container.innerHTML = `
      <div class="p-4 sm:p-6">
        <h1 class="text-2xl font-semibold mb-6">Saved</h1>

        <!-- Sub-tabs -->
        <div id="saved-subtabs" class="mb-6"></div>

        <!-- Content -->
        <div id="saved-content"></div>
      </div>
    `;

    // Render sub-tabs
    const subTabsContainer = $('#saved-subtabs', container);
    const tabs = Tabs.createSubTabs([
      { id: 'saved', label: 'Saved Lists' },
      { id: 'notes', label: 'With Notes' },
      { id: 'starred', label: 'Starred' },
      { id: 'recent', label: 'Recent' }
    ], subTab, (newTab) => {
      State.set('savedSubTab', newTab);
      renderContent(container);
    });
    subTabsContainer.appendChild(tabs);

    // Render content
    renderContent(container);
  }

  function renderContent(container) {
    const contentContainer = $('#saved-content', container);
    const subTab = State.get('savedSubTab') || 'saved';

    switch (subTab) {
      case 'saved':
        renderSavedLists(contentContainer);
        break;
      case 'notes':
        renderWithNotes(contentContainer);
        break;
      case 'starred':
        renderStarred(contentContainer);
        break;
      case 'recent':
        renderRecent(contentContainer);
        break;
    }

    // Update feather icons
    if (window.feather) {
      feather.replace();
    }
  }

  function renderSavedLists(container) {
    const savedLists = State.get('userData')?.savedLists || [];

    if (savedLists.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <i data-feather="bookmark"></i>
          <p class="text-lg font-medium mt-2">No saved lists yet</p>
          <p class="text-sm">Filter investors and click "Save current list" to create one</p>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        ${savedLists.map(list => `
          <div class="card">
            <div class="flex items-start justify-between mb-2">
              <h3 class="font-medium">${escapeHtml(list.label)}</h3>
              <button class="btn btn-icon btn-ghost btn-sm" data-delete="${list.id}" title="Delete">
                <i data-feather="trash-2" class="w-4 h-4"></i>
              </button>
            </div>
            <p class="text-sm text-secondary/60 dark:text-white/60 mb-2">
              ${list.recordIds.length} investor${list.recordIds.length !== 1 ? 's' : ''}
            </p>
            <p class="text-xs text-secondary/40 dark:text-white/40">
              Created ${timeAgo(list.created)}
            </p>
          </div>
        `).join('')}
      </div>
    `;

    // Setup delete handlers
    $$('[data-delete]', container).forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const listId = btn.dataset.delete;
        if (confirm('Delete this saved list?')) {
          await Store.deleteList(listId);
          const userData = await Store.loadUserData();
          State.set('userData', userData);
          renderContent(container.parentElement);
          Toast.success('List deleted');
        }
      });
    });
  }

  function renderWithNotes(container) {
    const notes = State.get('userData')?.notes || {};
    const pocIds = Object.keys(notes);

    if (pocIds.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <i data-feather="file-text"></i>
          <p class="text-lg font-medium mt-2">No notes yet</p>
          <p class="text-sm">Open an investor and add notes to see them here</p>
        </div>
      `;
      return;
    }

    const records = pocIds
      .map(id => State.getRecord(id))
      .filter(Boolean);

    renderRecordList(container, records, 'notes');
  }

  function renderStarred(container) {
    const starred = State.get('userData')?.starred || [];

    if (starred.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <i data-feather="star"></i>
          <p class="text-lg font-medium mt-2">No starred investors</p>
          <p class="text-sm">Star investors to quickly find them later</p>
        </div>
      `;
      return;
    }

    const records = starred
      .map(id => State.getRecord(id))
      .filter(Boolean);

    renderRecordList(container, records, 'starred');
  }

  function renderRecent(container) {
    const recent = State.get('userData')?.recent || [];

    if (recent.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <i data-feather="clock"></i>
          <p class="text-lg font-medium mt-2">No recent activity</p>
          <p class="text-sm">Investors you view will appear here</p>
        </div>
      `;
      return;
    }

    const records = recent
      .map(item => {
        const record = State.getRecord(item.id);
        if (record) {
          return { ...record, _viewedAt: item.ts };
        }
        return null;
      })
      .filter(Boolean);

    container.innerHTML = `
      <div class="flex justify-end mb-4">
        <button class="btn btn-sm btn-ghost" id="clear-recent">
          <i data-feather="trash-2" class="w-4 h-4"></i>
          Clear history
        </button>
      </div>
    `;

    const listContainer = document.createElement('div');
    renderRecordList(listContainer, records, 'recent');
    container.appendChild(listContainer);

    // Clear recent handler
    $('#clear-recent', container)?.addEventListener('click', async () => {
      if (confirm('Clear recent history?')) {
        await Store.clearRecent();
        const userData = await Store.loadUserData();
        State.set('userData', userData);
        renderContent(container.parentElement);
        Toast.success('History cleared');
      }
    });
  }

  function renderRecordList(container, records, type) {
    container.innerHTML = `
      <div class="space-y-2">
        ${records.map(r => `
          <div class="card flex items-center gap-4 cursor-pointer" data-poc-id="${r['poc.id']}">
            <div class="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center font-medium text-primary-700 flex-shrink-0">
              ${Format.initials(r['poc.first_name'], r['poc.last_name'])}
            </div>
            <div class="flex-1 min-w-0">
              <p class="font-medium truncate">${escapeHtml(Format.name(r['poc.first_name'], r['poc.last_name']))}</p>
              <p class="text-sm text-secondary/60 dark:text-white/60 truncate">${escapeHtml(r['fund.title'] || '-')}</p>
              ${type === 'notes' ? `
                <p class="text-xs text-secondary/40 dark:text-white/40 truncate mt-1">
                  ${escapeHtml(Format.truncate(State.getNote(r['poc.id']), 50))}
                </p>
              ` : ''}
              ${type === 'recent' && r._viewedAt ? `
                <p class="text-xs text-secondary/40 dark:text-white/40 mt-1">
                  Viewed ${timeAgo(r._viewedAt)}
                </p>
              ` : ''}
            </div>
            <div class="flex items-center gap-2">
              ${Format.flag(r['fund.country'])}
            </div>
          </div>
        `).join('')}
      </div>
    `;

    // Click handlers
    $$('[data-poc-id]', container).forEach(el => {
      el.addEventListener('click', () => {
        Toast.info('Detail view coming soon');
      });
    });
  }

  // Register page
  Router.registerPage('saved', render);
})();

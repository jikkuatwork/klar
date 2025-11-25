/**
 * Klar - Filter Panel Component
 */

const Filters = (function() {
  let isOpen = false;

  /**
   * Render filter panel
   */
  function render(container) {
    const filters = State.get('filters');
    const records = State.get('records');

    // Get unique values for dropdowns
    const fundTypes = State.getUniqueValues('fund.type');
    const countries = State.getUniqueValues('fund.country');
    const sectors = State.getUniqueValues('fund.sectors');
    const stages = State.getUniqueValues('fund.preferred_stage').filter(s => s);

    const hasActiveFilters =
      filters.fundType?.length > 0 ||
      filters.country?.length > 0 ||
      filters.sector?.length > 0 ||
      filters.stage?.length > 0 ||
      filters.aumMin !== null ||
      filters.aumMax !== null ||
      filters.hasEmail;

    container.innerHTML = `
      <div class="bg-white dark:bg-secondary-600 border-b border-secondary/10 dark:border-white/10">
        <!-- Filter Toggle Button (Mobile) -->
        <div class="sm:hidden p-3 flex items-center justify-between">
          <button id="filter-toggle" class="btn btn-sm btn-ghost flex items-center gap-2">
            <i data-feather="filter" class="w-4 h-4"></i>
            Filters
            ${hasActiveFilters ? '<span class="w-2 h-2 rounded-full bg-primary"></span>' : ''}
          </button>
          ${hasActiveFilters ? `
            <button id="clear-filters-mobile" class="btn btn-sm btn-ghost text-red-500">
              Clear
            </button>
          ` : ''}
        </div>

        <!-- Filter Panel -->
        <div id="filter-panel" class="${isOpen ? '' : 'hidden sm:block'} p-4 border-t sm:border-t-0 border-secondary/10 dark:border-white/10">
          <div class="flex flex-wrap gap-3 items-end">

            <!-- Fund Type -->
            <div class="w-full sm:w-auto">
              <label class="block text-xs font-medium text-secondary/60 dark:text-white/60 mb-1">Fund Type</label>
              <select id="filter-fund-type" class="input text-sm py-1.5">
                <option value="">All Types</option>
                ${fundTypes.map(t => `
                  <option value="${escapeHtml(t)}" ${filters.fundType?.includes(t) ? 'selected' : ''}>
                    ${escapeHtml(t)}
                  </option>
                `).join('')}
              </select>
            </div>

            <!-- Country -->
            <div class="w-full sm:w-auto">
              <label class="block text-xs font-medium text-secondary/60 dark:text-white/60 mb-1">Country</label>
              <select id="filter-country" class="input text-sm py-1.5">
                <option value="">All Countries</option>
                ${countries.map(c => `
                  <option value="${escapeHtml(c)}" ${filters.country?.includes(c) ? 'selected' : ''}>
                    ${Format.countryName(c)} (${c})
                  </option>
                `).join('')}
              </select>
            </div>

            <!-- Sector -->
            <div class="w-full sm:w-auto">
              <label class="block text-xs font-medium text-secondary/60 dark:text-white/60 mb-1">Sector</label>
              <select id="filter-sector" class="input text-sm py-1.5">
                <option value="">All Sectors</option>
                ${sectors.slice(0, 30).map(s => `
                  <option value="${escapeHtml(s)}" ${filters.sector?.includes(s) ? 'selected' : ''}>
                    ${Format.sectorName(s)}
                  </option>
                `).join('')}
              </select>
            </div>

            <!-- Stage -->
            ${stages.length > 0 ? `
              <div class="w-full sm:w-auto">
                <label class="block text-xs font-medium text-secondary/60 dark:text-white/60 mb-1">Stage</label>
                <select id="filter-stage" class="input text-sm py-1.5">
                  <option value="">All Stages</option>
                  ${stages.map(s => `
                    <option value="${escapeHtml(s)}" ${filters.stage?.includes(s) ? 'selected' : ''}>
                      ${escapeHtml(s)}
                    </option>
                  `).join('')}
                </select>
              </div>
            ` : ''}

            <!-- AUM Range -->
            <div class="w-full sm:w-auto">
              <label class="block text-xs font-medium text-secondary/60 dark:text-white/60 mb-1">AUM Range</label>
              <select id="filter-aum" class="input text-sm py-1.5">
                <option value="">Any AUM</option>
                <option value="0-100000000" ${filters.aumMax === 100000000 && !filters.aumMin ? 'selected' : ''}>Under $100M</option>
                <option value="100000000-500000000" ${filters.aumMin === 100000000 && filters.aumMax === 500000000 ? 'selected' : ''}>$100M - $500M</option>
                <option value="500000000-1000000000" ${filters.aumMin === 500000000 && filters.aumMax === 1000000000 ? 'selected' : ''}>$500M - $1B</option>
                <option value="1000000000-10000000000" ${filters.aumMin === 1000000000 && filters.aumMax === 10000000000 ? 'selected' : ''}>$1B - $10B</option>
                <option value="10000000000-" ${filters.aumMin === 10000000000 && !filters.aumMax ? 'selected' : ''}>Over $10B</option>
              </select>
            </div>

            <!-- Has Email -->
            <div class="flex items-center gap-2">
              <input type="checkbox" id="filter-has-email" class="w-4 h-4 rounded border-secondary/30" ${filters.hasEmail ? 'checked' : ''}>
              <label for="filter-has-email" class="text-sm">Has Email</label>
            </div>

            <!-- Clear Filters -->
            ${hasActiveFilters ? `
              <button id="clear-filters" class="btn btn-sm btn-ghost text-red-500 hidden sm:flex">
                <i data-feather="x" class="w-4 h-4"></i>
                Clear
              </button>
            ` : ''}
          </div>
        </div>
      </div>
    `;

    // Setup event handlers
    setupHandlers(container);

    // Update feather icons
    if (window.feather) {
      feather.replace();
    }
  }

  /**
   * Setup filter event handlers
   */
  function setupHandlers(container) {
    // Mobile toggle
    $('#filter-toggle', container)?.addEventListener('click', () => {
      isOpen = !isOpen;
      const panel = $('#filter-panel', container);
      if (panel) {
        panel.classList.toggle('hidden', !isOpen);
      }
    });

    // Fund Type
    $('#filter-fund-type', container)?.addEventListener('change', (e) => {
      const value = e.target.value;
      updateFilter('fundType', value ? [value] : []);
    });

    // Country
    $('#filter-country', container)?.addEventListener('change', (e) => {
      const value = e.target.value;
      updateFilter('country', value ? [value] : []);
    });

    // Sector
    $('#filter-sector', container)?.addEventListener('change', (e) => {
      const value = e.target.value;
      updateFilter('sector', value ? [value] : []);
    });

    // Stage
    $('#filter-stage', container)?.addEventListener('change', (e) => {
      const value = e.target.value;
      updateFilter('stage', value ? [value] : []);
    });

    // AUM Range
    $('#filter-aum', container)?.addEventListener('change', (e) => {
      const value = e.target.value;
      if (value) {
        const [min, max] = value.split('-').map(v => v ? parseInt(v) : null);
        State.update({
          'filters.aumMin': min,
          'filters.aumMax': max
        });
      } else {
        State.update({
          'filters.aumMin': null,
          'filters.aumMax': null
        });
      }
      notifyFilterChange();
    });

    // Has Email
    $('#filter-has-email', container)?.addEventListener('change', (e) => {
      updateFilter('hasEmail', e.target.checked);
    });

    // Clear Filters
    $('#clear-filters', container)?.addEventListener('click', clearAllFilters);
    $('#clear-filters-mobile', container)?.addEventListener('click', clearAllFilters);
  }

  /**
   * Update a single filter value
   */
  function updateFilter(key, value) {
    const filters = State.get('filters');
    filters[key] = value;
    State.set('filters', filters);
    notifyFilterChange();
  }

  /**
   * Clear all filters
   */
  function clearAllFilters() {
    State.clearFilters();
    notifyFilterChange();
  }

  /**
   * Notify that filters changed (triggers re-render)
   */
  function notifyFilterChange() {
    // Dispatch custom event that list page can listen to
    document.dispatchEvent(new CustomEvent('filtersChanged'));
  }

  /**
   * Get active filter count
   */
  function getActiveCount() {
    const filters = State.get('filters');
    let count = 0;
    if (filters.fundType?.length > 0) count++;
    if (filters.country?.length > 0) count++;
    if (filters.sector?.length > 0) count++;
    if (filters.stage?.length > 0) count++;
    if (filters.aumMin !== null || filters.aumMax !== null) count++;
    if (filters.hasEmail) count++;
    return count;
  }

  // Public API
  return {
    render,
    clearAllFilters,
    getActiveCount
  };
})();

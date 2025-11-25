/**
 * Klar - In-Memory State Management
 * Simple reactive state with subscription support
 */

const State = (function() {
  // Global application state
  let state = {
    // Data
    records: [],           // Merged CSV + user additions
    userData: null,        // User overlay from IndexedDB

    // UI State
    loading: true,
    activeTab: 'dashboard',
    searchQuery: '',
    filters: {
      fundType: [],
      country: [],
      sector: [],
      stage: [],
      aumMin: null,
      aumMax: null,
      hasEmail: false
    },
    sort: {
      field: 'poc.last_name',
      direction: 'asc'
    },
    listView: 'table',

    // Saved Lists sub-tab
    savedSubTab: 'saved',  // 'saved' | 'notes' | 'starred' | 'recent'

    // Selected records for bulk actions
    selectedIds: new Set(),

    // Modal state
    modalOpen: false,
    modalData: null
  };

  // Subscribers for state changes
  const subscribers = new Set();

  /**
   * Get current state (returns a shallow copy)
   */
  function get(path) {
    if (!path) return { ...state };

    const parts = path.split('.');
    let value = state;

    for (const part of parts) {
      if (value === undefined || value === null) return undefined;
      value = value[part];
    }

    return value;
  }

  /**
   * Set state value at path and notify subscribers
   */
  function set(path, value) {
    const parts = path.split('.');
    const lastKey = parts.pop();
    let target = state;

    for (const part of parts) {
      if (!(part in target)) {
        target[part] = {};
      }
      target = target[part];
    }

    const oldValue = target[lastKey];
    target[lastKey] = value;

    // Notify subscribers
    notify(path, value, oldValue);
  }

  /**
   * Update multiple state values at once
   */
  function update(updates) {
    for (const [path, value] of Object.entries(updates)) {
      set(path, value);
    }
  }

  /**
   * Subscribe to state changes
   * Returns unsubscribe function
   */
  function subscribe(callback) {
    subscribers.add(callback);
    return () => subscribers.delete(callback);
  }

  /**
   * Notify all subscribers of state change
   */
  function notify(path, value, oldValue) {
    subscribers.forEach(callback => {
      try {
        callback(path, value, oldValue);
      } catch (error) {
        console.error('State subscriber error:', error);
      }
    });
  }

  /**
   * Initialize state with loaded data
   */
  function initialize(records, userData) {
    state.records = records;
    state.userData = userData;
    state.loading = false;
    state.listView = userData?.settings?.listView || 'table';

    // Apply theme
    applyTheme(userData?.settings?.theme || 'light');

    notify('initialized', true, false);
  }

  /**
   * Apply theme to document
   */
  function applyTheme(theme) {
    const html = document.documentElement;

    if (theme === 'system') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      html.classList.toggle('dark', prefersDark);
    } else {
      html.classList.toggle('dark', theme === 'dark');
    }
  }

  /**
   * Get filtered and sorted records
   */
  function getFilteredRecords() {
    let records = [...state.records];
    const { filters, searchQuery, sort } = state;

    // Apply search
    if (searchQuery && searchQuery.trim()) {
      const query = searchQuery.toLowerCase().trim();
      records = records.filter(r => {
        const name = `${r['poc.first_name'] || ''} ${r['poc.last_name'] || ''}`.toLowerCase();
        const fundTitle = (r['fund.title'] || '').toLowerCase();
        const description = (r['fund.description'] || '').toLowerCase();
        return name.includes(query) || fundTitle.includes(query) || description.includes(query);
      });
    }

    // Apply filters
    if (filters.fundType && filters.fundType.length > 0) {
      records = records.filter(r => filters.fundType.includes(r['fund.type']));
    }

    if (filters.country && filters.country.length > 0) {
      records = records.filter(r => filters.country.includes(r['fund.country']));
    }

    if (filters.sector && filters.sector.length > 0) {
      records = records.filter(r => {
        const sectors = (r['fund.sectors'] || '').split(';').map(s => s.trim());
        return filters.sector.some(f => sectors.includes(f));
      });
    }

    if (filters.stage && filters.stage.length > 0) {
      records = records.filter(r => filters.stage.includes(r['fund.preferred_stage']));
    }

    if (filters.aumMin !== null) {
      records = records.filter(r => {
        const aum = parseFloat(r['fund.aum.value']);
        return !isNaN(aum) && aum >= filters.aumMin;
      });
    }

    if (filters.aumMax !== null) {
      records = records.filter(r => {
        const aum = parseFloat(r['fund.aum.value']);
        return !isNaN(aum) && aum <= filters.aumMax;
      });
    }

    if (filters.hasEmail) {
      records = records.filter(r => r['poc.email'] && r['poc.email'].trim());
    }

    // Apply sort
    if (sort.field) {
      records.sort((a, b) => {
        let aVal = a[sort.field];
        let bVal = b[sort.field];

        // Handle null/undefined
        if (aVal === null || aVal === undefined) aVal = '';
        if (bVal === null || bVal === undefined) bVal = '';

        // Numeric sort for AUM fields
        if (sort.field.includes('aum') || sort.field.includes('ticket')) {
          aVal = parseFloat(aVal) || 0;
          bVal = parseFloat(bVal) || 0;
        } else {
          aVal = String(aVal).toLowerCase();
          bVal = String(bVal).toLowerCase();
        }

        if (aVal < bVal) return sort.direction === 'asc' ? -1 : 1;
        if (aVal > bVal) return sort.direction === 'asc' ? 1 : -1;
        return 0;
      });
    }

    return records;
  }

  /**
   * Get unique values for a field (for filter options)
   */
  function getUniqueValues(field) {
    const values = new Set();

    state.records.forEach(record => {
      const value = record[field];
      if (value && value.trim()) {
        // Handle semicolon-separated values
        if (field === 'fund.sectors' || field === 'fund.geographies') {
          value.split(';').forEach(v => {
            const trimmed = v.trim();
            if (trimmed) values.add(trimmed);
          });
        } else {
          values.add(value.trim());
        }
      }
    });

    return Array.from(values).sort();
  }

  /**
   * Get a single record by POC ID
   */
  function getRecord(pocId) {
    return state.records.find(r => r['poc.id'] === pocId);
  }

  /**
   * Check if a record is starred
   */
  function isStarred(pocId) {
    return state.userData?.starred?.includes(pocId) || false;
  }

  /**
   * Get note for a record
   */
  function getNote(pocId) {
    return state.userData?.notes?.[pocId] || '';
  }

  /**
   * Update starred status in memory
   */
  function updateStarred(pocId, starred) {
    if (!state.userData) return;

    if (starred) {
      if (!state.userData.starred.includes(pocId)) {
        state.userData.starred.push(pocId);
      }
    } else {
      const index = state.userData.starred.indexOf(pocId);
      if (index > -1) {
        state.userData.starred.splice(index, 1);
      }
    }

    notify('userData.starred', state.userData.starred, null);
  }

  /**
   * Update note in memory
   */
  function updateNote(pocId, note) {
    if (!state.userData) return;

    if (note && note.trim()) {
      state.userData.notes[pocId] = note.trim();
    } else {
      delete state.userData.notes[pocId];
    }

    notify('userData.notes', state.userData.notes, null);
  }

  /**
   * Clear all filters
   */
  function clearFilters() {
    state.filters = {
      fundType: [],
      country: [],
      sector: [],
      stage: [],
      aumMin: null,
      aumMax: null,
      hasEmail: false
    };
    state.searchQuery = '';
    notify('filters', state.filters, null);
  }

  /**
   * Get aggregate stats
   */
  function getStats() {
    const records = state.records;
    const uniqueFunds = new Set(records.map(r => r['fund.id']));
    const uniqueCountries = new Set(records.filter(r => r['fund.country']).map(r => r['fund.country']));

    let totalAUM = 0;
    let recordsWithAUM = 0;
    records.forEach(r => {
      const aum = parseFloat(r['fund.aum.value']);
      if (!isNaN(aum)) {
        totalAUM += aum;
        recordsWithAUM++;
      }
    });

    const withEmail = records.filter(r => r['poc.email'] && r['poc.email'].trim()).length;
    const withNotes = Object.keys(state.userData?.notes || {}).length;
    const starred = state.userData?.starred?.length || 0;
    const savedLists = state.userData?.savedLists?.length || 0;

    return {
      totalRecords: records.length,
      uniqueFunds: uniqueFunds.size,
      uniqueCountries: uniqueCountries.size,
      totalAUM,
      recordsWithAUM,
      withEmail,
      withNotes,
      starred,
      savedLists
    };
  }

  // Public API
  return {
    get,
    set,
    update,
    subscribe,
    initialize,
    applyTheme,
    getFilteredRecords,
    getUniqueValues,
    getRecord,
    isStarred,
    getNote,
    updateStarred,
    updateNote,
    clearFilters,
    getStats
  };
})();

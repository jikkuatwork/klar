/**
 * Klar - IndexedDB Storage Layer
 * Uses idb-keyval for simple key-value storage
 */

const Store = (function() {
  // Keys for different data types
  const KEYS = {
    NOTES: 'klar_notes',
    STARRED: 'klar_starred',
    RECENT: 'klar_recent',
    SAVED_LISTS: 'klar_saved_lists',
    ADDED_RECORDS: 'klar_added_records',
    SETTINGS: 'klar_settings'
  };

  // Default values
  const DEFAULTS = {
    notes: {},           // { [poc.id]: string }
    starred: [],         // string[] of poc.ids
    recent: [],          // { id: string, ts: number }[]
    savedLists: [],      // { id, label, recordIds, created }[]
    addedRecords: [],    // Full record objects
    settings: {
      theme: 'light',    // 'light' | 'dark' | 'system'
      listView: 'table'  // 'table' | 'cards'
    }
  };

  /**
   * Get a value from storage with default fallback
   */
  async function get(key, defaultValue) {
    try {
      const value = await idbKeyval.get(key);
      return value !== undefined ? value : defaultValue;
    } catch (error) {
      console.error(`Store.get error for ${key}:`, error);
      return defaultValue;
    }
  }

  /**
   * Set a value in storage
   */
  async function set(key, value) {
    try {
      await idbKeyval.set(key, value);
      return true;
    } catch (error) {
      console.error(`Store.set error for ${key}:`, error);
      return false;
    }
  }

  /**
   * Load all user data from storage
   */
  async function loadUserData() {
    const [notes, starred, recent, savedLists, addedRecords, settings] = await Promise.all([
      get(KEYS.NOTES, DEFAULTS.notes),
      get(KEYS.STARRED, DEFAULTS.starred),
      get(KEYS.RECENT, DEFAULTS.recent),
      get(KEYS.SAVED_LISTS, DEFAULTS.savedLists),
      get(KEYS.ADDED_RECORDS, DEFAULTS.addedRecords),
      get(KEYS.SETTINGS, DEFAULTS.settings)
    ]);

    return {
      notes,
      starred,
      recent,
      savedLists,
      addedRecords,
      settings: { ...DEFAULTS.settings, ...settings }
    };
  }

  /**
   * Save notes for a POC
   */
  async function saveNote(pocId, note) {
    const notes = await get(KEYS.NOTES, DEFAULTS.notes);
    if (note && note.trim()) {
      notes[pocId] = note.trim();
    } else {
      delete notes[pocId];
    }
    return set(KEYS.NOTES, notes);
  }

  /**
   * Get note for a POC
   */
  async function getNote(pocId) {
    const notes = await get(KEYS.NOTES, DEFAULTS.notes);
    return notes[pocId] || '';
  }

  /**
   * Toggle starred status for a POC
   */
  async function toggleStarred(pocId) {
    const starred = await get(KEYS.STARRED, DEFAULTS.starred);
    const index = starred.indexOf(pocId);

    if (index === -1) {
      starred.push(pocId);
    } else {
      starred.splice(index, 1);
    }

    await set(KEYS.STARRED, starred);
    return index === -1; // Returns true if now starred
  }

  /**
   * Check if a POC is starred
   */
  async function isStarred(pocId) {
    const starred = await get(KEYS.STARRED, DEFAULTS.starred);
    return starred.includes(pocId);
  }

  /**
   * Get all starred POC IDs
   */
  async function getStarred() {
    return get(KEYS.STARRED, DEFAULTS.starred);
  }

  /**
   * Add a POC to recent history
   */
  async function addToRecent(pocId) {
    const MAX_RECENT = 50;
    let recent = await get(KEYS.RECENT, DEFAULTS.recent);

    // Remove if already exists
    recent = recent.filter(item => item.id !== pocId);

    // Add to beginning
    recent.unshift({ id: pocId, ts: Date.now() });

    // Limit to max
    if (recent.length > MAX_RECENT) {
      recent = recent.slice(0, MAX_RECENT);
    }

    return set(KEYS.RECENT, recent);
  }

  /**
   * Get recent history
   */
  async function getRecent() {
    return get(KEYS.RECENT, DEFAULTS.recent);
  }

  /**
   * Clear recent history
   */
  async function clearRecent() {
    return set(KEYS.RECENT, []);
  }

  /**
   * Save a list of records
   */
  async function saveList(label, recordIds) {
    const savedLists = await get(KEYS.SAVED_LISTS, DEFAULTS.savedLists);

    const newList = {
      id: 'sl_' + Math.random().toString(36).substring(2, 10),
      label: label.trim(),
      recordIds: [...recordIds],
      created: Date.now()
    };

    savedLists.push(newList);
    await set(KEYS.SAVED_LISTS, savedLists);

    return newList;
  }

  /**
   * Get all saved lists
   */
  async function getSavedLists() {
    return get(KEYS.SAVED_LISTS, DEFAULTS.savedLists);
  }

  /**
   * Delete a saved list
   */
  async function deleteList(listId) {
    let savedLists = await get(KEYS.SAVED_LISTS, DEFAULTS.savedLists);
    savedLists = savedLists.filter(list => list.id !== listId);
    return set(KEYS.SAVED_LISTS, savedLists);
  }

  /**
   * Rename a saved list
   */
  async function renameList(listId, newLabel) {
    const savedLists = await get(KEYS.SAVED_LISTS, DEFAULTS.savedLists);
    const list = savedLists.find(l => l.id === listId);

    if (list) {
      list.label = newLabel.trim();
      return set(KEYS.SAVED_LISTS, savedLists);
    }

    return false;
  }

  /**
   * Add a user-created record
   */
  async function addRecord(record) {
    const addedRecords = await get(KEYS.ADDED_RECORDS, DEFAULTS.addedRecords);

    // Ensure the record has required IDs
    if (!record['poc.id']) {
      record['poc.id'] = 'u_' + Math.random().toString(36).substring(2, 10);
    }
    if (!record['fund.id']) {
      record['fund.id'] = 'uf_' + Math.random().toString(36).substring(2, 10);
    }

    // Mark as user-added
    record._isUserAdded = true;
    record._addedAt = Date.now();

    addedRecords.push(record);
    await set(KEYS.ADDED_RECORDS, addedRecords);

    return record;
  }

  /**
   * Update a user-created record
   */
  async function updateRecord(pocId, updates) {
    const addedRecords = await get(KEYS.ADDED_RECORDS, DEFAULTS.addedRecords);
    const index = addedRecords.findIndex(r => r['poc.id'] === pocId);

    if (index !== -1) {
      addedRecords[index] = { ...addedRecords[index], ...updates };
      return set(KEYS.ADDED_RECORDS, addedRecords);
    }

    return false;
  }

  /**
   * Delete a user-created record
   */
  async function deleteRecord(pocId) {
    let addedRecords = await get(KEYS.ADDED_RECORDS, DEFAULTS.addedRecords);
    addedRecords = addedRecords.filter(r => r['poc.id'] !== pocId);
    return set(KEYS.ADDED_RECORDS, addedRecords);
  }

  /**
   * Get all user-added records
   */
  async function getAddedRecords() {
    return get(KEYS.ADDED_RECORDS, DEFAULTS.addedRecords);
  }

  /**
   * Get settings
   */
  async function getSettings() {
    const settings = await get(KEYS.SETTINGS, DEFAULTS.settings);
    return { ...DEFAULTS.settings, ...settings };
  }

  /**
   * Update settings
   */
  async function updateSettings(updates) {
    const settings = await get(KEYS.SETTINGS, DEFAULTS.settings);
    const newSettings = { ...settings, ...updates };
    return set(KEYS.SETTINGS, newSettings);
  }

  /**
   * Clear all user data (with confirmation)
   */
  async function clearAllData() {
    try {
      await idbKeyval.clear();
      return true;
    } catch (error) {
      console.error('Store.clearAllData error:', error);
      return false;
    }
  }

  // Public API
  return {
    loadUserData,
    saveNote,
    getNote,
    toggleStarred,
    isStarred,
    getStarred,
    addToRecent,
    getRecent,
    clearRecent,
    saveList,
    getSavedLists,
    deleteList,
    renameList,
    addRecord,
    updateRecord,
    deleteRecord,
    getAddedRecords,
    getSettings,
    updateSettings,
    clearAllData
  };
})();

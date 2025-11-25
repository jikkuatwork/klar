/**
 * Klar - CSV Utilities
 */

const CSV = (function() {
  /**
   * Load and parse CSV file
   * @param {string} url - Path to CSV file
   * @returns {Promise<Array>} Parsed records
   */
  async function load(url) {
    return new Promise((resolve, reject) => {
      Papa.parse(url, {
        download: true,
        header: true,
        skipEmptyLines: true,
        transformHeader: header => header.trim(),
        transform: value => value ? value.trim() : '',
        complete: results => {
          if (results.errors.length > 0) {
            console.warn('CSV parse warnings:', results.errors);
          }
          resolve(results.data);
        },
        error: error => {
          console.error('CSV parse error:', error);
          reject(error);
        }
      });
    });
  }

  /**
   * Export records to CSV string
   * @param {Array} records - Records to export
   * @param {Array} fields - Fields to include (optional, all if not specified)
   * @returns {string} CSV string
   */
  function toCSV(records, fields = null) {
    if (!records || records.length === 0) {
      return '';
    }

    // Get fields from first record if not specified
    const columns = fields || Object.keys(records[0]).filter(k => !k.startsWith('_'));

    // Header row
    const rows = [columns.join(',')];

    // Data rows
    records.forEach(record => {
      const values = columns.map(col => {
        let value = record[col];

        if (value === null || value === undefined) {
          return '';
        }

        // Convert to string
        value = String(value);

        // Escape quotes and wrap in quotes if contains comma, quote, or newline
        if (value.includes(',') || value.includes('"') || value.includes('\n')) {
          value = '"' + value.replace(/"/g, '""') + '"';
        }

        return value;
      });

      rows.push(values.join(','));
    });

    return rows.join('\n');
  }

  /**
   * Export filtered records with user notes
   * @param {Array} records - Records to export
   * @returns {string} CSV string
   */
  function exportWithNotes(records) {
    // Add poc.notes column
    const enrichedRecords = records.map(r => ({
      ...r,
      'poc.notes': State.getNote(r['poc.id']) || ''
    }));

    // Get all original fields plus poc.notes
    const fields = [
      'poc.id', 'fund.id',
      'poc.first_name', 'poc.last_name', 'poc.role', 'poc.email', 'poc.phone', 'poc.linkedin', 'poc.description', 'poc.notes',
      'fund.title', 'fund.type', 'fund.email', 'fund.phone', 'fund.website', 'fund.linkedin', 'fund.crunchbase',
      'fund.country', 'fund.city', 'fund.sectors', 'fund.preferred_stage',
      'fund.description', 'fund.thesis', 'fund.portfolio_companies', 'fund.geographies',
      'fund.aum.value', 'fund.aum.year', 'fund.ticket.min', 'fund.ticket.max'
    ];

    return toCSV(enrichedRecords, fields);
  }

  /**
   * Download records as CSV file
   * @param {Array} records - Records to export
   * @param {string} filename - Filename (without extension)
   * @param {boolean} includeNotes - Include user notes
   */
  function download(records, filename = 'klar-export', includeNotes = true) {
    const csvContent = includeNotes ? exportWithNotes(records) : toCSV(records);
    const date = new Date().toISOString().split('T')[0];
    const fullFilename = `${filename}-${date}.csv`;

    downloadFile(csvContent, fullFilename, 'text/csv;charset=utf-8;');
  }

  /**
   * Parse portfolio companies JSON-like string
   * @param {string} str - Portfolio companies string
   * @returns {Array} Parsed companies
   */
  function parsePortfolioCompanies(str) {
    if (!str || typeof str !== 'string') return [];

    const companies = [];

    // Try to parse as JSON-like format
    // Format: {'name': 'X', 'website': 'Y', 'sector': 'Z', 'description': 'W'}; ...
    const regex = /\{[^}]+\}/g;
    const matches = str.match(regex);

    if (matches) {
      matches.forEach(match => {
        try {
          // Convert Python-style dict to JSON
          const jsonStr = match
            .replace(/'/g, '"')
            .replace(/None/g, 'null');
          const company = JSON.parse(jsonStr);
          companies.push(company);
        } catch (e) {
          // If parsing fails, just skip
        }
      });
    }

    return companies;
  }

  // Public API
  return {
    load,
    toCSV,
    exportWithNotes,
    download,
    parsePortfolioCompanies
  };
})();

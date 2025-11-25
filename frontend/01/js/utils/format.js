/**
 * Klar - Formatting Utilities
 */

const Format = (function() {
  /**
   * Format currency with abbreviation
   * e.g., 1500000000 -> "$1.5B"
   */
  function currency(value, includeSymbol = true) {
    if (value === null || value === undefined || value === '') return '-';

    const num = parseFloat(value);
    if (isNaN(num)) return '-';

    const symbol = includeSymbol ? '$' : '';

    if (num >= 1e12) {
      return `${symbol}${(num / 1e12).toFixed(1)}T`;
    }
    if (num >= 1e9) {
      return `${symbol}${(num / 1e9).toFixed(1)}B`;
    }
    if (num >= 1e6) {
      return `${symbol}${(num / 1e6).toFixed(1)}M`;
    }
    if (num >= 1e3) {
      return `${symbol}${(num / 1e3).toFixed(0)}K`;
    }

    return `${symbol}${num.toLocaleString()}`;
  }

  /**
   * Format full currency (no abbreviation)
   */
  function currencyFull(value) {
    if (value === null || value === undefined || value === '') return '-';

    const num = parseFloat(value);
    if (isNaN(num)) return '-';

    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0
    }).format(num);
  }

  /**
   * Format person name
   */
  function name(firstName, lastName) {
    const parts = [firstName, lastName].filter(Boolean);
    return parts.length > 0 ? parts.join(' ') : '-';
  }

  /**
   * Format full name with title/role
   */
  function nameWithRole(firstName, lastName, role) {
    const fullName = name(firstName, lastName);
    if (role && role.trim()) {
      return `${fullName} - ${role}`;
    }
    return fullName;
  }

  /**
   * Get initials from name
   */
  function initials(firstName, lastName) {
    const first = (firstName || '')[0] || '';
    const last = (lastName || '')[0] || '';
    return (first + last).toUpperCase() || '?';
  }

  /**
   * Parse semicolon-separated string to array
   */
  function toArray(str) {
    if (!str || typeof str !== 'string') return [];
    return str.split(';').map(s => s.trim()).filter(Boolean);
  }

  /**
   * Format array as comma-separated string
   */
  function fromArray(arr, limit = null) {
    if (!Array.isArray(arr) || arr.length === 0) return '-';

    if (limit && arr.length > limit) {
      return `${arr.slice(0, limit).join(', ')} +${arr.length - limit} more`;
    }

    return arr.join(', ');
  }

  /**
   * Country code to name
   */
  const COUNTRIES = {
    AD: 'Andorra', AE: 'UAE', AF: 'Afghanistan', AT: 'Austria', AU: 'Australia',
    BE: 'Belgium', BH: 'Bahrain', BR: 'Brazil', CA: 'Canada', CH: 'Switzerland',
    CN: 'China', DE: 'Germany', DK: 'Denmark', EG: 'Egypt', ES: 'Spain',
    FI: 'Finland', FR: 'France', GB: 'UK', HK: 'Hong Kong', IL: 'Israel',
    IN: 'India', IT: 'Italy', JP: 'Japan', KR: 'South Korea', KW: 'Kuwait',
    LT: 'Lithuania', LU: 'Luxembourg', MC: 'Monaco', MX: 'Mexico', NL: 'Netherlands',
    NO: 'Norway', NZ: 'New Zealand', PL: 'Poland', PT: 'Portugal', QA: 'Qatar',
    RO: 'Romania', SA: 'Saudi Arabia', SE: 'Sweden', SG: 'Singapore', TW: 'Taiwan',
    UK: 'United Kingdom', US: 'United States', ZA: 'South Africa'
  };

  function countryName(code) {
    if (!code) return '-';
    return COUNTRIES[code.toUpperCase()] || code;
  }

  /**
   * Get flag HTML (using flag-icons CSS)
   */
  function flag(countryCode, size = '') {
    if (!countryCode) return '';
    // flag-icons uses lowercase 2-letter codes
    // UK should be gb for the flag
    let code = countryCode.toLowerCase();
    if (code === 'uk') code = 'gb';

    const sizeClass = size === 'lg' ? 'fi-lg' : '';
    return `<span class="fi fi-${code} ${sizeClass}" title="${countryName(countryCode)}"></span>`;
  }

  /**
   * Format location (country + city)
   */
  function location(country, city) {
    const parts = [];
    if (city) parts.push(city);
    if (country) parts.push(countryName(country));
    return parts.length > 0 ? parts.join(', ') : '-';
  }

  /**
   * Truncate text with ellipsis
   */
  function truncate(str, maxLength = 100) {
    if (!str) return '';
    if (str.length <= maxLength) return str;
    return str.slice(0, maxLength).trim() + '...';
  }

  /**
   * Format date
   */
  function date(timestamp, style = 'medium') {
    if (!timestamp) return '-';

    const d = new Date(timestamp);
    if (isNaN(d.getTime())) return '-';

    const options = {
      short: { month: 'numeric', day: 'numeric', year: '2-digit' },
      medium: { month: 'short', day: 'numeric', year: 'numeric' },
      long: { month: 'long', day: 'numeric', year: 'numeric' }
    };

    return d.toLocaleDateString('en-US', options[style] || options.medium);
  }

  /**
   * Format URL for display (remove protocol, trailing slash)
   */
  function displayUrl(url) {
    if (!url) return '-';
    return url.replace(/^https?:\/\//, '').replace(/\/$/, '');
  }

  /**
   * Ensure URL has protocol
   */
  function ensureProtocol(url) {
    if (!url) return '';
    if (url.startsWith('http://') || url.startsWith('https://')) {
      return url;
    }
    return 'https://' + url;
  }

  /**
   * Format phone number
   */
  function phone(value) {
    if (!value) return '-';
    // Just return as-is since formats vary internationally
    return value;
  }

  /**
   * Format email as mailto link
   */
  function emailLink(email) {
    if (!email) return '-';
    return `<a href="mailto:${escapeHtml(email)}" class="text-primary hover:underline">${escapeHtml(email)}</a>`;
  }

  /**
   * Format external link
   */
  function externalLink(url, text = null) {
    if (!url) return '-';
    const displayText = text || displayUrl(url);
    return `<a href="${ensureProtocol(escapeHtml(url))}" target="_blank" rel="noopener noreferrer" class="text-primary hover:underline">${escapeHtml(displayText)}</a>`;
  }

  /**
   * Format AUM range (ticket size)
   */
  function ticketRange(min, max) {
    const minStr = min ? currency(min) : null;
    const maxStr = max ? currency(max) : null;

    if (minStr && maxStr) {
      return `${minStr} - ${maxStr}`;
    }
    if (minStr) {
      return `${minStr}+`;
    }
    if (maxStr) {
      return `Up to ${maxStr}`;
    }
    return '-';
  }

  /**
   * Sector name formatting (kebab-case to Title Case)
   */
  const SECTOR_SPECIAL_CASES = {
    'ai-ml': 'AI/ML',
    'saas': 'SaaS',
    'esg': 'ESG',
    'ecommerce': 'eCommerce',
    'fintech': 'FinTech',
    'healthtech': 'HealthTech',
    'cleantech': 'CleanTech',
    'biotech': 'BioTech',
    'edtech': 'EdTech',
    'proptech': 'PropTech',
    'regtech': 'RegTech',
    'insurtech': 'InsurTech',
    'agtech': 'AgTech',
    'iot': 'IoT',
    'ar-vr': 'AR/VR',
    'b2b': 'B2B',
    'b2c': 'B2C',
    'd2c': 'D2C'
  };

  function sectorName(sector) {
    if (!sector) return '';

    // Check for special cases first
    const lower = sector.toLowerCase();
    if (SECTOR_SPECIAL_CASES[lower]) {
      return SECTOR_SPECIAL_CASES[lower];
    }

    // Default: convert kebab-case to Title Case
    return sector
      .split('-')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }

  // Public API
  return {
    currency,
    currencyFull,
    name,
    nameWithRole,
    initials,
    toArray,
    fromArray,
    countryName,
    flag,
    location,
    truncate,
    date,
    displayUrl,
    ensureProtocol,
    phone,
    emailLink,
    externalLink,
    ticketRange,
    sectorName
  };
})();

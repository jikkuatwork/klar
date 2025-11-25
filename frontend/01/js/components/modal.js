/**
 * Klar - Modal Component
 */

const Modal = (function() {
  let currentModal = null;
  let onCloseCallback = null;

  /**
   * Open a modal with content
   */
  function open(options = {}) {
    const {
      title = '',
      content = '',
      size = 'md', // 'sm', 'md', 'lg', 'full'
      onClose = null
    } = options;

    onCloseCallback = onClose;

    // Remove existing modal
    close();

    const sizeClasses = {
      sm: 'max-w-sm',
      md: 'max-w-xl',
      lg: 'max-w-3xl',
      full: 'max-w-full'
    };

    const modal = html(`
      <div class="fixed inset-0 z-50" role="dialog" aria-modal="true">
        <!-- Backdrop -->
        <div class="modal-backdrop" id="modal-backdrop"></div>

        <!-- Modal Panel -->
        <div class="modal-content ${sizeClasses[size] || sizeClasses.md}">
          <!-- Header -->
          <div class="sticky top-0 z-10 flex items-center justify-between px-4 py-3 bg-white dark:bg-secondary border-b border-secondary/10 dark:border-white/10">
            <h2 class="text-lg font-semibold truncate">${escapeHtml(title)}</h2>
            <button id="modal-close" class="btn btn-icon btn-ghost" aria-label="Close">
              <i data-feather="x" class="w-5 h-5"></i>
            </button>
          </div>

          <!-- Content -->
          <div class="p-4" id="modal-body">
            ${content}
          </div>
        </div>
      </div>
    `);

    document.body.appendChild(modal);
    document.body.classList.add('overflow-hidden');
    currentModal = modal;

    // Setup close handlers
    $('#modal-backdrop', modal).addEventListener('click', close);
    $('#modal-close', modal).addEventListener('click', close);

    // Close on Escape key
    document.addEventListener('keydown', handleEscape);

    // Update feather icons
    if (window.feather) {
      feather.replace();
    }

    return modal;
  }

  /**
   * Open detail modal for a record
   */
  async function openDetail(pocId) {
    const record = State.getRecord(pocId);
    if (!record) {
      Toast.error('Record not found');
      return;
    }

    // Add to recent
    await Store.addToRecent(pocId);
    const userData = State.get('userData');
    if (!userData.recent.some(r => r.id === pocId)) {
      userData.recent.unshift({ id: pocId, ts: Date.now() });
      State.set('userData', userData);
    }

    const isStarred = State.isStarred(pocId);
    const note = State.getNote(pocId);

    const content = `
      <div class="space-y-6">
        <!-- POC Header -->
        <div class="flex items-start gap-4">
          <div class="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center text-xl font-semibold text-primary-700 flex-shrink-0">
            ${Format.initials(record['poc.first_name'], record['poc.last_name'])}
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <h3 class="text-xl font-semibold">${escapeHtml(Format.name(record['poc.first_name'], record['poc.last_name']))}</h3>
              <button id="star-btn" class="btn btn-icon btn-ghost ${isStarred ? 'text-primary' : ''}" data-poc-id="${pocId}">
                <i data-feather="star" class="w-5 h-5 ${isStarred ? 'fill-current' : ''}"></i>
              </button>
            </div>
            <p class="text-secondary/60 dark:text-white/60">${escapeHtml(record['poc.role'] || '-')}</p>
          </div>
        </div>

        <!-- Contact Info -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          ${record['poc.email'] ? `
            <div class="flex items-center gap-3">
              <i data-feather="mail" class="w-4 h-4 text-secondary/40 dark:text-white/40"></i>
              <a href="mailto:${escapeHtml(record['poc.email'])}" class="text-primary hover:underline truncate">
                ${escapeHtml(record['poc.email'])}
              </a>
            </div>
          ` : ''}
          ${record['poc.phone'] ? `
            <div class="flex items-center gap-3">
              <i data-feather="phone" class="w-4 h-4 text-secondary/40 dark:text-white/40"></i>
              <span>${escapeHtml(record['poc.phone'])}</span>
            </div>
          ` : ''}
          ${record['poc.linkedin'] ? `
            <div class="flex items-center gap-3">
              <i data-feather="linkedin" class="w-4 h-4 text-secondary/40 dark:text-white/40"></i>
              <a href="${escapeHtml(record['poc.linkedin'])}" target="_blank" rel="noopener noreferrer" class="text-primary hover:underline truncate">
                LinkedIn Profile
              </a>
            </div>
          ` : ''}
        </div>

        <!-- POC Description -->
        ${record['poc.description'] ? `
          <div>
            <h4 class="text-sm font-medium text-secondary/60 dark:text-white/60 mb-2">About</h4>
            <p class="text-sm leading-relaxed">${escapeHtml(record['poc.description'])}</p>
          </div>
        ` : ''}

        <!-- Notes -->
        <div>
          <h4 class="text-sm font-medium text-secondary/60 dark:text-white/60 mb-2">Your Notes</h4>
          <textarea
            id="note-input"
            class="input min-h-[100px] resize-y"
            placeholder="Add notes about this contact..."
            data-poc-id="${pocId}"
          >${escapeHtml(note)}</textarea>
          <p class="text-xs text-secondary/40 dark:text-white/40 mt-1">Notes are saved automatically</p>
        </div>

        <hr class="border-secondary/10 dark:border-white/10">

        <!-- Fund Info -->
        <div>
          <div class="flex items-center gap-2 mb-4">
            ${Format.flag(record['fund.country'], 'lg')}
            <h3 class="text-lg font-semibold">${escapeHtml(record['fund.title'] || '-')}</h3>
            <span class="badge">${escapeHtml(record['fund.type'] || '-')}</span>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
            <div>
              <span class="text-secondary/60 dark:text-white/60">Location:</span>
              <span class="ml-2">${Format.location(record['fund.country'], record['fund.city'])}</span>
            </div>
            ${record['fund.aum.value'] ? `
              <div>
                <span class="text-secondary/60 dark:text-white/60">AUM:</span>
                <span class="ml-2 font-medium">${Format.currency(record['fund.aum.value'])}</span>
                ${record['fund.aum.year'] ? `<span class="text-secondary/40 dark:text-white/40">(${record['fund.aum.year']})</span>` : ''}
              </div>
            ` : ''}
            ${record['fund.ticket.min'] || record['fund.ticket.max'] ? `
              <div>
                <span class="text-secondary/60 dark:text-white/60">Ticket Size:</span>
                <span class="ml-2">${Format.ticketRange(record['fund.ticket.min'], record['fund.ticket.max'])}</span>
              </div>
            ` : ''}
            ${record['fund.preferred_stage'] ? `
              <div>
                <span class="text-secondary/60 dark:text-white/60">Stage:</span>
                <span class="ml-2">${escapeHtml(record['fund.preferred_stage'])}</span>
              </div>
            ` : ''}
          </div>

          <!-- Fund Contact -->
          <div class="flex flex-wrap gap-3 mt-4">
            ${record['fund.website'] ? `
              <a href="${Format.ensureProtocol(record['fund.website'])}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-ghost">
                <i data-feather="globe" class="w-4 h-4"></i>
                Website
              </a>
            ` : ''}
            ${record['fund.linkedin'] ? `
              <a href="${escapeHtml(record['fund.linkedin'])}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-ghost">
                <i data-feather="linkedin" class="w-4 h-4"></i>
                LinkedIn
              </a>
            ` : ''}
            ${record['fund.crunchbase'] ? `
              <a href="${escapeHtml(record['fund.crunchbase'])}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-ghost">
                <i data-feather="database" class="w-4 h-4"></i>
                Crunchbase
              </a>
            ` : ''}
          </div>
        </div>

        <!-- Sectors -->
        ${record['fund.sectors'] ? `
          <div>
            <h4 class="text-sm font-medium text-secondary/60 dark:text-white/60 mb-2">Sectors</h4>
            <div class="flex flex-wrap gap-2">
              ${Format.toArray(record['fund.sectors']).map(s => `
                <span class="badge">${Format.sectorName(s)}</span>
              `).join('')}
            </div>
          </div>
        ` : ''}

        <!-- Geographies -->
        ${record['fund.geographies'] ? `
          <div>
            <h4 class="text-sm font-medium text-secondary/60 dark:text-white/60 mb-2">Geographies</h4>
            <p class="text-sm">${escapeHtml(record['fund.geographies'])}</p>
          </div>
        ` : ''}

        <!-- Fund Description -->
        ${record['fund.description'] ? `
          <div>
            <h4 class="text-sm font-medium text-secondary/60 dark:text-white/60 mb-2">Fund Description</h4>
            <p class="text-sm leading-relaxed">${escapeHtml(record['fund.description'])}</p>
          </div>
        ` : ''}

        <!-- Investment Thesis -->
        ${record['fund.thesis'] ? `
          <div>
            <h4 class="text-sm font-medium text-secondary/60 dark:text-white/60 mb-2">Investment Thesis</h4>
            <p class="text-sm leading-relaxed">${escapeHtml(record['fund.thesis'])}</p>
          </div>
        ` : ''}

        <!-- Portfolio Companies -->
        ${record['fund.portfolio_companies'] ? `
          <div>
            <h4 class="text-sm font-medium text-secondary/60 dark:text-white/60 mb-2">Portfolio Companies</h4>
            ${renderPortfolioCompanies(record['fund.portfolio_companies'])}
          </div>
        ` : ''}
      </div>
    `;

    const name = Format.name(record['poc.first_name'], record['poc.last_name']);
    const modal = open({ title: name, content, size: 'lg' });

    // Setup star button
    const starBtn = $('#star-btn', modal);
    if (starBtn) {
      starBtn.addEventListener('click', async () => {
        const newStarred = await Store.toggleStarred(pocId);
        State.updateStarred(pocId, newStarred);

        // Update button appearance
        starBtn.classList.toggle('text-primary', newStarred);
        const icon = $('svg', starBtn);
        if (icon) {
          icon.classList.toggle('fill-current', newStarred);
        }

        Toast.success(newStarred ? 'Added to starred' : 'Removed from starred');
      });
    }

    // Setup note auto-save
    const noteInput = $('#note-input', modal);
    if (noteInput) {
      const saveNote = debounce(async (value) => {
        await Store.saveNote(pocId, value);
        State.updateNote(pocId, value);
        Toast.success('Note saved');
      }, 1000);

      noteInput.addEventListener('input', (e) => {
        saveNote(e.target.value);
      });
    }

    // Update feather icons
    if (window.feather) {
      feather.replace();
    }
  }

  /**
   * Render portfolio companies
   */
  function renderPortfolioCompanies(str) {
    const companies = CSV.parsePortfolioCompanies(str);

    if (companies.length === 0) {
      return `<p class="text-sm">${escapeHtml(Format.truncate(str, 500))}</p>`;
    }

    return `
      <div class="space-y-3">
        ${companies.slice(0, 5).map(c => `
          <div class="p-3 bg-secondary/5 dark:bg-white/5 rounded-lg">
            <div class="flex items-center gap-2 mb-1">
              <span class="font-medium">${escapeHtml(c.name || 'Unknown')}</span>
              ${c.website ? `
                <a href="${Format.ensureProtocol(c.website)}" target="_blank" rel="noopener noreferrer" class="text-primary hover:underline text-xs">
                  Visit
                </a>
              ` : ''}
            </div>
            ${c.sector ? `<span class="badge badge-primary text-xs">${escapeHtml(c.sector)}</span>` : ''}
            ${c.description ? `<p class="text-sm text-secondary/60 dark:text-white/60 mt-1">${escapeHtml(c.description)}</p>` : ''}
          </div>
        `).join('')}
        ${companies.length > 5 ? `
          <p class="text-sm text-secondary/40 dark:text-white/40">+${companies.length - 5} more companies</p>
        ` : ''}
      </div>
    `;
  }

  /**
   * Close the modal
   */
  function close() {
    if (currentModal) {
      // Animate out
      const panel = $('.modal-content', currentModal);
      const backdrop = $('.modal-backdrop', currentModal);

      if (panel) panel.classList.add('animate-slide-out-right');
      if (backdrop) backdrop.classList.add('animate-fade-out');

      setTimeout(() => {
        if (currentModal && currentModal.parentNode) {
          currentModal.parentNode.removeChild(currentModal);
        }
        currentModal = null;
        document.body.classList.remove('overflow-hidden');
      }, 250);

      // Remove escape handler
      document.removeEventListener('keydown', handleEscape);

      // Call onClose callback
      if (onCloseCallback) {
        onCloseCallback();
        onCloseCallback = null;
      }
    }
  }

  /**
   * Handle Escape key
   */
  function handleEscape(e) {
    if (e.key === 'Escape') {
      close();
    }
  }

  /**
   * Update modal body content
   */
  function setContent(html) {
    const body = $('#modal-body');
    if (body) {
      body.innerHTML = html;
      if (window.feather) {
        feather.replace();
      }
    }
  }

  /**
   * Check if modal is open
   */
  function isOpen() {
    return currentModal !== null;
  }

  // Public API
  return {
    open,
    openDetail,
    close,
    setContent,
    isOpen
  };
})();

/**
 * Klar - Add Record Component
 * Modal for adding new fund/POC records
 */

const AddRecord = (function() {
  /**
   * Open the add record modal
   */
  function open() {
    const content = `
      <form id="add-record-form" class="space-y-6">
        <!-- POC Section -->
        <div>
          <h3 class="text-sm font-semibold text-secondary/60 dark:text-white/60 uppercase tracking-wide mb-3">Point of Contact</h3>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium mb-1">First Name <span class="text-red-500">*</span></label>
              <input type="text" name="poc.first_name" class="input" required>
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Last Name <span class="text-red-500">*</span></label>
              <input type="text" name="poc.last_name" class="input" required>
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Role</label>
              <input type="text" name="poc.role" class="input" placeholder="e.g., Managing Partner">
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Email</label>
              <input type="email" name="poc.email" class="input" placeholder="email@example.com">
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Phone</label>
              <input type="tel" name="poc.phone" class="input" placeholder="+1 (555) 123-4567">
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">LinkedIn</label>
              <input type="url" name="poc.linkedin" class="input" placeholder="https://linkedin.com/in/...">
            </div>
          </div>
          <div class="mt-4">
            <label class="block text-sm font-medium mb-1">Description</label>
            <textarea name="poc.description" class="input min-h-[80px]" placeholder="Brief bio or notes about this person..."></textarea>
          </div>
        </div>

        <!-- Fund Section -->
        <div>
          <h3 class="text-sm font-semibold text-secondary/60 dark:text-white/60 uppercase tracking-wide mb-3">Fund Information</h3>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="sm:col-span-2">
              <label class="block text-sm font-medium mb-1">Fund Name <span class="text-red-500">*</span></label>
              <input type="text" name="fund.title" class="input" required>
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Fund Type</label>
              <select name="fund.type" class="input">
                <option value="">Select type...</option>
                <option value="Family Office">Family Office</option>
                <option value="Venture Capital">Venture Capital</option>
                <option value="Private Equity">Private Equity</option>
                <option value="Hedge Fund">Hedge Fund</option>
                <option value="Investment Bank">Investment Bank</option>
                <option value="Asset Manager">Asset Manager</option>
                <option value="Sovereign Wealth Fund">Sovereign Wealth Fund</option>
                <option value="Pension Fund">Pension Fund</option>
                <option value="Endowment">Endowment</option>
                <option value="Other">Other</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Website</label>
              <input type="url" name="fund.website" class="input" placeholder="https://...">
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">Country (ISO Code)</label>
              <input type="text" name="fund.country" class="input" maxlength="2" placeholder="US, GB, CH...">
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">City (LOCODE)</label>
              <input type="text" name="fund.city" class="input" maxlength="3" placeholder="NYC, LON, ZRH...">
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">AUM (USD)</label>
              <input type="number" name="fund.aum.value" class="input" placeholder="e.g., 500000000">
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">AUM Year</label>
              <input type="number" name="fund.aum.year" class="input" min="2000" max="2030" placeholder="${new Date().getFullYear()}">
            </div>
          </div>
          <div class="mt-4">
            <label class="block text-sm font-medium mb-1">Sectors</label>
            <input type="text" name="fund.sectors" class="input" placeholder="technology, healthcare, fintech (comma-separated)">
          </div>
          <div class="mt-4">
            <label class="block text-sm font-medium mb-1">Fund Description</label>
            <textarea name="fund.description" class="input min-h-[80px]" placeholder="Brief description of the fund..."></textarea>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex justify-end gap-3 pt-4 border-t border-secondary/10 dark:border-white/10">
          <button type="button" id="cancel-add" class="btn btn-ghost">Cancel</button>
          <button type="submit" class="btn btn-primary">
            <i data-feather="plus" class="w-4 h-4"></i>
            Add Investor
          </button>
        </div>
      </form>
    `;

    Modal.open({ title: 'Add New Investor', content, size: 'lg' });

    // Setup form handlers
    const form = $('#add-record-form');
    const cancelBtn = $('#cancel-add');

    cancelBtn?.addEventListener('click', Modal.close);

    form?.addEventListener('submit', async (e) => {
      e.preventDefault();

      const formData = new FormData(form);
      const record = {};

      // Convert form data to record object
      formData.forEach((value, key) => {
        if (value) {
          // Convert numeric fields
          if (key === 'fund.aum.value' || key === 'fund.aum.year') {
            record[key] = parseFloat(value) || null;
          } else {
            record[key] = value.trim();
          }
        }
      });

      // Validate required fields
      if (!record['poc.first_name'] || !record['poc.last_name'] || !record['fund.title']) {
        Toast.error('Please fill in all required fields');
        return;
      }

      // Normalize country code to uppercase
      if (record['fund.country']) {
        record['fund.country'] = record['fund.country'].toUpperCase();
      }

      // Normalize city code to uppercase
      if (record['fund.city']) {
        record['fund.city'] = record['fund.city'].toUpperCase();
      }

      try {
        // Save to IndexedDB
        const savedRecord = await Store.addRecord(record);

        // Update state
        const records = State.get('records');
        records.push({
          ...savedRecord,
          _note: null,
          _starred: false,
          _isUserAdded: true
        });
        State.set('records', records);

        Modal.close();
        Toast.success('Investor added successfully');

        // Open the detail modal for the new record
        setTimeout(() => {
          Modal.openDetail(savedRecord['poc.id']);
        }, 300);

      } catch (error) {
        console.error('Failed to add record:', error);
        Toast.error('Failed to add investor');
      }
    });

    if (window.feather) {
      feather.replace();
    }
  }

  // Public API
  return { open };
})();

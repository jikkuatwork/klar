# Klar - Build Plan

**Product:** Klar
**Tagline:** "Capital, Clarified."
**URL:** https://klar.toolbomber.com

**Target:** Static vanilla JS web app (no build tools)
**Output:** `frontend/01/`
**Hosting:** Vercel (static)

---

## Phase 0: Preprocessing (Run Once)

Run on host Mac: `zsh process.zsh`

This generates:
- `frontend/01/assets/favicon-16.png`, `favicon-32.png`, `favicon.ico`
- `frontend/01/assets/apple-touch-icon.png` (180px)
- `frontend/01/assets/icon-192.png`, `icon-512.png` (PWA)
- `frontend/01/assets/logo.svg` (copy)
- `frontend/01/manifest.json`
- `frontend/01/data.csv` → symlink to `../../data.csv`
- `frontend/01/assets/cities.json` (already created)

---

## Libraries (CDN)

```html
<!-- CSS -->
<script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/lipis/flag-icons@7.2.3/css/flag-icons.min.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">

<!-- JS -->
<script src="https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/idb-keyval@6/dist/umd.js"></script>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/feather-icons/dist/feather.min.js"></script>
```

---

## Theme

```
Primary:   #DEC26F (gold)
Secondary: #15213B (navy)

Light mode: white bg, navy text, gold accents
Dark mode:  navy bg, white text, gold accents
```

---

## File Structure

```
frontend/01/
├── index.html
├── manifest.json           # PWA manifest
├── data.csv → symlink      # → ../../data.csv
├── css/
│   └── app.css
├── js/
│   ├── app.js              # Entry point, initialization
│   ├── store.js            # IndexedDB operations
│   ├── state.js            # In-memory state management
│   ├── router.js           # Tab navigation
│   ├── components/
│   │   ├── header.js
│   │   ├── tabs.js
│   │   ├── card.js
│   │   ├── modal.js
│   │   ├── table.js
│   │   ├── filters.js
│   │   ├── toast.js
│   │   └── empty.js
│   ├── pages/
│   │   ├── dashboard.js
│   │   ├── list.js
│   │   ├── map.js
│   │   ├── charts.js
│   │   ├── saved.js
│   │   ├── chat.js
│   │   └── settings.js
│   └── utils/
│       ├── csv.js
│       ├── geo.js
│       ├── format.js
│       └── helpers.js
└── assets/
    ├── cities.json         # UN/LOCODE → lat/lng lookup
    ├── logo.svg
    ├── favicon.ico
    ├── favicon-16.png
    ├── favicon-32.png
    ├── apple-touch-icon.png
    ├── icon-192.png
    └── icon-512.png
```

---

## Data Model

```javascript
// Source record (from CSV)
{
  "poc.id": "csj3xg35",
  "fund.id": "hbrpoig8",
  "poc.first_name": "Benjamin",
  // ... 29 fields total
}

// User overlay (persisted to IndexedDB)
{
  notes: {
    "csj3xg35": "Met at conference, follow up Q1"
  },
  starred: ["csj3xg35", "b61x91zl"],
  recent: [
    { id: "csj3xg35", ts: 1732537200000 }
  ],
  savedLists: [
    {
      id: "sl_abc123",
      label: "US Family Offices",
      recordIds: ["csj3xg35", "dghyjgk6"],
      created: 1732537200000
    }
  ],
  addedRecords: [
    { /* full record structure, marked as _isUserAdded: true */ }
  ],
  settings: {
    theme: "light",
    listView: "table"
  }
}

// Runtime merged record
{
  ...sourceRecord,
  _note: "user note or null",
  _starred: true/false,
  _isUserAdded: true/false
}
```

---

# PHASES

---

## Phase 1: Foundation

**Objective:** App shell with navigation, styling, data loading

### Todos

- [ ] Create `frontend/01/` directory structure
- [ ] Create `index.html` with:
  - [ ] DOCTYPE, meta viewport, Inter font import
  - [ ] Tailwind CDN with custom config (colors)
  - [ ] All library CDN links
  - [ ] App shell: header, tab bar, content area
  - [ ] Fixed viewport layout (no page scroll)
- [ ] Create `css/app.css`:
  - [ ] CSS custom properties for theme colors
  - [ ] Light/dark mode classes
  - [ ] Scrollbar styling
  - [ ] Transition utilities
- [ ] Create `js/store.js`:
  - [ ] Init IndexedDB via idb-keyval
  - [ ] `getUserData()` - load user overlay
  - [ ] `saveUserData(key, value)` - persist changes
  - [ ] `clearAllUserData()` - reset
- [ ] Create `js/state.js`:
  - [ ] Global state object
  - [ ] `setState(path, value)` - update + notify
  - [ ] `subscribe(callback)` - state change listeners
- [ ] Create `js/utils/csv.js`:
  - [ ] `loadCSV(url)` - fetch + parse with PapaParse
  - [ ] `exportCSV(records, filename)` - generate download
- [ ] Create `js/utils/helpers.js`:
  - [ ] `$(selector)` - query shorthand
  - [ ] `$$( selector)` - queryAll shorthand
  - [ ] `html(template)` - create element from string
  - [ ] `debounce(fn, ms)`
  - [ ] `generateId()` - 8-char random ID
- [ ] Create `js/utils/format.js`:
  - [ ] `formatCurrency(value)` - "$1.2B", "$450M"
  - [ ] `formatName(first, last)`
  - [ ] `formatSectors(semicolonString)` - split to array
  - [ ] `formatCountry(code)` - code to name
  - [ ] `truncate(str, len)`
- [ ] Create `js/router.js`:
  - [ ] Tab definitions (id, label, icon)
  - [ ] `navigate(tabId)` - switch active tab
  - [ ] URL hash sync (#list, #map, etc.)
  - [ ] Render tab bar
- [ ] Create `js/app.js`:
  - [ ] On DOMContentLoaded:
    - [ ] Load CSV data
    - [ ] Load user overlay from IndexedDB
    - [ ] Merge into runtime state
    - [ ] Initialize router
    - [ ] Render initial tab
  - [ ] Loading state with spinner
  - [ ] Error handling for failed loads
- [ ] Create `js/components/header.js`:
  - [ ] Logo/title
  - [ ] Global search input (wired in Phase 2)
  - [ ] Settings gear icon
- [ ] Create `js/components/tabs.js`:
  - [ ] Tab bar component
  - [ ] Active state styling
  - [ ] Feather icons
- [ ] Verify symlink exists: `data.csv → ../../data.csv` (created by process.zsh)
- [ ] Test: App loads, tabs clickable, no errors

**Commit:** `feat: Phase 1 - app foundation and data loading`

---

## Phase 2: List Tab

**Objective:** Browsable, searchable, filterable list of all records

### Todos

- [ ] Create `js/pages/list.js`:
  - [ ] Render function
  - [ ] View toggle: table / cards
  - [ ] Records container
- [ ] Create `js/components/table.js`:
  - [ ] Table with columns: Name, Role, Fund, Type, Country, Sectors, AUM
  - [ ] Sortable columns (click header)
  - [ ] Row click → open detail (Phase 3)
  - [ ] Handle null values gracefully (show "-")
- [ ] Create `js/components/card.js`:
  - [ ] Card layout: avatar placeholder, name, role, fund name
  - [ ] Country flag (flag-icons CSS)
  - [ ] Sectors as pills
  - [ ] AUM if available
- [ ] Create `js/components/filters.js`:
  - [ ] Filter panel (collapsible on mobile)
  - [ ] Fund type dropdown (Family Office, Investment Advisor, etc.)
  - [ ] Country multi-select
  - [ ] Sector multi-select
  - [ ] Stage dropdown
  - [ ] AUM range slider or min/max inputs
  - [ ] "Has email" checkbox
  - [ ] Clear all filters button
- [ ] Implement search:
  - [ ] Wire global search input
  - [ ] Search across: name, fund title, description
  - [ ] Debounced (300ms)
  - [ ] Highlight matches (optional)
- [ ] Implement filtering logic:
  - [ ] `applyFilters(records, filters)` utility
  - [ ] AND logic between filter types
  - [ ] OR logic within multi-selects
- [ ] Implement sorting:
  - [ ] `sortRecords(records, field, direction)`
  - [ ] Default: alphabetical by last name
- [ ] Results count display ("Showing 42 of 527")
- [ ] Empty state component when no results
- [ ] Pagination or infinite scroll:
  - [ ] Show 50 at a time
  - [ ] "Load more" button or scroll trigger
- [ ] Test: Filter combinations, search, sort, empty states

**Commit:** `feat: Phase 2 - list tab with search, filter, sort`

---

## Phase 3: Detail View & User Data

**Objective:** View full record details, add notes, star records

### Todos

- [ ] Create `js/components/modal.js`:
  - [ ] Overlay with backdrop
  - [ ] Close on X, Escape, backdrop click
  - [ ] Slide-in animation
  - [ ] Scrollable content area
- [ ] Create detail view content:
  - [ ] POC section: name, role, email (mailto link), phone, LinkedIn (external link)
  - [ ] POC description (full text)
  - [ ] Fund section: title, type, website, email, phone
  - [ ] Fund description, thesis (collapsible if long)
  - [ ] Location: country flag + name, city
  - [ ] Sectors as pills
  - [ ] Stage, geographies
  - [ ] Financials: AUM (formatted), ticket range
  - [ ] Portfolio companies (parsed from JSON-like string)
  - [ ] Crunchbase, LinkedIn links
- [ ] Star/favorite functionality:
  - [ ] Star icon button in detail header
  - [ ] Toggle starred state
  - [ ] Persist to IndexedDB immediately
  - [ ] Visual indicator in list/cards
- [ ] Notes functionality:
  - [ ] Textarea in detail view
  - [ ] Auto-save on blur (debounced)
  - [ ] Persist to IndexedDB
  - [ ] Show note indicator in list
- [ ] Recent tracking:
  - [ ] On detail open, add to recent array
  - [ ] Keep last 50, deduplicate
  - [ ] Persist to IndexedDB
- [ ] Create `js/components/toast.js`:
  - [ ] Success/error/info toasts
  - [ ] Auto-dismiss after 3s
  - [ ] "Note saved", "Added to starred", etc.
- [ ] Test: Open detail, add note, star, verify persistence after reload

**Commit:** `feat: Phase 3 - detail view with notes and starring`

---

## Phase 4: Saved Lists Tab

**Objective:** Save filtered selections, manage collections

### Todos

- [ ] Create `js/pages/saved.js`:
  - [ ] Sub-tab navigation: Saved | With Notes | Starred | Recent
  - [ ] Active sub-tab state
- [ ] "Saved" sub-tab:
  - [ ] List of saved lists with label, count, created date
  - [ ] Click to view records in that list
  - [ ] Delete saved list (with confirm)
  - [ ] Rename saved list
  - [ ] Empty state: "No saved lists yet"
- [ ] "With Notes" sub-tab:
  - [ ] Query all records where note exists
  - [ ] Display as card/table
  - [ ] Show note preview
- [ ] "Starred" sub-tab:
  - [ ] Query all starred records
  - [ ] Unstar action available
- [ ] "Recent" sub-tab:
  - [ ] Show last 50 viewed records
  - [ ] Timestamp display ("2 hours ago")
  - [ ] Clear recent history button
- [ ] Save list functionality (from List tab):
  - [ ] "Save current list" button in List tab when filtered
  - [ ] Modal: enter label name
  - [ ] Save recordIds + label to IndexedDB
  - [ ] Toast confirmation
- [ ] Test: Save list, view in Saved tab, delete, verify sub-tabs

**Commit:** `feat: Phase 4 - saved lists with sub-tabs`

---

## Phase 5: Dashboard Tab

**Objective:** Overview stats and quick insights

### Todos

- [ ] Create `js/pages/dashboard.js`:
  - [ ] Grid layout for stat cards
- [ ] Stat cards:
  - [ ] Total POCs
  - [ ] Total unique funds
  - [ ] Total AUM (sum, formatted)
  - [ ] Countries represented
  - [ ] Records with email (contactable)
- [ ] Quick filters / shortcuts:
  - [ ] "Family Offices" → navigate to List with filter
  - [ ] "US Funds" → navigate to List with filter
  - [ ] "Large funds (>$1B AUM)" → navigate to List with filter
- [ ] Mini charts (optional, can defer):
  - [ ] Fund types pie chart
  - [ ] Top 5 countries bar chart
- [ ] User stats:
  - [ ] Records with notes: X
  - [ ] Starred: X
  - [ ] Saved lists: X
- [ ] Test: Stats accuracy, quick filter navigation

**Commit:** `feat: Phase 5 - dashboard with stats and quick filters`

---

## Phase 6: Map Tab

**Objective:** Geographic visualization of funds

### Todos

- [ ] Create `assets/cities.json`:
  - [ ] Extract unique city codes from data.csv
  - [ ] Map UN/LOCODE to lat/lng coordinates
  - [ ] Format: `{ "NYC": { "lat": 40.7128, "lng": -74.0060, "name": "New York" }, ... }`
- [ ] Create `js/utils/geo.js`:
  - [ ] `loadCities()` - fetch cities.json
  - [ ] `getCityCoords(code)` - lookup
  - [ ] `getCountryCenter(code)` - fallback if city unknown
- [ ] Create `js/pages/map.js`:
  - [ ] Initialize Leaflet map
  - [ ] OpenStreetMap tiles (free, no API key)
  - [ ] Fit bounds to data points
- [ ] Add markers:
  - [ ] One marker per unique city
  - [ ] Cluster if multiple funds in same city
  - [ ] Custom marker color (theme primary)
- [ ] Hover popup:
  - [ ] City name
  - [ ] Count of funds
  - [ ] List first 3 fund names
  - [ ] "and X more" if > 3
- [ ] Click behavior:
  - [ ] Click marker → filter List to that city (or just show popup)
- [ ] Map controls:
  - [ ] Zoom in/out
  - [ ] Reset view button
- [ ] Responsive: Full height within content area
- [ ] Test: Markers display, popups work, no console errors

**Commit:** `feat: Phase 6 - interactive map with city markers`

---

## Phase 7: Charts Tab (Histograms)

**Objective:** Visual breakdowns by various dimensions

### Todos

- [ ] Create `js/pages/charts.js`:
  - [ ] Chart selector/tabs: By Type, By Country, By Sector, By AUM
- [ ] "By Fund Type" chart:
  - [ ] Horizontal bar chart
  - [ ] Family Office, Investment Advisor, SFO, MFO, etc.
  - [ ] Click bar → filter List
- [ ] "By Country" chart:
  - [ ] Top 15 countries bar chart
  - [ ] Show flag next to label
  - [ ] "Other" bucket for rest
- [ ] "By Sector" chart:
  - [ ] Top 15 sectors
  - [ ] Note: records have multiple sectors (count each)
- [ ] "By AUM Range" chart:
  - [ ] Buckets: <$100M, $100M-$500M, $500M-$1B, $1B-$10B, >$10B, Unknown
  - [ ] Bar or pie chart
- [ ] Chart.js setup:
  - [ ] Consistent theme colors
  - [ ] Tooltips
  - [ ] Responsive sizing
- [ ] Test: All charts render, data accurate

**Commit:** `feat: Phase 7 - charts tab with distribution visualizations`

---

## Phase 8: Add Data

**Objective:** Allow users to add new POC/Fund records

### Todos

- [ ] Add "+" button in header or List tab
- [ ] Create add/edit form modal:
  - [ ] POC fields: first name, last name, role, email, phone, LinkedIn
  - [ ] Fund fields: title, type (dropdown), website, country (dropdown), city
  - [ ] Sectors (multi-select or tags input)
  - [ ] AUM value, ticket min/max
  - [ ] Notes field
- [ ] Form validation:
  - [ ] Required: first name, last name, fund title
  - [ ] Email format validation
  - [ ] URL format for website/LinkedIn
- [ ] On save:
  - [ ] Generate poc.id and fund.id
  - [ ] Mark as `_isUserAdded: true`
  - [ ] Add to `addedRecords` in IndexedDB
  - [ ] Merge into runtime state
  - [ ] Show in List with visual indicator (badge "Added")
- [ ] Edit existing (user-added only):
  - [ ] Edit button in detail view (only for user-added)
  - [ ] Pre-fill form
  - [ ] Update in IndexedDB
- [ ] Delete user-added record:
  - [ ] Delete button (only for user-added)
  - [ ] Confirm dialog
  - [ ] Remove from IndexedDB and state
- [ ] Test: Add record, see in list, edit, delete, persists after reload

**Commit:** `feat: Phase 8 - add and edit user records`

---

## Phase 9: Export

**Objective:** Export filtered data as CSV

### Todos

- [ ] Add "Export" button in List tab header
- [ ] Export logic:
  - [ ] Take current filtered/sorted records
  - [ ] Include user notes as `poc.notes` column
  - [ ] Generate CSV string
  - [ ] Trigger download as `silversky-export-{date}.csv`
- [ ] Export options (optional modal):
  - [ ] All fields or selected fields
  - [ ] Include user-added records toggle
- [ ] Handle special characters in CSV (quotes, commas)
- [ ] Test: Export with filters, open in Excel/Sheets

**Commit:** `feat: Phase 9 - CSV export functionality`

---

## Phase 10: Settings & Polish

**Objective:** Settings tab, PWA, final polish

### Todos

- [ ] Create `js/pages/settings.js`:
  - [ ] Theme toggle: Light / Dark / System
  - [ ] Default list view: Table / Cards
  - [ ] Clear all user data (with confirm)
  - [ ] About section: version, data count
- [ ] Implement dark mode:
  - [ ] CSS class toggle on html element
  - [ ] Persist preference
  - [ ] Respect system preference if "System" selected
- [ ] Create `js/pages/chat.js`:
  - [ ] Empty placeholder tab
  - [ ] "Coming soon" message
  - [ ] Chat UI mockup (input, messages area)
- [ ] PWA setup:
  - [ ] Create `manifest.json`
  - [ ] App name, icons (use placeholder or generate)
  - [ ] Theme color, background color
  - [ ] Display: standalone
- [ ] Service worker (optional for offline):
  - [ ] Cache static assets
  - [ ] Cache data.csv
  - [ ] Offline fallback
- [ ] Final polish:
  - [ ] Loading skeletons
  - [ ] Smooth transitions between tabs
  - [ ] Focus states for accessibility
  - [ ] Keyboard navigation (Escape closes modals)
  - [ ] Mobile responsive testing
  - [ ] Console error cleanup
- [ ] Test: Theme switching, PWA install prompt, offline behavior

**Commit:** `feat: Phase 10 - settings, dark mode, PWA`

---

## Final Commit

After all phases:

```
git tag v1.0.0
```

**Final commit:** `chore: Silversky CRM v1.0 complete`

---

## Post-Launch Ideas (Not in scope)

- AI chat integration (Gemini)
- Email templates / outreach tracking
- Import from CSV/Excel
- Sync to HubSpot/Attio API
- Collaboration features
- Advanced analytics

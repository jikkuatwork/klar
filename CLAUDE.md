# Silversky Capital - Investor CRM Data Enrichment

**Status:** Phase 2 Complete ✅ | 527 Records

---

## Current State

**Enriched Dataset:** `data.csv` - 527 unique investor contacts
- Enriched via Gemini 2.5 Pro with Google Search grounding
- Cleaned, standardized, and deduplicated
- Location codes: ISO 3166-1 (countries) + UN/LOCODE (cities)
- Unique IDs: 8-char alphanumeric (poc.id, fund.id)

**Original Data:** `data_original.csv` - 544 raw records (backup)

---

## Data Schema (29 fields)

```csv
# Identifiers
poc.id, fund.id

# POC (Point of Contact) fields
poc.first_name, poc.last_name, poc.role, poc.email, poc.linkedin,
poc.phone, poc.description

# Fund fields
fund.title, fund.type, fund.email, fund.website, fund.country,
fund.city, fund.sectors, fund.preferred_stage, fund.crunchbase,
fund.linkedin, fund.phone, fund.description, fund.thesis,
fund.portfolio_companies, fund.geographies

# Financial fields (raw USD integers)
fund.aum.value, fund.aum.year, fund.ticket.min, fund.ticket.max

# Metadata
_validation_issues
```

**Naming Convention:**
- `poc.*` = Point of contact (person) fields
- `fund.*` = Company/organization fields
- Nested fields use dots: `fund.aum.value`, `fund.ticket.min`
- `_validation_issues` = Auto-detected quality flags

---

## Location Standards

### Countries: ISO 3166-1 alpha-2
- **Standard:** [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)
- **Format:** 2-letter uppercase codes (e.g., `US`, `GB`, `CH`, `DE`)
- **Field:** `fund.country`

### Cities: UN/LOCODE
- **Standard:** [UN/LOCODE](https://unece.org/trade/uncefact/unlocode)
- **Format:** 3-letter uppercase codes (e.g., `NYC`, `LON`, `ZRH`, `SFO`)
- **Field:** `fund.city`
- **Note:** We store only the 3-letter city portion (country is separate)

### JS Libraries for Web App

```javascript
// Country flags (SVG)
// https://www.npmjs.com/package/country-flag-icons
import { US, GB, CH } from 'country-flag-icons/react/3x2'

// Country names from ISO codes
// https://www.npmjs.com/package/i18n-iso-countries
import countries from 'i18n-iso-countries'
countries.getName('US', 'en') // → "United States"

// City coordinates from UN/LOCODE
// https://www.npmjs.com/package/@geoapify/un-locode
// Provides lat/lng for map placement

// Alternative: Simple lookup tables
const CITY_NAMES = {
  'NYC': 'New York',
  'LON': 'London',
  'ZRH': 'Zurich',
  // ...
}
```

---

## Project Structure

```
├── CLAUDE.md                    # This file - project documentation
├── data.csv                     # 527 enriched records (PRIMARY) ⭐
├── data_original.csv            # 544 original records (backup)
├── manual.md                    # Quick start guide
├── .gitignore                   # Python/test artifacts
│
├── scripts/
│   ├── run_enrichment.py        # Production enrichment runner
│   ├── multi_stage_enrichment.py # Core enrichment engine
│   ├── consistency_check.py     # Data quality validation
│   ├── standardize_locations.py # ISO/LOCODE transformation
│   └── export_clean_data.py     # Original data export
│
├── docs/                        # Historical documentation
│   ├── multi-stage-enrichment-guide.md
│   ├── single-vs-multi-stage-comparison.md
│   └── gemini-grounding-learnings.md
│
└── koder/                       # Original source materials
    ├── rough.md
    └── docs/CRM.xlsx            # Source Excel (6,528 records)
```

---

## Enrichment System

### Model: `gemini-2.5-pro`
- Best balance of speed (~40s/record) and quality
- With Google Search grounding for real-time data

### Architecture (2-Stage)

**Stage 1: POC (Person)**
- Fields: poc.linkedin, poc.role, poc.description, poc.phone
- Validation: LinkedIn URL must contain person's name

**Stage 2: Fund (Company)**
- Fields: fund.linkedin, fund.crunchbase, fund.website, fund.sectors
- Financial: fund.aum.value, fund.aum.year, fund.ticket.min, fund.ticket.max
- Validation: LinkedIn must be /company/ URL (not personal)

### Running Enrichment

```bash
# Full run (~3-5 min with 40 workers)
python3 scripts/run_enrichment.py \
  --input data.csv \
  --output data_enriched.csv \
  --workers 40

# Test with subset
python3 scripts/run_enrichment.py \
  --limit 10 \
  --workers 10 \
  --verbose
```

### Cost (gemini-2.5-pro)

- ~7,600 tokens per record
- Input: $1.25/1M tokens, Output: $10.00/1M tokens
- **Full dataset: ~$34**

---

## Standard Sectors

```python
[
    # Investment types
    "venture-capital", "private-equity", "hedge-funds", "growth-capital",
    "private-debt", "public-markets", "fixed-income", "commodities",
    # Industries
    "technology", "software", "saas", "enterprise-software", "ai-ml",
    "healthcare", "healthtech", "biotech", "fintech", "cleantech",
    "real-estate", "infrastructure", "energy", "manufacturing",
    "consumer", "retail", "ecommerce", "hospitality",
    "media", "entertainment", "telecommunications",
    "aerospace", "defense", "transportation", "agriculture",
    "education", "financial-services", "insurance",
    # Themes
    "crypto-blockchain", "impact-investing", "esg", "sustainable-finance"
]
```

---

## Environment

```bash
export GEMINI_API_KEY='your-key'
```

---

**Last Updated:** 2025-11-25
**Records:** 527 (cleaned, standardized, with unique IDs)

# Silversky Capital - Investor CRM Data Enrichment

**Status:** Phase 1 Complete ✅ | 539 Records Enriched

---

## Current State

**Enriched Dataset:** `data.csv` - 539 unique investor contacts
- Enriched via Gemini 2.5 Pro with Google Search grounding
- 87% clean records (no validation issues)
- 99% role completion, 97% sectors, 88% descriptions
- Deduplicated (removed 4 duplicate person+fund entries)

**Original Data:** `data_original.csv` - 544 raw records (backup)

---

## Project Structure

```
├── CLAUDE.md                    # This file - project documentation
├── data.csv                     # 539 enriched records (PRIMARY) ⭐
├── data_original.csv            # 544 original records (backup)
├── manual.md                    # Quick start guide
├── .gitignore                   # Python/test artifacts
│
├── scripts/
│   ├── run_enrichment.py        # Production runner ⭐
│   ├── multi_stage_enrichment.py # Core enrichment engine
│   └── export_clean_data.py     # Original data export script
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

## Data Schema

```csv
fund.title, fund.type, poc.first_name, poc.last_name, poc.role,
poc.email, fund.email, fund.website, fund.country, fund.city,
fund.sectors, fund.preferred_stage, poc.linkedin, fund.crunchbase,
fund.linkedin, poc.phone, fund.phone, poc.description,
fund.description, fund.thesis, fund.portfolio_companies, fund.aum,
fund.geographies, _validation_issues
```

**Prefix Convention:**
- `fund.*` = Company/organization fields
- `poc.*` = Point of contact (person) fields
- `_validation_issues` = Auto-detected quality flags

---

## Quality Metrics (Phase 1 Results)

| Metric | Value |
|--------|-------|
| Total records | 539 |
| Clean records | 87% |
| POC LinkedIn mismatches | 1.3% (auto-cleared) |
| Fund LinkedIn issues | 0% |
| Missing descriptions | 12% |

### Field Completion

| Field | Rate |
|-------|------|
| poc.role | 99% |
| fund.sectors | 97% |
| fund.website | 95% |
| poc.description | 88% |
| poc.linkedin | 75% |
| fund.linkedin | 62% |
| fund.crunchbase | 62% |
| poc.phone | 22% |

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
- Validation: LinkedIn must be /company/ URL (not personal)

### Running Enrichment

```bash
# Full run (539 records, ~3-5 min with 40 workers)
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

### Cost

- ~7,600 tokens per record
- Input: $1.25/1M tokens, Output: $10.00/1M tokens
- **Full 539 records: ~$34**

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
**Phase 1 Completed:** 539 records enriched, deduplicated, validated

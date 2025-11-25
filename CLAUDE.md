# Silversky Capital - Investor CRM

**Status:** Data Ready | 527 Records

---

## Dataset: `data.csv`

527 unique investor contacts with:
- Unique IDs: 8-char alphanumeric (`poc.id`, `fund.id`)
- Location codes: ISO 3166-1 (countries) + UN/LOCODE (cities)
- Financial data in raw USD integers

---

## Schema (29 fields)

```
# Identifiers
poc.id, fund.id

# POC (Point of Contact)
poc.first_name, poc.last_name, poc.role, poc.email, poc.linkedin,
poc.phone, poc.description

# Fund
fund.title, fund.type, fund.email, fund.website, fund.country,
fund.city, fund.sectors, fund.preferred_stage, fund.crunchbase,
fund.linkedin, fund.phone, fund.description, fund.thesis,
fund.portfolio_companies, fund.geographies

# Financials (raw USD integers)
fund.aum.value, fund.aum.year, fund.ticket.min, fund.ticket.max

# Metadata
_validation_issues
```

---

## Location Standards

| Field | Standard | Format | Example |
|-------|----------|--------|---------|
| `fund.country` | ISO 3166-1 alpha-2 | 2-letter | `US`, `GB`, `CH` |
| `fund.city` | UN/LOCODE | 3-letter | `NYC`, `LON`, `ZRH` |

### JS Libraries

```javascript
// Country flags (SVG)
import { US, GB } from 'country-flag-icons/react/3x2'

// Country names from ISO codes
import countries from 'i18n-iso-countries'
countries.getName('US', 'en') // → "United States"

// City coordinates from UN/LOCODE
// @geoapify/un-locode - provides lat/lng for map placement
```

---

## Standard Sectors

```
venture-capital, private-equity, hedge-funds, growth-capital,
private-debt, public-markets, fixed-income, commodities,
technology, software, saas, enterprise-software, ai-ml,
healthcare, healthtech, biotech, fintech, cleantech,
real-estate, infrastructure, energy, manufacturing,
consumer, retail, ecommerce, hospitality,
media, entertainment, telecommunications,
aerospace, defense, transportation, agriculture,
education, financial-services, insurance,
crypto-blockchain, impact-investing, esg, sustainable-finance
```

---

**Last Updated:** 2025-11-25

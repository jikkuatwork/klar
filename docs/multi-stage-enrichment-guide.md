# Multi-Stage Enrichment System Guide

## Overview

This system separates data enrichment into configurable stages to understand Gemini3's grounding behavior and optimize search quality.

## Architecture

### Stage Separation Philosophy

Instead of requesting all data in one query, we separate concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    Single-Stage Approach                      │
│  "Find everything about person AND company in one query"     │
│                                                               │
│  Problem: Search may prioritize company over person          │
│  Result: Mixed quality, unclear what was found where         │
└─────────────────────────────────────────────────────────────┘

                            VS

┌─────────────────────────────────────────────────────────────┐
│                    Multi-Stage Approach                       │
│                                                               │
│  Stage 1: POC (Person)         Stage 2: Fund (Company)       │
│  ┌──────────────────┐          ┌──────────────────┐          │
│  │ - poc.linkedin   │          │ - fund.linkedin  │          │
│  │ - poc.role       │          │ - fund.crunchbase│          │
│  │ - poc.description│          │ - fund.website   │          │
│  │ - poc.phone      │          │ - fund.sectors   │          │
│  └──────────────────┘          └──────────────────┘          │
│                                                               │
│  Benefit: Focused searches, clear attribution, better depth  │
└─────────────────────────────────────────────────────────────┘
```

## Available Stages

### Stage 1: POC (Contact Person) Enrichment
**Focus:** Individual professional information

**Fields:**
- `poc.linkedin` - Personal LinkedIn profile (linkedin.com/in/...)
- `poc.role` - Current job title
- `poc.description` - Professional bio (2-3 sentences)
  - Role and responsibilities
  - Years of experience
  - Previous companies
  - Education/specializations
- `poc.phone` - Direct phone number

**Search Strategy:**
- Queries focus on the person's name + company
- Prioritizes personal profiles over company pages
- Looks for career history and background

**Expected Tokens:** ~3,000-5,000 per record

### Stage 2: Fund (Company) Enrichment
**Focus:** Organization and investment information

**Fields:**
- `fund.linkedin` - Company LinkedIn page (linkedin.com/company/...)
- `fund.crunchbase` - Crunchbase organization page
- `fund.website` - Official company website
- `fund.sectors` - Investment focus areas (standardized array)
- `fund.preferred_stage` - Investment stage preference
- `fund.city` - Headquarters location

**Search Strategy:**
- Queries focus on company name + type
- Looks for official pages and profiles
- Researches investment focus and portfolio

**Expected Tokens:** ~3,000-5,000 per record

### Stage 3: Fund Deep Research (Optional)
**Focus:** Strategic insights and portfolio

**Fields:**
- `fund.description` - Company overview (3-4 sentences)
  - What they do, market position
  - AUM or fund size
  - Year founded, key milestones
- `fund.thesis` - Investment philosophy (2-3 sentences)
  - Investment approach
  - What they look for
  - Focus areas and ticket size
- `fund.portfolio_companies` - Recent investments (array)
  - Name, website, sector, description
  - 3-5 notable portfolio companies
- `fund.aum` - Assets under management
- `fund.geographies` - Geographic investment focus

**Search Strategy:**
- Deep research into investment strategy
- Portfolio analysis
- Strategic positioning research

**Expected Tokens:** ~4,000-8,000 per record

## Configuration Options

### Grounding Configuration

**IMPORTANT DISCOVERY:** The Gemini API does NOT support advanced grounding configuration options like `dynamicRetrievalConfig` or `dynamicThreshold`, despite being mentioned in some documentation.

**What Works:**
```python
"tools": [
    {
        "googleSearch": {}  # Simple grounding - this is all that's supported
    }
]
```

**What Doesn't Work:**
```python
# ❌ API returns 400 error - field not recognized
"tools": [
    {
        "googleSearch": {
            "dynamicRetrievalConfig": {
                "mode": "MODE_DYNAMIC",
                "dynamicThreshold": 0.7
            }
        }
    }
]
```

**Implication:**
Since we cannot control grounding behavior via API parameters, we must rely on:
1. **Prompt design** - Be specific about what to search for
2. **Multi-stage architecture** - Separate queries to focus searches
3. **Query structure** - Clear instructions improve search quality

This makes the multi-stage approach even MORE valuable, since prompt design is our only control mechanism

## Usage Examples

### Example 1: Standard 2-Stage Enrichment

```python
from scripts.multi_stage_enrichment import MultiStageEnricher

enricher = MultiStageEnricher()

result = enricher.enrich_record_multistage(
    record=my_record,
    stages=["poc", "fund"],  # Person + Company
    delay_between_stages=2   # 2 second delay
)

print(f"Enriched {len(result['enriched'])} fields")
print(f"Used {result['total_tokens']} tokens")
```

### Example 2: Company Only (Skip Person)

Useful when you only need company data:

```python
result = enricher.enrich_record_multistage(
    record=my_record,
    stages=["fund"],  # Company only
    delay_between_stages=0
)
```

### Example 3: Full 3-Stage Enrichment

For maximum detail including portfolio analysis:

```python
result = enricher.enrich_record_multistage(
    record=my_record,
    stages=["poc", "fund", "deep"],
    delay_between_stages=3
)
```

### Example 4: Custom Grounding Per Stage

Test different search depths per stage:

```python
grounding_configs = {
    "poc": {
        "dynamicRetrievalConfig": {
            "mode": "MODE_DYNAMIC",
            "dynamicThreshold": 0.5  # Very thorough for person research
        }
    },
    "fund": {
        "dynamicRetrievalConfig": {
            "mode": "MODE_DYNAMIC",
            "dynamicThreshold": 0.8  # Less thorough for company (faster)
        }
    }
}

result = enricher.enrich_record_multistage(
    record=my_record,
    stages=["poc", "fund"],
    grounding_configs=grounding_configs,
    delay_between_stages=2
)
```

## Experimentation Guide

### Questions to Answer Through Testing

1. **Does multi-stage improve quality?**
   - Compare 2-stage vs 1-stage for same records
   - Check if person descriptions are better when queried separately
   - Verify if company URLs are more accurate

2. **What's the optimal stage combination?**
   - Test: ["poc", "fund"] vs ["fund"] vs ["poc", "fund", "deep"]
   - Measure: quality, tokens, time
   - Find the sweet spot for your use case

3. **How does grounding threshold affect results?**
   - Test same record with threshold 0.5, 0.7, 0.9
   - Measure: search_quality from metadata, tokens used
   - Determine if lower threshold = better data

4. **Is deep research worth the tokens?**
   - Compare "poc + fund" vs "poc + fund + deep"
   - Check if portfolio_companies and thesis add value
   - Calculate ROI of deep stage

### Recommended Testing Protocol

```python
# Test Configuration Matrix
test_matrix = [
    {
        "name": "Baseline: 1-Stage Fund Only",
        "stages": ["fund"],
        "threshold": 0.7
    },
    {
        "name": "Standard: 2-Stage POC + Fund",
        "stages": ["poc", "fund"],
        "threshold": 0.7
    },
    {
        "name": "Thorough: 2-Stage Low Threshold",
        "stages": ["poc", "fund"],
        "threshold": 0.5
    },
    {
        "name": "Full: 3-Stage with Deep Research",
        "stages": ["poc", "fund", "deep"],
        "threshold": 0.7
    }
]

# Run each config on same 5-10 sample records
# Compare results in a spreadsheet
```

## Output Structure

### Enriched Result Format

```python
{
  "original": {
    # Original record data
  },
  "enriched": {
    # All successfully enriched fields merged from all stages
    "poc.linkedin": "...",
    "poc.description": "...",
    "fund.linkedin": "...",
    "fund.sectors": ["..."]
  },
  "stage_results": {
    "poc": {
      # POC stage output
      "poc.linkedin": "...",
      "_stage_meta": {
        "confidence": "high",
        "fields_found": ["poc.linkedin", "poc.description"],
        "search_quality": "excellent",
        "notes": "..."
      }
    },
    "fund": {
      # Fund stage output
      "fund.linkedin": "...",
      "_stage_meta": {
        "confidence": "high",
        "fields_found": ["fund.linkedin", "fund.sectors"],
        "fields_corrected": [],
        "search_quality": "good",
        "notes": "..."
      }
    }
  },
  "total_tokens": 8500,
  "stages_run": ["poc", "fund"]
}
```

### Metadata Fields

Each stage returns metadata for analysis:

- `confidence`: high | medium | low
  - How confident is the model in the results?

- `fields_found`: List of fields successfully enriched
  - Track what was discovered

- `fields_corrected`: List of fields that were wrong and fixed
  - Identify data quality issues

- `search_quality`: excellent | good | limited | poor
  - Gemini's assessment of search result quality
  - May indicate if more stages/searches needed

- `notes`: Free-form explanation
  - Why certain fields were not found
  - What sources were used
  - Any caveats or uncertainties

## Token Economics

### Expected Token Usage

**Per Record Estimates:**

| Configuration | Stages | Avg Tokens | Cost @ $0.15/1M tokens |
|--------------|--------|------------|------------------------|
| Fund Only | fund | ~3,500 | $0.000525 |
| Standard | poc + fund | ~7,000 | $0.00105 |
| Thorough | poc + fund (low threshold) | ~9,000 | $0.00135 |
| Full | poc + fund + deep | ~12,000 | $0.0018 |

**For 544 Clean Records:**

| Configuration | Total Tokens | Estimated Cost |
|--------------|--------------|----------------|
| Fund Only | ~1.9M | $0.29 |
| Standard | ~3.8M | $0.57 |
| Thorough | ~4.9M | $0.74 |
| Full | ~6.5M | $0.98 |

**For Aggressive (6,528 Records → 2,000 enriched):**

| Configuration | Total Tokens | Estimated Cost |
|--------------|--------------|----------------|
| Standard | ~14M | $2.10 |
| Full | ~24M | $3.60 |

## Performance Tuning

### Rate Limiting

```python
# Conservative (avoid rate limits)
delay_between_stages = 3  # seconds
batch_delay = 5  # between records

# Balanced
delay_between_stages = 2
batch_delay = 3

# Aggressive (may hit limits)
delay_between_stages = 1
batch_delay = 1
```

### Batch Processing

Process records in parallel batches:

```python
from concurrent.futures import ThreadPoolExecutor

def enrich_batch(records, max_workers=3):
    enricher = MultiStageEnricher()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                enricher.enrich_record_multistage,
                record,
                stages=["poc", "fund"],
                delay_between_stages=2
            )
            for record in records
        ]

        results = [f.result() for f in futures]

    return results
```

**Recommended:**
- `max_workers=3` for conservative rate limiting
- `max_workers=5` for faster processing (may hit limits)
- Add retry logic for rate limit errors

## Quality Validation

### Post-Enrichment Checks

After enrichment, validate:

1. **URL Format Validation**
   ```python
   # poc.linkedin must be linkedin.com/in/...
   # fund.linkedin must be linkedin.com/company/...
   # fund.crunchbase must be crunchbase.com/organization/...
   ```

2. **Sector Standardization**
   ```python
   # fund.sectors must only contain standardized values
   # Check against standard_sectors list
   ```

3. **Confidence Scoring**
   ```python
   # Only accept results with confidence = "high"
   # Review medium/low confidence manually
   ```

4. **Completeness Check**
   ```python
   # How many target fields were filled?
   # Did we get minimum viable data?
   ```

## Next Steps

1. **Run Test Suite**
   ```bash
   python3 scripts/multi_stage_enrichment.py
   ```

2. **Analyze Results**
   - Review `multi_stage_test_results.json`
   - Compare stage outputs
   - Check search_quality scores

3. **Choose Configuration**
   - Based on token budget
   - Based on quality needs
   - Based on time constraints

4. **Scale to Full Dataset**
   - Start with 544 clean records
   - Monitor quality and tokens
   - Adjust configuration as needed

5. **Document Learnings**
   - What threshold works best?
   - Is multi-stage better than single-stage?
   - Which fields are hardest to find?
   - Does grounding have limitations?

## Troubleshooting

### Common Issues

**1. Empty search_quality metadata**
- Gemini may not always provide this field
- Focus on confidence and fields_found instead

**2. High token usage**
- Increase dynamicThreshold (0.8 or 0.9)
- Reduce number of stages
- Skip deep research stage

**3. Low quality results**
- Decrease dynamicThreshold (0.5 or 0.6)
- Add more context to prompts
- Try multi-stage if using single-stage

**4. Rate limiting errors**
- Increase delay_between_stages
- Reduce max_workers in batch processing
- Add exponential backoff retry logic

## Advanced: Custom Stages

You can add custom stages for specific needs:

```python
def build_custom_stage_prompt(self, record: Dict) -> str:
    """Custom stage for specific data extraction"""

    prompt = f"""
    Your custom research task here...

    Return JSON with:
    {{
      "custom.field1": "...",
      "custom.field2": "...",
      "_stage_meta": {{ ... }}
    }}
    """

    return prompt

# Add to enrich_record_multistage() method
# Register as new stage option
```

## Comparison: Single-Stage vs Multi-Stage

### Hypothesis

**Single-Stage:**
- Pros: Fewer API calls, faster
- Cons: Search may be unfocused, lower quality per field

**Multi-Stage:**
- Pros: Focused searches, better quality, clear attribution
- Cons: More API calls, slower, more tokens

### Testing This Hypothesis

Run the test script and compare:

1. **Single comprehensive prompt** (like test_comprehensive_enrichment.py)
   - All fields in one request
   - Measure: tokens, quality, completeness

2. **Multi-stage approach** (this system)
   - Separate POC and Fund queries
   - Measure: tokens, quality, completeness

3. **Compare Results:**
   - Which finds more accurate poc.linkedin?
   - Which generates better poc.description?
   - Which has better fund.sectors mapping?
   - What's the token difference?

The answer will inform your production enrichment strategy!

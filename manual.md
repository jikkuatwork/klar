# Manual Enrichment Instructions

## Quick Start

```bash
# Ensure API key is set
export GEMINI_API_KEY='your-key'

# Run full enrichment (544 records, ~2-3 min with 40 workers)
python3 scripts/run_enrichment.py \
  --input data.csv \
  --output data_enriched.csv \
  --workers 40
```

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--input, -i` | data.csv | Input CSV |
| `--output, -o` | data_enriched.csv | Output CSV |
| `--workers, -w` | 5 | Parallel workers (20-40 recommended) |
| `--limit, -l` | None | Process only N records |
| `--start, -s, --start-index` | 0 | Start from row N (0-indexed) |
| `--resume, -r` | False | Resume from progress file |
| `--stages` | poc,fund | Stages: poc,fund,deep |
| `--delay, -d` | 2 | Seconds between stages |
| `--verbose, -v` | False | Show detailed output per record |
| `--model, -m` | gemini-2.5-pro | Model to use |

## Resume After Interruption

```bash
# If interrupted, resume with:
python3 scripts/run_enrichment.py \
  --input data.csv \
  --output data_enriched.csv \
  --resume
```

## Test First

```bash
# Test with 10 records
python3 scripts/run_enrichment.py \
  --input data.csv \
  --output test_out.csv \
  --limit 10 \
  --workers 10
```

## Output Files

- `data_enriched.csv` - Enriched records with validation
- `.enrichment_progress` - Last completed row index
- `enrichment_errors.log` - Failed records
- `_validation_issues` column - Auto-detected quality issues

## Expected Performance

| Workers | 100 records | 544 records | Cost |
|---------|-------------|-------------|------|
| 20 | ~2 min | ~10 min | ~$34 |
| 40 | ~1.5 min | ~5 min | ~$34 |

## Cost Breakdown (gemini-2.5-pro)

- Input: $1.25 per 1M tokens
- Output: $10.00 per 1M tokens
- ~7,600 tokens per record
- **~$34 for 544 records**

## Quality Metrics (from 100-record test)

- 88% clean records (no validation issues)
- 0% LinkedIn mismatches (auto-validated)
- 98% role completion
- 98% sectors completion
- 88% descriptions completion

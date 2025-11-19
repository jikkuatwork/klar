# TODO - Production Enrichment System

**Priority:** High - Needed before Phase 1 execution (544 records)

---

## 🎯 Required Features

### 1. Parallel Processing (HIGH PRIORITY)

**Current State:** ❌ Sequential processing only
**Requirement:** Support up to 20 concurrent requests

**What to Build:**
```python
# Use ThreadPoolExecutor for parallel record processing
from concurrent.futures import ThreadPoolExecutor, as_completed

class ProductionEnricher:
    def process_batch(self, records, max_workers=20):
        """Process records in parallel"""
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.enrich_record, record): record
                for record in records
            }

            for future in as_completed(futures):
                try:
                    result = future.result()
                    yield result
                except Exception as e:
                    # Handle errors gracefully
                    pass
```

**Benefits:**
- 20x faster processing (20 concurrent vs 1 sequential)
- Full utilization of Gemini API rate limits
- 544 records: ~10-15 minutes instead of 2-3 hours

**Implementation Notes:**
- Use `ThreadPoolExecutor` (not multiprocessing - API calls are I/O bound)
- Configure `max_workers` via CLI argument (default: 10, max: 20)
- Add rate limiting safety (track requests/minute)
- Handle 429 errors with exponential backoff

---

### 2. Graceful Resumability (HIGH PRIORITY)

**Current State:** ❌ No checkpoint system - must restart from beginning if interrupted
**Requirement:** Resume from last completed record if process crashes/stops

**What to Build:**

#### A. Checkpoint System
```python
# progress.json structure
{
    "started_at": "2025-11-20T10:00:00Z",
    "last_updated": "2025-11-20T10:15:00Z",
    "total_records": 544,
    "completed_count": 127,
    "completed_ids": [
        "hash_of_record_1",
        "hash_of_record_2",
        ...
    ],
    "failed_ids": [
        "hash_of_record_x"
    ],
    "total_tokens": 847250,
    "errors": []
}
```

#### B. Incremental Output
```python
# Append to output file as records complete
# Don't wait for all 544 to finish

def save_result(self, result):
    """Save result immediately to CSV"""
    # Append mode, with file locking
    with file_lock('data_enriched.csv'):
        append_to_csv(result)

    # Update checkpoint
    self.update_checkpoint(result['id'])
```

#### C. Resume Logic
```python
def load_records(self, input_file, checkpoint_file):
    """Load records, skip already completed"""
    all_records = load_csv(input_file)
    checkpoint = load_checkpoint(checkpoint_file)

    completed_ids = set(checkpoint.get('completed_ids', []))

    # Filter out completed
    pending = [
        r for r in all_records
        if self.record_id(r) not in completed_ids
    ]

    print(f"Total: {len(all_records)}, Completed: {len(completed_ids)}, Pending: {len(pending)}")
    return pending
```

**Benefits:**
- Can stop/restart anytime without losing progress
- Power failure / network interruption → just resume
- Failed records tracked separately for retry
- Real-time progress visibility

**Implementation Notes:**
- Checkpoint file: `enrichment_progress.json`
- Save checkpoint every 10 records (configurable)
- Record ID: hash of `fund.title + poc.first_name + poc.last_name`
- Failed records: save error details for debugging
- Resume flag: `--resume` to continue from checkpoint

---

## 📋 Production Script Design

### Script Name: `run_production_enrichment.py`

### CLI Interface:
```bash
# Fresh start
python3 scripts/run_production_enrichment.py \
  --input data.csv \
  --output data_enriched.csv \
  --stages poc,fund \
  --max-workers 20 \
  --checkpoint enrichment_progress.json

# Resume after interruption
python3 scripts/run_production_enrichment.py \
  --input data.csv \
  --output data_enriched.csv \
  --resume \
  --checkpoint enrichment_progress.json

# Retry failed records only
python3 scripts/run_production_enrichment.py \
  --input data.csv \
  --output data_enriched_retry.csv \
  --retry-failed \
  --checkpoint enrichment_progress.json
```

### Arguments:
```python
parser.add_argument('--input', required=True, help='Input CSV file')
parser.add_argument('--output', required=True, help='Output CSV file')
parser.add_argument('--stages', default='poc,fund', help='Stages: poc,fund,deep')
parser.add_argument('--max-workers', type=int, default=10, help='Parallel workers (max 20)')
parser.add_argument('--checkpoint', default='enrichment_progress.json', help='Checkpoint file')
parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
parser.add_argument('--retry-failed', action='store_true', help='Retry only failed records')
parser.add_argument('--delay', type=int, default=2, help='Delay between stages (seconds)')
parser.add_argument('--checkpoint-interval', type=int, default=10, help='Save checkpoint every N records')
```

### Features to Include:
- ✅ Parallel processing with ThreadPoolExecutor
- ✅ Checkpoint system (save progress)
- ✅ Resume capability (continue from last checkpoint)
- ✅ Incremental output (append to CSV as records complete)
- ✅ Progress bar (tqdm or similar)
- ✅ Real-time stats (completed, failed, tokens used, ETA)
- ✅ Error handling with retry logic
- ✅ Rate limiting safety (track API calls/minute)
- ✅ Graceful shutdown (Ctrl+C saves checkpoint)
- ✅ Final summary report

### Output Files:
```
enrichment_progress.json       # Checkpoint file
data_enriched.csv              # Incrementally updated output
enrichment_report.json         # Final stats and quality metrics
enrichment_errors.log          # Detailed error logs
```

---

## 🔧 Implementation Details

### Error Handling Strategy

```python
# Retry logic for transient errors
def enrich_with_retry(self, record, max_retries=3):
    """Enrich record with retry logic"""
    for attempt in range(max_retries):
        try:
            result = self.enricher.enrich_record_multistage(record)
            return result
        except RateLimitError as e:
            # 429 error - exponential backoff
            wait_time = 2 ** attempt
            print(f"Rate limited, waiting {wait_time}s...")
            time.sleep(wait_time)
        except Exception as e:
            if attempt == max_retries - 1:
                # Final attempt failed - log and continue
                self.log_error(record, e)
                return None
            time.sleep(1)
```

### Progress Tracking

```python
# Real-time progress display
from tqdm import tqdm

with tqdm(total=len(pending_records), desc="Enriching") as pbar:
    for result in self.process_batch(pending_records):
        if result:
            pbar.update(1)
            pbar.set_postfix({
                'tokens': f"{self.total_tokens:,}",
                'failed': self.failed_count,
                'rate': f"{self.get_rate():.1f} rec/min"
            })
```

### Graceful Shutdown

```python
import signal

class ProductionEnricher:
    def __init__(self):
        self.shutdown_requested = False
        signal.signal(signal.SIGINT, self.handle_shutdown)

    def handle_shutdown(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\n\n⚠️  Shutdown requested, saving checkpoint...")
        self.shutdown_requested = True
        self.save_checkpoint()
        print("✅ Checkpoint saved. Run with --resume to continue.")
        sys.exit(0)
```

---

## 📊 Testing Strategy

### Before Full Run:
1. **Test parallel processing** with 10 records, max_workers=5
2. **Test checkpoint/resume** by interrupting after 5 records, resuming
3. **Test error handling** with invalid records
4. **Test rate limiting** with max_workers=20

### Test Commands:
```bash
# Test with 10 records
head -11 data.csv > data_test.csv  # Header + 10 records

# Test parallel
python3 scripts/run_production_enrichment.py \
  --input data_test.csv \
  --output test_enriched.csv \
  --max-workers 5

# Test resume (kill with Ctrl+C after a few seconds)
python3 scripts/run_production_enrichment.py \
  --input data_test.csv \
  --output test_enriched.csv \
  --resume
```

---

## 🎯 Estimated Effort

**Implementation Time:** 1-2 hours
**Testing Time:** 30 minutes
**Total:** ~2 hours

**Complexity:** Medium
- Parallel processing: Straightforward with ThreadPoolExecutor
- Checkpoint system: Moderate - need atomic file updates
- Resume logic: Simple - filter by completed IDs
- Error handling: Well-defined patterns

---

## 📝 Additional Enhancements (Optional)

### Nice-to-Have Features (not critical for Phase 1):

1. **Batch Prioritization**
   - Process high-value records first
   - Skip low-priority records initially

2. **Quality Metrics Tracking**
   - Real-time confidence distribution
   - Search quality histogram
   - Fields found statistics

3. **Cost Tracking**
   - Real-time cost calculation
   - Budget warnings
   - Per-record cost analysis

4. **Webhook Notifications**
   - Slack/Discord notification when complete
   - Email summary report

5. **Dry Run Mode**
   - Estimate tokens and cost without running
   - Validate input data first

---

## 🚀 Next Steps

1. **Create `run_production_enrichment.py`**
   - Implement parallel processing
   - Implement checkpoint system
   - Add all CLI arguments

2. **Test with 10 records**
   - Verify parallel works
   - Verify resume works
   - Verify error handling

3. **Run Phase 1 (544 records)**
   - Start with max_workers=10 (conservative)
   - Monitor for rate limits
   - Increase to 20 if stable

4. **Review Results**
   - Quality check enriched data
   - Analyze errors
   - Decide on Phase 2 strategy

---

**Status:** Ready to implement
**Blocker:** None
**Dependencies:** None (uses existing `multi_stage_enrichment.py`)

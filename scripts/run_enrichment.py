#!/usr/bin/env python3
"""Minimal production enrichment runner. Compact output, parallel processing."""

import argparse
import csv
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Import the enricher
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.multi_stage_enrichment import MultiStageEnricher

# Globals for thread-safe operations
write_lock = Lock()
progress_lock = Lock()
stats = {"done": 0, "ok": 0, "fail": 0, "tokens": 0}


def enrich_one(enricher, record, idx, stages, delay, verbose=False):
    """Enrich single record. Returns (idx, result, error)."""
    try:
        if verbose:
            name = f"{record.get('poc.first_name', '')} {record.get('poc.last_name', '')}".strip()
            fund = record.get('fund.title', 'Unknown')
            print(f"\n[{idx}] Starting: {name} @ {fund}")

        result = enricher.enrich_record_multistage(
            record, stages=stages, delay_between_stages=delay
        )

        if verbose:
            tokens = result.get("total_tokens", 0)
            stages_done = len(result.get("stage_results", {}))
            print(f"[{idx}] ✓ Done: {stages_done} stages, {tokens:,} tokens")

        return (idx, result, None)
    except Exception as e:
        if verbose:
            import traceback
            print(f"\n[{idx}] ✗ ERROR: {e}")
            traceback.print_exc()
        return (idx, None, str(e))


def validate_and_clean(original, enriched):
    """Validate enriched data and flag/fix issues."""
    issues = []

    first_name = original.get('poc.first_name', '').lower()
    last_name = original.get('poc.last_name', '').lower()
    fund_name = original.get('fund.title', '').lower()

    # Validate POC LinkedIn - must contain part of person's name
    poc_linkedin = enriched.get('poc.linkedin', '')
    if poc_linkedin and '/in/' in poc_linkedin:
        username = poc_linkedin.split('/in/')[-1].strip('/').lower()
        if first_name and last_name:
            # Check if name appears in username
            if first_name not in username and last_name not in username:
                issues.append(f"POC LinkedIn mismatch: {poc_linkedin}")
                enriched['poc.linkedin'] = None  # Clear invalid

    # Validate Fund LinkedIn - must be /company/ not /in/
    fund_linkedin = enriched.get('fund.linkedin', '')
    if fund_linkedin and '/in/' in fund_linkedin:
        issues.append(f"Fund LinkedIn is personal profile: {fund_linkedin}")
        enriched['fund.linkedin'] = None  # Clear invalid

    # Flag empty descriptions
    if not enriched.get('poc.description'):
        issues.append("Missing POC description")

    return enriched, issues


def flatten_result(original, enriched):
    """Merge original + enriched into flat dict for CSV."""
    # First validate and clean
    enriched, issues = validate_and_clean(original, enriched)

    row = dict(original)
    for k, v in enriched.items():
        if k.startswith("_"):
            continue
        if isinstance(v, list):
            row[k] = "; ".join(str(x) for x in v) if v else ""
        elif v is not None:
            row[k] = v

    # Add issues column for review
    row['_validation_issues'] = "; ".join(issues) if issues else ""

    return row


def write_result(outfile, fieldnames, row):
    """Append one row to CSV (thread-safe)."""
    with write_lock:
        with open(outfile, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writerow(row)


def save_progress(progress_file, idx):
    """Save last completed index."""
    with progress_lock:
        with open(progress_file, "w") as f:
            f.write(str(idx))


def load_progress(progress_file):
    """Load last completed index, or -1 if none."""
    if os.path.exists(progress_file):
        with open(progress_file) as f:
            return int(f.read().strip())
    return -1


def print_status(total):
    """Print compact status line."""
    pct = (stats["done"] / total * 100) if total else 0
    sys.stdout.write(f"\r⚡ {stats['done']}/{total} ({pct:.0f}%) | ✓{stats['ok']} ✗{stats['fail']} | 🎫{stats['tokens']:,} tokens")
    sys.stdout.flush()


def main():
    p = argparse.ArgumentParser(description="Enrich CRM records with Gemini")
    p.add_argument("--input", "-i", default="data.csv", help="Input CSV")
    p.add_argument("--output", "-o", default="data_enriched.csv", help="Output CSV")
    p.add_argument("--progress", "-p", default=".enrichment_progress", help="Progress file")
    p.add_argument("--workers", "-w", type=int, default=5, help="Parallel workers")
    p.add_argument("--start", "-s", "--start-index", type=int, default=None, help="Start from row N (0-indexed)")
    p.add_argument("--limit", "-l", type=int, default=None, help="Process only N records")
    p.add_argument("--verbose", "-v", action="store_true", help="Verbose output with details per record")
    p.add_argument("--stages", default="poc,fund", help="Stages: poc,fund,deep")
    p.add_argument("--delay", "-d", type=int, default=2, help="Delay between stages (sec)")
    p.add_argument("--resume", "-r", action="store_true", help="Resume from progress file")
    p.add_argument("--model", "-m", default="gemini-2.5-pro",
                   help="Model: gemini-2.5-pro (recommended), gemini-2.0-flash (fast), gemini-3-pro-preview (slow)")
    args = p.parse_args()

    # Check API key
    if not os.environ.get("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not set")
        sys.exit(1)

    # Load records
    with open(args.input, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        records = list(reader)

    # Add enriched fields that may not exist in source
    enriched_fields = [
        "poc.description", "fund.description", "fund.thesis",
        "fund.portfolio_companies", "fund.aum", "fund.geographies",
        "_validation_issues"  # Track quality issues
    ]
    for f in enriched_fields:
        if f not in fieldnames:
            fieldnames.append(f)

    total_records = len(records)
    print(f"📂 Loaded {total_records} records from {args.input}")

    # Determine start index
    start_idx = 0
    if args.resume:
        start_idx = load_progress(args.progress) + 1
        print(f"🔄 Resuming from row {start_idx}")
    elif args.start is not None:
        start_idx = args.start

    # Filter records to process
    records_to_process = list(enumerate(records))[start_idx:]
    if args.limit:
        records_to_process = records_to_process[:args.limit]

    if not records_to_process:
        print("✅ Nothing to process")
        return

    print(f"🎯 Processing {len(records_to_process)} records (rows {start_idx}-{start_idx + len(records_to_process) - 1})")
    print(f"⚙️  Workers: {args.workers} | Stages: {args.stages} | Delay: {args.delay}s")

    # Prepare output file
    output_exists = os.path.exists(args.output)
    if not output_exists or start_idx == 0:
        # Write header
        with open(args.output, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

    # Initialize enricher
    enricher = MultiStageEnricher(model=args.model)
    stages = args.stages.split(",")

    print(f"🤖 Model: {args.model}")
    print(f"\n🚀 Starting...\n")
    start_time = time.time()

    # Process in parallel
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(enrich_one, enricher, rec, idx, stages, args.delay, args.verbose): idx
            for idx, rec in records_to_process
        }

        for future in as_completed(futures):
            idx, result, error = future.result()

            stats["done"] += 1

            if error:
                stats["fail"] += 1
                # Log error minimally
                with open("enrichment_errors.log", "a") as f:
                    f.write(f"{idx}|{error}\n")
            else:
                stats["ok"] += 1
                stats["tokens"] += result.get("total_tokens", 0)

                # Flatten and write
                row = flatten_result(result["original"], result["enriched"])
                write_result(args.output, fieldnames, row)

                # Save progress
                save_progress(args.progress, idx)

            if not args.verbose:
                print_status(len(records_to_process))

    # Final summary - visually distinct
    elapsed = time.time() - start_time
    tokens = stats['tokens']
    rate = stats['ok'] / elapsed if elapsed > 0 else 0

    # Cost calculation for gemini-2.5-pro (per 1M tokens)
    # <=200K context: Input $1.25/1M, Output $10.00/1M
    # Estimate ~20% input, ~80% output based on grounding response patterns
    input_tokens = tokens * 0.2
    output_tokens = tokens * 0.8
    cost = (input_tokens / 1_000_000 * 1.25) + (output_tokens / 1_000_000 * 10.00)

    print(f"\n\n")
    print(f"╔{'═'*62}╗")
    print(f"║{'✅  ENRICHMENT COMPLETE':^62}║")
    print(f"╠{'═'*62}╣")
    print(f"║                                                              ║")
    print(f"║   📊 Records     {stats['ok']:>6} success  │  {stats['fail']:>6} failed            ║")
    print(f"║   ⏱️  Duration    {elapsed:>6.1f}s  ({elapsed/60:.1f} min)                       ║")
    print(f"║   ⚡ Speed       {rate:>6.2f} records/sec                        ║")
    print(f"║   👷 Workers     {args.workers:>6}                                     ║")
    print(f"║   🤖 Model       {args.model:<40}  ║")
    print(f"║                                                              ║")
    print(f"╠{'─'*62}╣")
    print(f"║   🎫 Tokens      {tokens:>10,}                              ║")
    print(f"║   💰 Est. Cost   ${cost:>8.2f}  (input×$1.25 + output×$10/1M)   ║")
    print(f"╠{'─'*62}╣")
    print(f"║   📁 Output      {args.output:<43}║")
    print(f"║                                                              ║")
    print(f"╚{'═'*62}╝")


if __name__ == "__main__":
    main()

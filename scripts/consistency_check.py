#!/usr/bin/env python3
"""
Consolidated Consistency Check for data.csv
Combines vital tests from all analysis scripts into a compact validation/quality report.

Usage:
    python3 consistency_check.py [data.csv] [--json] [--verbose]
"""

import csv
import sys
import json
import re
from collections import Counter
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

# Expected URL patterns
LINKEDIN_PERSONAL_PATTERN = r'linkedin\.com/in/'
LINKEDIN_COMPANY_PATTERN = r'linkedin\.com/company/'
CRUNCHBASE_ORG_PATTERN = r'crunchbase\.com/organization/'

# Known country variations to flag
COUNTRY_VARIATIONS = {
    'usa': 'United States',
    'us': 'United States',
    'uk': 'United Kingdom',
    'uae': 'United Arab Emirates',
}

# Thresholds
QUALITY_THRESHOLDS = {
    'excellent': 90,
    'good': 75,
    'acceptable': 60,
    'poor': 40,
}

# ============================================================================
# VALIDATORS
# ============================================================================

def validate_email(email):
    """Basic email validation."""
    if not email:
        return True, None
    # Allow apostrophes and other valid email characters
    pattern = r'^[\w\.\-\+\']+@[\w\.\-]+\.\w+$'
    if re.match(pattern, email):
        return True, None
    return False, f"Invalid email format: {email}"

def validate_url(url, required_pattern=None, pattern_name=None):
    """Validate URL format and optional pattern."""
    if not url:
        return True, None

    issues = []

    # Check for basic URL structure
    if not re.match(r'^https?://', url):
        issues.append("Missing http(s):// protocol")

    # Check for spaces
    if ' ' in url or '\t' in url:
        issues.append("Contains whitespace")

    # Check required pattern
    if required_pattern and not re.search(required_pattern, url, re.IGNORECASE):
        issues.append(f"Expected {pattern_name} URL pattern")

    if issues:
        return False, '; '.join(issues)
    return True, None

def validate_linkedin_poc(url, first_name='', last_name=''):
    """Validate POC LinkedIn URL."""
    if not url:
        return True, None

    # Must be personal profile
    if '/company/' in url.lower():
        return False, "Company URL used for person (should be /in/)"

    if '/in/' not in url.lower():
        return False, "Not a valid LinkedIn profile URL"

    return True, None

def validate_linkedin_fund(url):
    """Validate Fund LinkedIn URL."""
    if not url:
        return True, None

    # Must be company profile
    if '/in/' in url.lower() and '/company/' not in url.lower():
        return False, "Personal URL used for company (should be /company/)"

    return True, None

def validate_crunchbase(url):
    """Validate Crunchbase URL."""
    if not url:
        return True, None

    if 'crunchbase.com' not in url.lower():
        return False, "Not a Crunchbase URL"

    if '/person/' in url.lower():
        return False, "Person URL used for fund (should be /organization/)"

    return True, None

def validate_phone(phone):
    """Basic phone validation."""
    if not phone:
        return True, None

    # Remove common formatting
    cleaned = re.sub(r'[\s\-\.\(\)]', '', phone)

    # Should have mostly digits
    digit_ratio = sum(c.isdigit() for c in cleaned) / len(cleaned) if cleaned else 0
    if digit_ratio < 0.7:
        return False, f"Unusual phone format: {phone}"

    return True, None

# ============================================================================
# ANALYSIS FUNCTIONS
# ============================================================================

def calculate_fill_rates(rows, headers):
    """Calculate fill rates for all fields."""
    field_stats = {}
    for field in headers:
        filled = sum(1 for r in rows if r.get(field, '').strip())
        field_stats[field] = {
            'filled': filled,
            'total': len(rows),
            'rate': filled / len(rows) * 100 if rows else 0
        }
    return field_stats

def find_duplicates(rows):
    """Find duplicate person+fund combinations."""
    seen = {}
    duplicates = []

    for i, row in enumerate(rows):
        key = (
            row.get('fund.title', '').lower().strip(),
            row.get('poc.first_name', '').lower().strip(),
            row.get('poc.last_name', '').lower().strip()
        )
        if key in seen:
            duplicates.append({
                'row': i + 2,  # 1-indexed + header
                'fund': row.get('fund.title', ''),
                'poc': f"{row.get('poc.first_name', '')} {row.get('poc.last_name', '')}",
                'first_seen': seen[key] + 2
            })
        else:
            seen[key] = i

    return duplicates

def check_country_consistency(rows):
    """Check for country naming inconsistencies."""
    countries = Counter(r.get('fund.country', '').strip() for r in rows if r.get('fund.country', '').strip())
    issues = []

    for country, count in countries.items():
        normalized = country.lower().strip()
        if normalized in COUNTRY_VARIATIONS:
            issues.append({
                'value': country,
                'count': count,
                'suggested': COUNTRY_VARIATIONS[normalized]
            })

    return issues

def check_city_consistency(rows):
    """Check for city naming issues."""
    cities = Counter(r.get('fund.city', '').strip() for r in rows if r.get('fund.city', '').strip())
    issues = []

    # Check for multiple cities in one field
    for city, count in cities.items():
        if ',' in city and city.count(',') > 0:
            # Might be "City, State" format - check if multiple cities
            parts = [p.strip() for p in city.split(',')]
            if len(parts) > 2:
                issues.append({
                    'value': city,
                    'count': count,
                    'issue': 'Multiple locations in city field'
                })

    return issues

def validate_all_records(rows):
    """Run all validators on all records."""
    record_issues = []

    for i, row in enumerate(rows):
        issues = []

        # Email validations
        valid, msg = validate_email(row.get('poc.email', ''))
        if not valid:
            issues.append(('poc.email', msg))

        valid, msg = validate_email(row.get('fund.email', ''))
        if not valid:
            issues.append(('fund.email', msg))

        # LinkedIn validations
        valid, msg = validate_linkedin_poc(
            row.get('poc.linkedin', ''),
            row.get('poc.first_name', ''),
            row.get('poc.last_name', '')
        )
        if not valid:
            issues.append(('poc.linkedin', msg))

        valid, msg = validate_linkedin_fund(row.get('fund.linkedin', ''))
        if not valid:
            issues.append(('fund.linkedin', msg))

        # Crunchbase validation
        valid, msg = validate_crunchbase(row.get('fund.crunchbase', ''))
        if not valid:
            issues.append(('fund.crunchbase', msg))

        # Phone validations
        valid, msg = validate_phone(row.get('poc.phone', ''))
        if not valid:
            issues.append(('poc.phone', msg))

        # Website validation
        website = row.get('fund.website', '').strip()
        if website and not re.match(r'^https?://', website):
            issues.append(('fund.website', 'Missing protocol'))

        if issues:
            record_issues.append({
                'row': i + 2,
                'fund': row.get('fund.title', ''),
                'poc': f"{row.get('poc.first_name', '')} {row.get('poc.last_name', '')}",
                'issues': issues
            })

    return record_issues

def calculate_quality_score(stats):
    """Calculate overall quality score."""
    score = 0
    max_score = 100

    # Fill rate (40 points)
    avg_fill = sum(s['rate'] for s in stats['fill_rates'].values()) / len(stats['fill_rates'])
    score += min(40, avg_fill * 0.4)

    # Key field completion (30 points)
    key_fields = ['poc.email', 'fund.website', 'poc.role', 'fund.sectors']
    key_avg = sum(stats['fill_rates'].get(f, {'rate': 0})['rate'] for f in key_fields) / len(key_fields)
    score += min(30, key_avg * 0.3)

    # Validation pass rate (30 points)
    total_records = stats['total_records']
    records_with_issues = len(stats['validation_issues'])
    pass_rate = (total_records - records_with_issues) / total_records * 100 if total_records else 0
    score += min(30, pass_rate * 0.3)

    return round(score, 1)

def get_grade(score):
    """Get letter grade from score."""
    if score >= 90:
        return 'A'
    elif score >= 80:
        return 'B'
    elif score >= 70:
        return 'C'
    elif score >= 60:
        return 'D'
    else:
        return 'F'

# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_report(filepath, verbose=False):
    """Generate comprehensive consistency report."""
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        headers = reader.fieldnames

    stats = {
        'file': filepath,
        'timestamp': datetime.now().isoformat(),
        'total_records': len(rows),
        'total_fields': len(headers),
    }

    # Fill rates
    stats['fill_rates'] = calculate_fill_rates(rows, headers)

    # Duplicates
    stats['duplicates'] = find_duplicates(rows)

    # Country/City consistency
    stats['country_issues'] = check_country_consistency(rows)
    stats['city_issues'] = check_city_consistency(rows)

    # Validation issues
    stats['validation_issues'] = validate_all_records(rows)

    # Existing validation issues from data
    existing_issues = Counter()
    for row in rows:
        issues = row.get('_validation_issues', '').strip()
        if issues:
            for issue in issues.split(';'):
                issue = issue.strip()
                if issue:
                    existing_issues[issue] += 1
    stats['existing_validation_issues'] = dict(existing_issues)

    # Quality score
    stats['quality_score'] = calculate_quality_score(stats)
    stats['grade'] = get_grade(stats['quality_score'])

    return stats

def print_report(stats, verbose=False):
    """Print formatted report."""
    print("=" * 70)
    print("DATA CONSISTENCY & QUALITY REPORT")
    print("=" * 70)
    print(f"File: {stats['file']}")
    print(f"Generated: {stats['timestamp']}")
    print(f"Records: {stats['total_records']} | Fields: {stats['total_fields']}")

    # Quality Score
    score = stats['quality_score']
    grade = stats['grade']
    print(f"\n{'─' * 70}")
    print(f"QUALITY SCORE: {score}/100 (Grade: {grade})")
    print(f"{'─' * 70}")

    bar_len = int(score / 2)
    bar = "█" * bar_len + "░" * (50 - bar_len)
    print(f"[{bar}]")

    # Summary Stats
    print(f"\n{'─' * 70}")
    print("SUMMARY")
    print(f"{'─' * 70}")

    # Key metrics
    total = stats['total_records']
    records_with_issues = len(stats['validation_issues'])
    clean_records = total - records_with_issues

    print(f"  Clean Records: {clean_records}/{total} ({clean_records/total*100:.1f}%)")
    print(f"  Records with Issues: {records_with_issues}/{total} ({records_with_issues/total*100:.1f}%)")
    print(f"  Duplicates: {len(stats['duplicates'])}")

    # Fill rate summary for key fields
    print(f"\n{'─' * 70}")
    print("KEY FIELD COMPLETION")
    print(f"{'─' * 70}")

    key_fields = [
        ('poc.email', 'POC Email'),
        ('poc.role', 'POC Role'),
        ('poc.linkedin', 'POC LinkedIn'),
        ('poc.description', 'POC Description'),
        ('fund.website', 'Fund Website'),
        ('fund.linkedin', 'Fund LinkedIn'),
        ('fund.crunchbase', 'Crunchbase'),
        ('fund.sectors', 'Sectors'),
    ]

    for field, label in key_fields:
        rate = stats['fill_rates'].get(field, {}).get('rate', 0)
        filled = stats['fill_rates'].get(field, {}).get('filled', 0)
        bar = "█" * int(rate / 5) + "░" * (20 - int(rate / 5))
        status = "✅" if rate >= 80 else "🟡" if rate >= 50 else "🔴"
        print(f"  {status} {label:20s} {bar} {rate:5.1f}% ({filled})")

    # Validation Issues Summary
    if stats['validation_issues']:
        print(f"\n{'─' * 70}")
        print(f"VALIDATION ISSUES ({len(stats['validation_issues'])} records)")
        print(f"{'─' * 70}")

        # Group by issue type
        issue_types = Counter()
        for record in stats['validation_issues']:
            for field, msg in record['issues']:
                issue_types[f"{field}: {msg}"] += 1

        for issue, count in issue_types.most_common(10):
            print(f"  • {issue}: {count}")

        if verbose:
            print(f"\n  Affected Records:")
            for record in stats['validation_issues'][:10]:
                issues_str = ', '.join(f"{f}" for f, m in record['issues'])
                print(f"    Row {record['row']}: {record['fund']} / {record['poc']} [{issues_str}]")
            if len(stats['validation_issues']) > 10:
                print(f"    ... and {len(stats['validation_issues']) - 10} more")

    # Existing validation issues from enrichment
    if stats['existing_validation_issues']:
        print(f"\n{'─' * 70}")
        print("PRE-EXISTING VALIDATION FLAGS (from enrichment)")
        print(f"{'─' * 70}")
        for issue, count in stats['existing_validation_issues'].items():
            print(f"  • {issue}: {count}")

    # Country/City Issues
    if stats['country_issues'] or stats['city_issues']:
        print(f"\n{'─' * 70}")
        print("LOCATION DATA ISSUES")
        print(f"{'─' * 70}")

        if stats['country_issues']:
            print(f"\n  Country Variations:")
            for issue in stats['country_issues']:
                print(f"    • '{issue['value']}' ({issue['count']}x) → suggest '{issue['suggested']}'")

        if stats['city_issues']:
            print(f"\n  City Issues:")
            for issue in stats['city_issues']:
                print(f"    • '{issue['value']}' ({issue['count']}x): {issue['issue']}")

    # Duplicates
    if stats['duplicates']:
        print(f"\n{'─' * 70}")
        print(f"DUPLICATE RECORDS ({len(stats['duplicates'])})")
        print(f"{'─' * 70}")
        for dup in stats['duplicates'][:5]:
            print(f"  Row {dup['row']}: {dup['fund']} / {dup['poc']} (first seen: row {dup['first_seen']})")
        if len(stats['duplicates']) > 5:
            print(f"  ... and {len(stats['duplicates']) - 5} more")

    # Recommendations
    print(f"\n{'─' * 70}")
    print("RECOMMENDATIONS")
    print(f"{'─' * 70}")

    recommendations = []

    # Based on issues found
    if records_with_issues > total * 0.1:
        recommendations.append("Review and fix validation issues in flagged records")

    if stats['duplicates']:
        recommendations.append(f"Remove or merge {len(stats['duplicates'])} duplicate records")

    if stats['country_issues']:
        recommendations.append("Standardize country names for consistency")

    # Based on fill rates
    low_fill_fields = [f for f, label in key_fields
                       if stats['fill_rates'].get(f, {}).get('rate', 0) < 50]
    if low_fill_fields:
        recommendations.append(f"Improve data collection for: {', '.join(low_fill_fields)}")

    # Check for HTTP URLs
    http_count = 0
    for row in stats.get('_rows', []):
        for field in ['poc.linkedin', 'fund.linkedin', 'fund.website', 'fund.crunchbase']:
            url = row.get(field, '')
            if url.startswith('http://') and not url.startswith('https://'):
                http_count += 1
    if http_count > 0:
        recommendations.append(f"Upgrade {http_count} HTTP URLs to HTTPS")

    if not recommendations:
        recommendations.append("Data quality is good. Continue regular maintenance.")

    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")

    # Final verdict
    print(f"\n{'=' * 70}")
    if score >= 85:
        print("✅ VERDICT: Data is HIGH QUALITY and ready for production use")
    elif score >= 70:
        print("🟡 VERDICT: Data is ACCEPTABLE with minor issues to address")
    elif score >= 55:
        print("🟠 VERDICT: Data needs IMPROVEMENT before production use")
    else:
        print("🔴 VERDICT: Data requires SIGNIFICANT cleanup")
    print(f"{'=' * 70}")

def main():
    """Main entry point."""
    filepath = 'data.csv'
    output_json = False
    verbose = False

    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == '--json':
            output_json = True
        elif arg == '--verbose' or arg == '-v':
            verbose = True
        elif not arg.startswith('-'):
            filepath = arg

    stats = generate_report(filepath, verbose)

    if output_json:
        # Clean up for JSON output
        output = {
            'file': stats['file'],
            'timestamp': stats['timestamp'],
            'total_records': stats['total_records'],
            'quality_score': stats['quality_score'],
            'grade': stats['grade'],
            'clean_records': stats['total_records'] - len(stats['validation_issues']),
            'records_with_issues': len(stats['validation_issues']),
            'duplicates': len(stats['duplicates']),
            'fill_rates': {k: round(v['rate'], 1) for k, v in stats['fill_rates'].items()},
            'validation_issues_count': len(stats['validation_issues']),
            'country_issues_count': len(stats['country_issues']),
            'city_issues_count': len(stats['city_issues']),
        }
        print(json.dumps(output, indent=2))
    else:
        print_report(stats, verbose)

if __name__ == '__main__':
    main()

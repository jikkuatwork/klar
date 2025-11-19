#!/usr/bin/env python3
"""
Comprehensive Data Quality Analysis for Family Office CRM
Analyzes the Excel file to determine data quality, completeness, and usability
"""

import zipfile
import xml.etree.ElementTree as ET
import re
from collections import defaultdict
from datetime import datetime
import json

class CRMDataAnalyzer:
    def __init__(self, excel_path):
        self.excel_path = excel_path
        self.shared_strings = []
        self.rows = []
        self.headers = []
        self.data_rows = []
        self.header_row_index = None

        # Analysis results
        self.stats = {
            'total_records': 0,
            'quality_tiers': defaultdict(int),
            'field_completeness': defaultdict(int),
            'field_validity': defaultdict(lambda: {'valid': 0, 'invalid': 0}),
            'duplicates': defaultdict(list),
            'misaligned_rows': [],
            'empty_critical_fields': defaultdict(int),
        }

    def load_data(self):
        """Load Excel data from xlsx file"""
        print("📂 Loading Excel file...")
        with zipfile.ZipFile(self.excel_path, 'r') as zip_ref:
            # Read shared strings
            try:
                shared_strings_xml = zip_ref.read('xl/sharedStrings.xml').decode('utf-8')
                strings_root = ET.fromstring(shared_strings_xml)
                for si in strings_root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'):
                    self.shared_strings.append(si.text if si.text else '')
                print(f"   ✓ Loaded {len(self.shared_strings)} shared strings")
            except Exception as e:
                print(f"   ⚠ Warning: Could not load shared strings: {e}")

            # Read worksheet
            sheet_xml = zip_ref.read('xl/worksheets/sheet1.xml').decode('utf-8')
            sheet_root = ET.fromstring(sheet_xml)

            rows = sheet_root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row')
            print(f"   ✓ Found {len(rows)} total rows")

            # Parse all rows
            for row_elem in rows:
                row_data = self._parse_row(row_elem)
                self.rows.append(row_data)

    def _parse_row(self, row_elem):
        """Parse a single row element"""
        cells = row_elem.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c')
        row_data = []

        # Track cell positions to handle gaps
        last_col = 0
        for cell in cells:
            # Get cell reference (e.g., "A1", "B1")
            cell_ref = cell.get('r')
            if cell_ref:
                col_letter = re.match(r'[A-Z]+', cell_ref).group()
                col_num = self._col_letter_to_num(col_letter)

                # Fill gaps with empty strings
                while last_col < col_num - 1:
                    row_data.append('')
                    last_col += 1

                last_col = col_num

            cell_type = cell.get('t')
            value_elem = cell.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')

            if value_elem is not None:
                value = value_elem.text
                # If it's a shared string, look it up
                if cell_type == 's' and self.shared_strings:
                    try:
                        value = self.shared_strings[int(value)]
                    except:
                        pass
                row_data.append(value if value else '')
            else:
                row_data.append('')

        return row_data

    def _col_letter_to_num(self, col):
        """Convert column letter to number (A=1, B=2, etc.)"""
        num = 0
        for c in col:
            num = num * 26 + (ord(c.upper()) - ord('A')) + 1
        return num

    def find_headers(self):
        """Identify the header row"""
        print("\n🔍 Identifying header row...")
        for i, row in enumerate(self.rows[:20]):  # Check first 20 rows
            row_text = ' '.join(str(v) for v in row).lower()
            if 'company name' in row_text and ('first name' in row_text or 'email' in row_text):
                self.header_row_index = i
                self.headers = [str(h).strip() if h else f'Column_{j}' for j, h in enumerate(row)]
                self.data_rows = self.rows[i+1:]
                print(f"   ✓ Found headers at row {i+1}")
                print(f"   ✓ Columns: {len(self.headers)}")
                print(f"   ✓ Data rows: {len(self.data_rows)}")
                return

        raise Exception("Could not find header row!")

    def validate_email(self, email):
        """Validate email format"""
        if not email or not isinstance(email, str):
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.strip()))

    def validate_url(self, url):
        """Validate URL format"""
        if not url or not isinstance(url, str):
            return False
        pattern = r'^https?://[^\s]+\.[^\s]+'
        return bool(re.match(pattern, url.strip()))

    def validate_phone(self, phone):
        """Validate phone number (basic check)"""
        if not phone or not isinstance(phone, str):
            return False
        # Remove common separators
        cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
        # Should have at least 7 digits
        return len(re.findall(r'\d', cleaned)) >= 7

    def analyze_quality(self):
        """Comprehensive quality analysis"""
        print("\n📊 Analyzing data quality...\n")

        # Define critical fields (indexes or names)
        critical_fields = ['Company Name', 'First Name', 'Last Name', 'Email contact person',
                          'Email company', 'Country/Region', 'Investor Type']

        email_fields = ['Email contact person', 'Email company']
        url_fields = ['Website', 'LinkedIn URL CP', 'Company Linkedin', 'Crunchbase profile Company']
        phone_fields = ['Phone Number CP', 'Office phone #']

        for row_idx, row in enumerate(self.data_rows):
            if not any(row):  # Skip completely empty rows
                continue

            record = {}
            field_scores = []
            issues = []

            # Map row to headers
            for col_idx, value in enumerate(row):
                header = self.headers[col_idx] if col_idx < len(self.headers) else f'Column_{col_idx}'
                record[header] = value

                # Track completeness
                if value and str(value).strip():
                    self.stats['field_completeness'][header] += 1

            # Check critical fields
            critical_filled = 0
            for field in critical_fields:
                if field in record and record[field] and str(record[field]).strip():
                    critical_filled += 1
                else:
                    self.stats['empty_critical_fields'][field] += 1
                    issues.append(f"Missing {field}")

            # Validate emails
            for field in email_fields:
                if field in record and record[field]:
                    if self.validate_email(str(record[field])):
                        self.stats['field_validity'][field]['valid'] += 1
                    else:
                        self.stats['field_validity'][field]['invalid'] += 1
                        issues.append(f"Invalid {field}")

            # Validate URLs
            for field in url_fields:
                if field in record and record[field]:
                    if self.validate_url(str(record[field])):
                        self.stats['field_validity'][field]['valid'] += 1
                    else:
                        self.stats['field_validity'][field]['invalid'] += 1
                        issues.append(f"Invalid {field}")

            # Validate phones
            for field in phone_fields:
                if field in record and record[field]:
                    if self.validate_phone(str(record[field])):
                        self.stats['field_validity'][field]['valid'] += 1
                    else:
                        self.stats['field_validity'][field]['invalid'] += 1

            # Check for misalignment (heuristic: if email field contains URL or vice versa)
            misaligned = False
            for email_field in email_fields:
                if email_field in record and record[email_field]:
                    val = str(record[email_field]).lower()
                    if 'http' in val or 'www.' in val or 'linkedin' in val:
                        misaligned = True
                        issues.append("Data misalignment detected")
                        break

            if misaligned:
                self.stats['misaligned_rows'].append(row_idx)

            # Check for duplicates (based on company name)
            company_name = record.get('Company Name', '')
            if company_name and str(company_name).strip():
                self.stats['duplicates'][str(company_name).strip().lower()].append(row_idx)

            # Quality tier classification
            completeness_score = critical_filled / len(critical_fields) if critical_fields else 0

            if completeness_score >= 0.85 and not misaligned and not any('Invalid' in i for i in issues):
                tier = 'Perfect'
            elif completeness_score >= 0.6 and not misaligned:
                tier = 'Good'
            elif completeness_score >= 0.3:
                tier = 'Fair'
            else:
                tier = 'Poor'

            self.stats['quality_tiers'][tier] += 1
            self.stats['total_records'] += 1

    def generate_report(self):
        """Generate comprehensive analysis report"""
        print("\n" + "="*80)
        print("📋 FAMILY OFFICE CRM - DATA QUALITY ANALYSIS REPORT")
        print("="*80)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"File: {self.excel_path}")
        print("="*80)

        # Overview
        print("\n📈 OVERVIEW")
        print("-" * 80)
        print(f"Total Records: {self.stats['total_records']:,}")
        print(f"Total Columns: {len(self.headers)}")
        print(f"Header Row: {self.header_row_index + 1}")

        # Column list
        print("\n📋 COLUMNS DETECTED")
        print("-" * 80)
        for i, header in enumerate(self.headers[:20], 1):  # Show first 20
            print(f"{i:2d}. {header}")
        if len(self.headers) > 20:
            print(f"    ... and {len(self.headers) - 20} more")

        # Quality Tiers
        print("\n⭐ QUALITY TIERS")
        print("-" * 80)
        for tier in ['Perfect', 'Good', 'Fair', 'Poor']:
            count = self.stats['quality_tiers'][tier]
            pct = (count / self.stats['total_records'] * 100) if self.stats['total_records'] > 0 else 0
            bar = '█' * int(pct / 2)
            print(f"{tier:8s}: {count:5,d} ({pct:5.1f}%) {bar}")

        # Completeness Analysis
        print("\n📊 FIELD COMPLETENESS (Top Critical Fields)")
        print("-" * 80)
        critical_fields = ['Company Name', 'First Name', 'Last Name', 'Email contact person',
                          'Email company', 'Country/Region', 'Investor Type', 'Website']

        for field in critical_fields:
            if field in self.stats['field_completeness']:
                count = self.stats['field_completeness'][field]
                pct = (count / self.stats['total_records'] * 100) if self.stats['total_records'] > 0 else 0
                bar = '█' * int(pct / 2)
                status = '✓' if pct > 70 else '⚠' if pct > 30 else '✗'
                print(f"{status} {field:25s}: {count:5,d} ({pct:5.1f}%) {bar}")

        # Validity Analysis
        print("\n✅ DATA VALIDITY")
        print("-" * 80)
        for field, validity in sorted(self.stats['field_validity'].items()):
            total = validity['valid'] + validity['invalid']
            if total > 0:
                valid_pct = (validity['valid'] / total * 100)
                status = '✓' if valid_pct > 80 else '⚠' if valid_pct > 50 else '✗'
                print(f"{status} {field:30s}: {validity['valid']:4,d} valid, {validity['invalid']:4,d} invalid ({valid_pct:.1f}% valid)")

        # Missing Critical Fields
        print("\n⚠️  MISSING CRITICAL FIELDS")
        print("-" * 80)
        for field in critical_fields:
            if field in self.stats['empty_critical_fields']:
                missing = self.stats['empty_critical_fields'][field]
                pct = (missing / self.stats['total_records'] * 100) if self.stats['total_records'] > 0 else 0
                if missing > 0:
                    print(f"{field:25s}: {missing:5,d} records missing ({pct:5.1f}%)")

        # Duplicates
        print("\n🔄 DUPLICATE ANALYSIS")
        print("-" * 80)
        duplicates = {k: v for k, v in self.stats['duplicates'].items() if len(v) > 1}
        print(f"Companies with duplicate entries: {len(duplicates):,}")
        print(f"Total duplicate records: {sum(len(v) - 1 for v in duplicates.values()):,}")

        if len(duplicates) > 0:
            print("\nTop 10 most duplicated:")
            sorted_dupes = sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)[:10]
            for company, indices in sorted_dupes:
                print(f"  • {company[:50]:50s}: {len(indices)} entries")

        # Misalignment
        print("\n🔀 DATA MISALIGNMENT")
        print("-" * 80)
        misaligned_count = len(self.stats['misaligned_rows'])
        pct = (misaligned_count / self.stats['total_records'] * 100) if self.stats['total_records'] > 0 else 0
        print(f"Rows with apparent misalignment: {misaligned_count:,} ({pct:.1f}%)")

        # Recommendations
        print("\n💡 RECOMMENDATIONS")
        print("=" * 80)

        perfect = self.stats['quality_tiers']['Perfect']
        good = self.stats['quality_tiers']['Good']
        fair = self.stats['quality_tiers']['Fair']
        poor = self.stats['quality_tiers']['Poor']

        usable = perfect + good
        usable_pct = (usable / self.stats['total_records'] * 100) if self.stats['total_records'] > 0 else 0

        print(f"\n1. USABLE DATASET (Perfect + Good quality)")
        print(f"   • {usable:,} records ({usable_pct:.1f}%) are immediately usable")
        print(f"   • This represents your 'clean' dataset for MVP")

        if fair > 0:
            fair_pct = (fair / self.stats['total_records'] * 100)
            print(f"\n2. RECOVERABLE DATA (Fair quality)")
            print(f"   • {fair:,} records ({fair_pct:.1f}%) could be cleaned with effort")
            print(f"   • Requires: Data cleaning, manual review, or enrichment")

        if poor > 0:
            poor_pct = (poor / self.stats['total_records'] * 100)
            print(f"\n3. LOW QUALITY DATA (Poor quality)")
            print(f"   • {poor:,} records ({poor_pct:.1f}%) have significant issues")
            print(f"   • Recommendation: Exclude from MVP, revisit later")

        if misaligned_count > 100:
            print(f"\n4. DATA ALIGNMENT ISSUE")
            print(f"   • ⚠️  {misaligned_count:,} rows show signs of column misalignment")
            print(f"   • This needs to be addressed before building the app")
            print(f"   • Recommendation: Clean data extraction or manual correction")

        print("\n5. STRATEGY")
        if usable_pct > 60:
            print("   ✓ GOOD NEWS: Majority of data is usable")
            print("   → Start with Perfect + Good records for MVP")
            print("   → Address Fair records in Phase 2")
        elif usable_pct > 30:
            print("   ⚠️  MODERATE: About half the data is immediately usable")
            print("   → Use Perfect + Good for MVP")
            print("   → Plan data cleaning sprint for Fair records")
        else:
            print("   ✗ CONCERN: Less than 30% of data is immediately usable")
            print("   → Recommend data cleanup before building")
            print("   → May need to revisit data collection process")

        # Export recommendations
        print("\n6. NEXT STEPS")
        print("   1. Export 'Perfect + Good' records to clean dataset")
        print("   2. Review sample of misaligned rows to understand pattern")
        print("   3. Decide on duplicate handling strategy")
        print("   4. Clean and standardize 'Fair' records if needed")
        print("   5. Build MVP with clean dataset")

        print("\n" + "="*80)
        print("END OF REPORT")
        print("="*80 + "\n")

    def export_summary_json(self, output_path):
        """Export summary statistics as JSON"""
        summary = {
            'generated': datetime.now().isoformat(),
            'total_records': self.stats['total_records'],
            'quality_tiers': dict(self.stats['quality_tiers']),
            'usable_count': self.stats['quality_tiers']['Perfect'] + self.stats['quality_tiers']['Good'],
            'usable_percentage': ((self.stats['quality_tiers']['Perfect'] + self.stats['quality_tiers']['Good']) / self.stats['total_records'] * 100) if self.stats['total_records'] > 0 else 0,
            'misaligned_rows': len(self.stats['misaligned_rows']),
            'duplicate_companies': len([k for k, v in self.stats['duplicates'].items() if len(v) > 1]),
            'completeness': {k: v for k, v in self.stats['field_completeness'].items()},
            'validity': {k: v for k, v in self.stats['field_validity'].items()},
        }

        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"📄 Summary exported to: {output_path}")

def main():
    excel_path = '/Users/bluebox/Projects/Silversky/analysis/koder/docs/CRM.xlsx'

    analyzer = CRMDataAnalyzer(excel_path)
    analyzer.load_data()
    analyzer.find_headers()
    analyzer.analyze_quality()
    analyzer.generate_report()
    analyzer.export_summary_json('crm_quality_summary.json')

if __name__ == '__main__':
    main()

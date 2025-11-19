#!/usr/bin/env python3
"""
Detailed investigation of specific data issues
Shows actual examples of misaligned data and duplicates
"""

import zipfile
import xml.etree.ElementTree as ET
import re
import csv
from collections import defaultdict

class DetailedInvestigator:
    def __init__(self, excel_path):
        self.excel_path = excel_path
        self.shared_strings = []
        self.rows = []
        self.headers = []
        self.data_rows = []

    def load_data(self):
        """Load Excel data"""
        with zipfile.ZipFile(self.excel_path, 'r') as zip_ref:
            # Read shared strings
            shared_strings_xml = zip_ref.read('xl/sharedStrings.xml').decode('utf-8')
            strings_root = ET.fromstring(shared_strings_xml)
            for si in strings_root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'):
                self.shared_strings.append(si.text if si.text else '')

            # Read worksheet
            sheet_xml = zip_ref.read('xl/worksheets/sheet1.xml').decode('utf-8')
            sheet_root = ET.fromstring(sheet_xml)
            rows = sheet_root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row')

            for row_elem in rows:
                row_data = self._parse_row(row_elem)
                self.rows.append(row_data)

    def _parse_row(self, row_elem):
        """Parse a single row"""
        cells = row_elem.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c')
        row_data = []
        last_col = 0

        for cell in cells:
            cell_ref = cell.get('r')
            if cell_ref:
                col_letter = re.match(r'[A-Z]+', cell_ref).group()
                col_num = self._col_letter_to_num(col_letter)
                while last_col < col_num - 1:
                    row_data.append('')
                    last_col += 1
                last_col = col_num

            cell_type = cell.get('t')
            value_elem = cell.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')

            if value_elem is not None:
                value = value_elem.text
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
        """Convert column letter to number"""
        num = 0
        for c in col:
            num = num * 26 + (ord(c.upper()) - ord('A')) + 1
        return num

    def find_headers(self):
        """Find header row"""
        for i, row in enumerate(self.rows[:20]):
            row_text = ' '.join(str(v) for v in row).lower()
            if 'company name' in row_text and 'first name' in row_text:
                self.headers = [str(h).strip() if h else f'Column_{j}' for j, h in enumerate(row)]
                self.data_rows = self.rows[i+1:]
                return

    def investigate_misalignment(self):
        """Find and show examples of misaligned data"""
        print("\n" + "="*80)
        print("🔍 MISALIGNMENT INVESTIGATION")
        print("="*80)

        misaligned_examples = []
        email_fields = ['Email contact person', 'Email company']

        for idx, row in enumerate(self.data_rows[:100]):  # Check first 100
            record = {}
            for col_idx, value in enumerate(row):
                header = self.headers[col_idx] if col_idx < len(self.headers) else f'Column_{col_idx}'
                record[header] = value

            # Check if email fields contain URLs
            for email_field in email_fields:
                if email_field in record and record[email_field]:
                    val = str(record[email_field]).lower()
                    if 'http' in val or 'linkedin' in val or 'www.' in val:
                        misaligned_examples.append((idx, record))
                        break

        print(f"\nFound {len(misaligned_examples)} misaligned rows in first 100 records")
        print("\n📋 SAMPLE MISALIGNED RECORDS (First 5):")
        print("-" * 80)

        for i, (idx, record) in enumerate(misaligned_examples[:5], 1):
            print(f"\n--- Example {i} (Row {idx + 7}) ---")
            print(f"Company Name: {record.get('Company Name', 'N/A')}")
            print(f"Investor Type: {record.get('Investor Type', 'N/A')}")
            print(f"First Name: {record.get('First Name', 'N/A')}")
            print(f"Last Name: {record.get('Last Name', 'N/A')}")
            print(f"Email contact: {record.get('Email contact person', 'N/A')[:80]}")
            print(f"Email company: {record.get('Email company', 'N/A')[:80]}")
            print(f"Website: {record.get('Website', 'N/A')[:80]}")
            print(f"Country: {record.get('Country/Region', 'N/A')}")

        print("\n💡 ANALYSIS:")
        print("The data shows column shift issues where:")
        print("  • LinkedIn URLs appear in Email fields")
        print("  • Country names appear in Email/Website fields")
        print("  • Data is shifted 1-2 columns to the left or right")

    def investigate_duplicates(self):
        """Analyze duplicate companies"""
        print("\n" + "="*80)
        print("🔄 DUPLICATE INVESTIGATION")
        print("="*80)

        company_records = defaultdict(list)

        for idx, row in enumerate(self.data_rows):
            if not any(row):
                continue

            record = {}
            for col_idx, value in enumerate(row):
                header = self.headers[col_idx] if col_idx < len(self.headers) else f'Column_{col_idx}'
                record[header] = value

            company_name = record.get('Company Name', '')
            if company_name and str(company_name).strip():
                company_records[str(company_name).strip().lower()].append((idx, record))

        # Find duplicates
        duplicates = {k: v for k, v in company_records.items() if len(v) > 1}

        print(f"\nTotal unique companies: {len(company_records)}")
        print(f"Companies with duplicates: {len(duplicates)}")
        print(f"Average duplicates per company: {sum(len(v) for v in duplicates.values()) / len(duplicates):.1f}")

        # Show example
        print("\n📋 EXAMPLE: Sequoia Financial Group (Most duplicated)")
        print("-" * 80)

        sequoia = [v for k, v in duplicates.items() if 'sequoia' in k]
        if sequoia:
            records = sequoia[0][:5]  # Show first 5
            for i, (idx, record) in enumerate(records, 1):
                print(f"\n--- Entry {i} ---")
                print(f"First Name: {record.get('First Name', 'N/A')}")
                print(f"Last Name: {record.get('Last Name', 'N/A')}")
                print(f"Role: {record.get('Role/Title', 'N/A')}")
                print(f"Email: {record.get('Email contact person', 'N/A')}")
                print(f"Country: {record.get('Country/Region', 'N/A')}")

        print("\n💡 DUPLICATE PATTERNS:")
        print("  1. Multiple contacts from same company (GOOD - keep all)")
        print("  2. Same person listed multiple times (BAD - dedupe)")
        print("  3. Data entry errors / variations in company name")

    def analyze_email_coverage(self):
        """Analyze email field coverage"""
        print("\n" + "="*80)
        print("📧 EMAIL COVERAGE ANALYSIS")
        print("="*80)

        has_contact_email = 0
        has_company_email = 0
        has_either_email = 0
        has_both_emails = 0
        has_no_email = 0
        valid_contact_email = 0
        valid_company_email = 0

        def validate_email(email):
            if not email or not isinstance(email, str):
                return False
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return bool(re.match(pattern, email.strip()))

        for row in self.data_rows:
            if not any(row):
                continue

            record = {}
            for col_idx, value in enumerate(row):
                header = self.headers[col_idx] if col_idx < len(self.headers) else f'Column_{col_idx}'
                record[header] = value

            contact_email = record.get('Email contact person', '')
            company_email = record.get('Email company', '')

            has_c = bool(contact_email and str(contact_email).strip())
            has_co = bool(company_email and str(company_email).strip())

            if has_c:
                has_contact_email += 1
                if validate_email(str(contact_email)):
                    valid_contact_email += 1

            if has_co:
                has_company_email += 1
                if validate_email(str(company_email)):
                    valid_company_email += 1

            if has_c and has_co:
                has_both_emails += 1
            elif has_c or has_co:
                has_either_email += 1
            else:
                has_no_email += 1

        total = len([r for r in self.data_rows if any(r)])

        print(f"\nEmail Field Population:")
        print(f"  Contact Email field: {has_contact_email:,} ({has_contact_email/total*100:.1f}%)")
        print(f"  Company Email field: {has_company_email:,} ({has_company_email/total*100:.1f}%)")
        print(f"\nEmail Validity:")
        print(f"  Valid Contact Emails: {valid_contact_email:,} ({valid_contact_email/has_contact_email*100 if has_contact_email else 0:.1f}% of populated)")
        print(f"  Valid Company Emails: {valid_company_email:,} ({valid_company_email/has_company_email*100 if has_company_email else 0:.1f}% of populated)")
        print(f"\nCoverage:")
        print(f"  Records with both emails: {has_both_emails:,} ({has_both_emails/total*100:.1f}%)")
        print(f"  Records with at least one: {has_either_email + has_both_emails:,} ({(has_either_email + has_both_emails)/total*100:.1f}%)")
        print(f"  Records with NO email: {has_no_email:,} ({has_no_email/total*100:.1f}%)")

        print("\n💡 IMPLICATION:")
        if has_no_email / total > 0.5:
            print("  ⚠️  Over 50% of records have no email - limits outreach capability")
        else:
            print("  ✓ Majority of records have at least some email contact info")

    def export_samples(self):
        """Export sample good and bad records to CSV"""
        print("\n" + "="*80)
        print("📤 EXPORTING SAMPLE DATA")
        print("="*80)

        # Collect samples
        perfect_samples = []
        fair_samples = []
        misaligned_samples = []

        for idx, row in enumerate(self.data_rows[:500]):  # Check first 500
            if not any(row):
                continue

            record = {}
            for col_idx, value in enumerate(row):
                header = self.headers[col_idx] if col_idx < len(self.headers) else f'Column_{col_idx}'
                record[header] = value

            record['_row_num'] = idx + 7  # Actual Excel row

            # Check quality
            critical_fields = ['Company Name', 'First Name', 'Last Name', 'Country/Region']
            filled = sum(1 for f in critical_fields if record.get(f, '').strip())

            # Check misalignment
            misaligned = False
            for email_field in ['Email contact person', 'Email company']:
                if email_field in record and record[email_field]:
                    val = str(record[email_field]).lower()
                    if 'http' in val or 'linkedin' in val:
                        misaligned = True

            if misaligned:
                if len(misaligned_samples) < 20:
                    misaligned_samples.append(record)
            elif filled >= 4:
                if len(perfect_samples) < 50:
                    perfect_samples.append(record)
            elif filled >= 2:
                if len(fair_samples) < 30:
                    fair_samples.append(record)

        # Export perfect samples
        if perfect_samples:
            with open('sample_perfect_records.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['_row_num'] + self.headers[:15], extrasaction='ignore')
                writer.writeheader()
                writer.writerows(perfect_samples)
            print(f"✓ Exported {len(perfect_samples)} perfect records → sample_perfect_records.csv")

        # Export misaligned samples
        if misaligned_samples:
            with open('sample_misaligned_records.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['_row_num'] + self.headers[:15], extrasaction='ignore')
                writer.writeheader()
                writer.writerows(misaligned_samples)
            print(f"✓ Exported {len(misaligned_samples)} misaligned records → sample_misaligned_records.csv")

        print("\n📁 Sample files created for customer review")

def main():
    excel_path = '/Users/bluebox/Projects/Silversky/analysis/koder/docs/CRM.xlsx'

    investigator = DetailedInvestigator(excel_path)
    investigator.load_data()
    investigator.find_headers()
    investigator.investigate_misalignment()
    investigator.investigate_duplicates()
    investigator.analyze_email_coverage()
    investigator.export_samples()

    print("\n" + "="*80)
    print("✅ INVESTIGATION COMPLETE")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()

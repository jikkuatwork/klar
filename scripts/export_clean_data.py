#!/usr/bin/env python3
"""
Export Clean Data to CSV
Extracts high-quality records (Perfect + Good) and exports to clean CSV format
with improved dot notation column names.
"""

import zipfile
import xml.etree.ElementTree as ET
import re
import csv
from collections import defaultdict

class CleanDataExporter:
    def __init__(self, excel_path):
        self.excel_path = excel_path
        self.shared_strings = []
        self.rows = []
        self.headers = []
        self.data_rows = []
        self.header_row_index = None

    def load_data(self):
        """Load Excel data from xlsx file"""
        print("📂 Loading Excel file...")
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

            # Parse all rows
            for row_elem in rows:
                row_data = self._parse_row(row_elem)
                self.rows.append(row_data)

        print(f"   ✓ Loaded {len(self.rows)} rows")

    def _parse_row(self, row_elem):
        """Parse a single row element"""
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
        """Convert column letter to number (A=1, B=2, etc.)"""
        num = 0
        for c in col:
            num = num * 26 + (ord(c.upper()) - ord('A')) + 1
        return num

    def find_headers(self):
        """Identify the header row"""
        print("\n🔍 Identifying header row...")
        for i, row in enumerate(self.rows[:20]):
            row_text = ' '.join(str(v) for v in row).lower()
            if 'company name' in row_text and 'first name' in row_text:
                self.header_row_index = i
                self.headers = [str(h).strip() if h else f'Column_{j}' for j, h in enumerate(row)]
                self.data_rows = self.rows[i+1:]
                print(f"   ✓ Found headers at row {i+1}")
                print(f"   ✓ Data rows: {len(self.data_rows)}")
                return

    def validate_email(self, email):
        """Validate email format"""
        if not email or not isinstance(email, str):
            return False
        email = email.strip()
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def validate_url(self, url):
        """Validate URL format"""
        if not url or not isinstance(url, str):
            return False
        url = url.strip()
        pattern = r'^https?://[^\s]+\.[^\s]+'
        return bool(re.match(pattern, url))

    def clean_value(self, value):
        """Clean and normalize a value"""
        if not value:
            return ''
        value = str(value).strip()
        # Remove extra whitespace
        value = ' '.join(value.split())
        return value

    def is_city_like(self, value):
        """Check if value looks like a city name"""
        if not value:
            return False
        value = str(value).strip()
        # Cities are typically short text without URLs
        if 'http' in value.lower() or 'linkedin' in value.lower() or 'www.' in value.lower():
            return False
        if len(value) > 50:
            return False
        return True

    def is_perfectly_aligned(self, record):
        """
        Check if record is perfectly aligned (TRULY STRICT)
        Returns True only if ALL fields are in correct columns
        """
        # Check Company Name (should NOT be URL or email)
        company = record.get('Company Name', '')
        if not company or not company.strip():
            return False
        if 'http' in company.lower() or 'linkedin.com' in company.lower() or 'www.' in company.lower() or '@' in company:
            return False

        # Check Investor Type (should NOT be URL or email)
        inv_type = record.get('Investor Type', '')
        if not inv_type or not inv_type.strip():
            return False
        if 'http' in inv_type.lower() or 'linkedin.com' in inv_type.lower() or 'www.' in inv_type.lower() or '@' in inv_type:
            return False

        # Check First Name (should NOT be URL or email)
        first_name = record.get('First Name', '')
        if not first_name or not first_name.strip():
            return False
        if 'http' in first_name.lower() or '@' in first_name or 'linkedin.com' in first_name.lower():
            return False
        if len(first_name) > 50:  # Names shouldn't be super long
            return False

        # Check Last Name (should NOT be URL or email)
        last_name = record.get('Last Name', '')
        if not last_name or not last_name.strip():
            return False
        if 'http' in last_name.lower() or '@' in last_name or 'linkedin.com' in last_name.lower():
            return False
        if len(last_name) > 50:
            return False

        # Check Role/Title (should NOT be URL or email)
        role = record.get('Role/Title', '')
        if role and role.strip():
            if 'http' in role.lower() or 'linkedin.com' in role.lower() or '@' in role:
                return False

        # Check Country (must exist, should NOT be URL)
        country = record.get('Country/Region', '')
        if not country or not country.strip():
            return False
        if 'http' in country.lower() or 'www.' in country.lower() or '@' in country:
            return False

        # Check Email fields (if present, must be valid emails, NOT URLs)
        for email_field in ['Email contact person', 'Email company']:
            email = record.get(email_field, '')
            if email and email.strip():
                if 'http' in email.lower() or 'linkedin.com' in email.lower() or 'www.' in email.lower():
                    return False

        # Check Sectors (should NOT have emails or weird URLs)
        sectors = record.get('Sectors', '')
        if sectors and sectors.strip():
            if '@' in sectors or 'http' in sectors.lower():
                return False

        # Check Stage (should NOT have emails or URLs)
        stage = record.get('Stage', '')
        if stage and stage.strip():
            if '@' in stage or 'http' in stage.lower():
                return False

        # Check City column (Column 10) - should be city-like, not URLs
        # This is the column with the misnamed header
        if len(record) > 9:
            city_col = list(record.values())[9] if len(list(record.values())) > 9 else ''
            if city_col and city_col.strip():
                if 'http' in city_col.lower() or 'linkedin.com' in city_col.lower():
                    return False

        # NEW: Check LinkedIn URL fields (must contain linkedin.com if not empty)
        linkedin_cp = record.get('LinkedIn URL CP', '')
        if linkedin_cp and linkedin_cp.strip():
            # If there's a value and it's a URL, it MUST be LinkedIn
            if 'http' in linkedin_cp.lower():
                if 'linkedin.com' not in linkedin_cp.lower():
                    return False  # URL but not LinkedIn
            elif 'crunchbase.com' in linkedin_cp.lower():
                return False  # Crunchbase in LinkedIn field

        # Check Company LinkedIn (Column 15)
        company_linkedin = record.get('Company Linkedin', '')
        if company_linkedin and company_linkedin.strip():
            # If there's a URL, it MUST be LinkedIn
            if 'http' in company_linkedin.lower():
                if 'linkedin.com' not in company_linkedin.lower():
                    return False
            elif 'crunchbase.com' in company_linkedin.lower():
                return False

        # Check Crunchbase field (must contain crunchbase.com if not empty)
        crunchbase = record.get('Crunchbase profile Company', '')
        if crunchbase and crunchbase.strip():
            # If there's a URL, it MUST be Crunchbase
            if 'http' in crunchbase.lower():
                if 'crunchbase.com' not in crunchbase.lower():
                    return False  # URL but not Crunchbase
            elif 'linkedin.com' in crunchbase.lower():
                return False  # LinkedIn in Crunchbase field

        # Check Website (must NOT be LinkedIn or Crunchbase)
        website = record.get('Website', '')
        if website and website.strip():
            if 'linkedin.com' in website.lower():
                return False  # LinkedIn in Website field
            if 'crunchbase.com' in website.lower():
                return False  # Crunchbase in Website field

        # All checks passed
        return True

    def classify_record_quality(self, record):
        """Classify record quality - now STRICT"""
        if self.is_perfectly_aligned(record):
            return 'Perfect'
        else:
            return 'Poor'  # Everything else is rejected

    def export_clean_csv(self, output_path):
        """Export clean data to CSV with new column names"""
        print("\n🔄 Processing and cleaning data...")

        # Column mapping: new_name -> old_index
        column_mapping = {
            'fund.title': 0,           # Company Name
            'fund.type': 1,            # Investor Type
            'poc.first_name': 2,       # First Name
            'poc.last_name': 3,        # Last Name
            'poc.role': 4,             # Role/Title
            'poc.email': 5,            # Email contact person
            'fund.email': 6,           # Email company
            'fund.website': 7,         # Website
            'fund.country': 8,         # Country/Region
            'fund.city': 9,            # Column 10 (city data!)
            'fund.sectors': 10,        # Sectors
            'fund.preferred_stage': 11, # Stage
            'poc.linkedin': 12,        # LinkedIn URL CP
            'fund.crunchbase': 13,     # Crunchbase profile Company
            'fund.linkedin': 14,       # Company Linkedin
            'poc.phone': 15,           # Phone Number CP
            'fund.phone': 16,          # Office phone #
        }

        new_headers = list(column_mapping.keys())
        clean_records = []

        stats = {
            'total': 0,
            'perfect': 0,
            'good': 0,
            'fair': 0,
            'poor': 0,
            'exported': 0,
            'city_fixed': 0,
            'email_validated': 0,
        }

        for row in self.data_rows:
            if not any(row):  # Skip empty rows
                continue

            stats['total'] += 1

            # Map row to original headers
            old_record = {}
            for col_idx, value in enumerate(row):
                header = self.headers[col_idx] if col_idx < len(self.headers) else f'Column_{col_idx}'
                old_record[header] = value

            # Classify quality (STRICT - only Perfect or Poor)
            quality = self.classify_record_quality(old_record)
            stats[quality.lower()] += 1

            # Only export Perfect (100% clean)
            if quality != 'Perfect':
                continue

            # Build new clean record
            clean_record = {}

            for new_col, old_idx in column_mapping.items():
                value = row[old_idx] if old_idx < len(row) else ''
                value = self.clean_value(value)

                # Special handling for specific fields
                if new_col == 'fund.city':
                    # Fix misaligned URLs in city field
                    if not self.is_city_like(value):
                        stats['city_fixed'] += 1
                        value = ''  # Clear non-city data

                elif new_col == 'poc.email' or new_col == 'fund.email':
                    # Validate email
                    if value and not self.validate_email(value):
                        # Check if it's actually a URL (misaligned)
                        if 'http' in value.lower() or 'linkedin' in value.lower():
                            value = ''  # Clear misaligned URL
                    if value and self.validate_email(value):
                        stats['email_validated'] += 1
                        value = value.lower()  # Normalize to lowercase

                elif new_col in ['fund.website', 'poc.linkedin', 'fund.crunchbase', 'fund.linkedin']:
                    # Validate URLs
                    if value and not self.validate_url(value):
                        # Check if it's not a URL but something else
                        if 'http' not in value.lower():
                            value = ''  # Clear non-URL data

                elif new_col == 'fund.country':
                    # Standardize country names
                    country_map = {
                        'usa': 'United States',
                        'us': 'United States',
                        'uk': 'United Kingdom',
                        'uae': 'United Arab Emirates',
                    }
                    value_lower = value.lower()
                    if value_lower in country_map:
                        value = country_map[value_lower]

                clean_record[new_col] = value

            clean_records.append(clean_record)
            stats['exported'] += 1

        # Write to CSV
        print(f"\n📝 Writing to {output_path}...")

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=new_headers)
            writer.writeheader()
            writer.writerows(clean_records)

        # Report
        print("\n" + "="*80)
        print("✅ EXPORT COMPLETE")
        print("="*80)
        print(f"Input records:       {stats['total']:,}")
        print(f"  Perfect quality:   {stats['perfect']:,}")
        print(f"  Good quality:      {stats['good']:,}")
        print(f"  Fair quality:      {stats['fair']:,}")
        print(f"  Poor quality:      {stats['poor']:,}")
        print(f"\nExported records:    {stats['exported']:,}")
        print(f"City field fixed:    {stats['city_fixed']:,}")
        print(f"Emails validated:    {stats['email_validated']:,}")
        print(f"\nOutput file:         {output_path}")

        # File size
        import os
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"File size:           {size_mb:.2f} MB")
        print("="*80)

        return stats

def main():
    excel_path = '/Users/bluebox/Projects/Silversky/analysis/koder/docs/CRM.xlsx'
    output_path = '/Users/bluebox/Projects/Silversky/analysis/data.csv'

    exporter = CleanDataExporter(excel_path)
    exporter.load_data()
    exporter.find_headers()
    stats = exporter.export_clean_csv(output_path)

    print("\n💡 Next Steps:")
    print("   1. Review data.csv to verify quality")
    print("   2. Open in Excel/Google Sheets to spot check")
    print("   3. Use for static web app development")
    print(f"   4. {stats['fair']:,} Fair quality records available for Phase 2")
    print("\n✨ Ready to build!")

if __name__ == '__main__':
    main()

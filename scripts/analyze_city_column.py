#!/usr/bin/env python3
"""
Analyze Column 10 to understand the city data pattern
"""

import zipfile
import xml.etree.ElementTree as ET
import re
from collections import Counter

def parse_xlsx():
    excel_path = '/Users/bluebox/Projects/Silversky/analysis/koder/docs/CRM.xlsx'

    with zipfile.ZipFile(excel_path, 'r') as zip_ref:
        # Read shared strings
        shared_strings_xml = zip_ref.read('xl/sharedStrings.xml').decode('utf-8')
        strings_root = ET.fromstring(shared_strings_xml)
        shared_strings = []
        for si in strings_root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'):
            shared_strings.append(si.text if si.text else '')

        # Read worksheet
        sheet_xml = zip_ref.read('xl/worksheets/sheet1.xml').decode('utf-8')
        sheet_root = ET.fromstring(sheet_xml)
        rows = sheet_root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row')

        def parse_row(row_elem):
            cells = row_elem.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c')
            row_data = []
            last_col = 0

            for cell in cells:
                cell_ref = cell.get('r')
                if cell_ref:
                    col_letter = re.match(r'[A-Z]+', cell_ref).group()
                    col_num = sum((ord(c) - ord('A') + 1) * (26 ** i) for i, c in enumerate(reversed(col_letter)))
                    while last_col < col_num - 1:
                        row_data.append('')
                        last_col += 1
                    last_col = col_num

                cell_type = cell.get('t')
                value_elem = cell.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')

                if value_elem is not None:
                    value = value_elem.text
                    if cell_type == 's' and shared_strings:
                        try:
                            value = shared_strings[int(value)]
                        except:
                            pass
                    row_data.append(value if value else '')
                else:
                    row_data.append('')

            return row_data

        # Find header row
        header_idx = None
        for i, row in enumerate(rows[:20]):
            row_data = parse_row(row)
            row_text = ' '.join(str(v) for v in row_data).lower()
            if 'company name' in row_text:
                header_idx = i
                break

        data_rows = rows[header_idx + 1:]

        print("="*80)
        print("ANALYZING COLUMN 10 (Suspected City Field)")
        print("="*80)

        col_10_values = []
        has_url = 0
        has_city_like = 0
        empty = 0

        print("\nSample values from Column 10 (first 50 records):\n")

        for i, row_elem in enumerate(data_rows[:50], 1):
            row_data = parse_row(row_elem)
            if len(row_data) > 9:
                val = row_data[9]  # Column 10 is index 9
                if val:
                    col_10_values.append(val)
                    value_str = str(val)

                    # Classify
                    if 'http' in value_str.lower() or 'linkedin' in value_str.lower():
                        has_url += 1
                        marker = "[URL]"
                    elif len(value_str) < 50 and ',' not in value_str:
                        has_city_like += 1
                        marker = "[CITY?]"
                    else:
                        marker = "[OTHER]"

                    print(f"{i:3d}. {marker:8s} {value_str[:70]}")
                else:
                    empty += 1

        print("\n" + "="*80)
        print("STATISTICS FOR COLUMN 10:")
        print("="*80)
        print(f"Total records analyzed: 50")
        print(f"Empty: {empty}")
        print(f"Contains URL: {has_url}")
        print(f"City-like (short text): {has_city_like}")

        # Analyze all data
        print("\n" + "="*80)
        print("ANALYZING ALL RECORDS IN COLUMN 10:")
        print("="*80)

        all_values = []
        url_count = 0
        city_count = 0
        empty_count = 0

        for row_elem in data_rows:
            row_data = parse_row(row_elem)
            if len(row_data) > 9:
                val = row_data[9]
                if val:
                    all_values.append(str(val))
                    val_str = str(val)
                    if 'http' in val_str.lower() or 'linkedin' in val_str.lower():
                        url_count += 1
                    elif len(val_str) < 50:
                        city_count += 1
                else:
                    empty_count += 1

        total = len(data_rows)
        print(f"\nTotal data rows: {total}")
        print(f"Empty: {empty_count} ({empty_count/total*100:.1f}%)")
        print(f"Contains URLs: {url_count} ({url_count/total*100:.1f}%)")
        print(f"City-like (short text): {city_count} ({city_count/total*100:.1f}%)")

        # Show most common city-like values
        city_like = [v for v in all_values if len(v) < 50 and 'http' not in v.lower()]
        city_counter = Counter(city_like)

        print("\n" + "="*80)
        print("TOP 30 MOST COMMON CITY-LIKE VALUES:")
        print("="*80)
        for city, count in city_counter.most_common(30):
            print(f"{count:4d}x  {city}")

if __name__ == '__main__':
    parse_xlsx()

#!/usr/bin/env python3
"""
Carefully examine all columns in the Excel file
"""

import zipfile
import xml.etree.ElementTree as ET
import re

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
        header_row = None
        header_idx = None
        for i, row in enumerate(rows[:20]):
            row_data = parse_row(row)
            row_text = ' '.join(str(v) for v in row_data).lower()
            if 'company name' in row_text and 'first name' in row_text:
                header_row = row_data
                header_idx = i
                break

        if not header_row:
            print("Could not find header row!")
            return

        print(f"Found header row at index {header_idx + 1}")
        print(f"Total columns: {len(header_row)}")
        print("\n" + "="*80)
        print("ALL COLUMNS IN ORDER:")
        print("="*80)

        for i, col in enumerate(header_row, 1):
            col_name = str(col).strip() if col else f'[EMPTY_{i}]'
            print(f"{i:2d}. {col_name}")

        # Show sample data for each column
        print("\n" + "="*80)
        print("SAMPLE DATA FOR EACH COLUMN (first 3 records):")
        print("="*80)

        data_rows = rows[header_idx + 1:header_idx + 4]

        for col_idx, col_name in enumerate(header_row):
            col_name_display = str(col_name).strip() if col_name else f'[EMPTY_{col_idx+1}]'
            print(f"\n--- Column {col_idx + 1}: {col_name_display} ---")

            for record_num, row_elem in enumerate(data_rows, 1):
                row_data = parse_row(row_elem)
                value = row_data[col_idx] if col_idx < len(row_data) else ''
                value_display = str(value)[:100] if value else '[empty]'
                print(f"  Record {record_num}: {value_display}")

if __name__ == '__main__':
    parse_xlsx()

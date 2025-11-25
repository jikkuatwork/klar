#!/usr/bin/env python3
"""Transform country and city fields to standardized codes.

- fund.country → ISO 3166-1 alpha-2 (e.g., "US", "GB", "CH")
- fund.city → UN/LOCODE 3-letter city code (e.g., "NYC", "LON", "ZRH")
"""

import csv
import sys

# ISO 3166-1 alpha-2 country codes
COUNTRY_TO_ISO = {
    "Andorra": "AD",
    "Australia": "AU",
    "Austria": "AT",
    "Bahrain": "BH",
    "Belgium": "BE",
    "Belguim": "BE",  # Typo in data
    "Canada": "CA",
    "China": "CN",
    "Cyprus": "CY",
    "Denmark": "DK",
    "Egypt": "EG",
    "Finland": "FI",
    "France": "FR",
    "Germany": "DE",
    "Hong Kong": "HK",
    "India": "IN",
    "Israel": "IL",
    "Italy": "IT",
    "Kuwait": "KW",
    "Lithuania": "LT",
    "Luxembourg": "LU",
    "Monaco": "MC",
    "Netherlands": "NL",
    "New York": "US",  # State listed as country
    "Norway": "NO",
    "Poland": "PL",
    "Portugal": "PT",
    "Romania": "RO",
    "Saudi Arabia": "SA",
    "Singapore": "SG",
    "Spain": "ES",
    "Sweden": "SE",
    "Switzerland": "CH",
    "United Arab Emirates": "AE",
    "United Kingdom": "UK",
    "United States": "US",
    "Brazil": "BR",
}

# UN/LOCODE city codes (3-letter portion)
CITY_TO_LOCODE = {
    # India
    "Ahmedabad": "AMD",
    "Bengaluru": "BLR",
    "Mumbai": "BOM",

    # Netherlands
    "Amsterdam": "AMS",
    "Arnhem": "ARN",
    "De Nijensteen": "AMS",
    "Maastricht": "MST",
    "Nieuwkuijk": "NKJ",
    "Oisterwijk": "OIJ",
    "Rhenen": "RHN",
    "The Hague": "HAG",

    # Andorra
    "Andorra la Vella": "ALV",

    # United States
    "Atlanta": "ATL",
    "Austin": "AUS",
    "Avon": "AVN",
    "Baltimore": "BAL",
    "Bangor": "BGR",
    "Bay Harbor Islands": "MIA",
    "Bellevue": "BVU",
    "Bethesda": "BES",
    "Beverly": "BVY",
    "Boise": "BOI",
    "Boston": "BOS",
    "Boulder": "BOU",
    "Bryn Mawr": "BWR",
    "Cedar Knolls": "CDK",
    "Champaign": "CMI",
    "Chapel Hill": "CHP",
    "Charlotte": "CLT",
    "Chicago": "CHI",
    "Cincinnati": "CVG",
    "Cleveland": "CLE",
    "Columbia": "CAE",
    "Coral Gables": "CGB",
    "Cypress": "CYP",
    "Dallas": "DFW",
    "Delray Beach": "DRB",
    "Denver": "DEN",
    "Devon": "DVN",
    "Encino": "ENC",
    "Estero": "EST",
    "Farmington": "FAR",
    "Fayetteville": "FYV",
    "Fort Wayne": "FWA",
    "Fort Worth": "FTW",
    "Grand Rapids": "GRR",
    "Grapevine": "GPV",
    "Greenville": "GVL",
    "Greenwich": "GRW",
    "Houston": "HOU",
    "Hunt Valley": "HVY",
    "Huntsville": "HSV",
    "Irvington": "IRV",
    "Jackson": "JAN",
    "Johnson City": "JCY",
    "Knoxville": "TYS",
    "Los Angeles": "LAX",
    "Manchester": "MHT",
    "Massachusetts": "BOS",
    "McLean": "MCL",
    "Memphis": "MEM",
    "Menlo Park": "MPK",
    "Mesa": "MSA",
    "Miami": "MIA",
    "Miami Beach": "MIB",
    "Minneapolis": "MSP",
    "Montecito": "MTC",
    "Naples": "APF",
    "New Canaan": "NCA",
    "New York": "NYC",
    "Nicosia": "NIC",
    "North York": "NYK",
    "Northbrook": "NBK",
    "Oklahoma City": "OKC",
    "Ottawa": "OTT",
    "Palm Harbor": "PHB",
    "Pasadena": "PSD",
    "Philadelphia": "PHL",
    "Plymouth Meeting": "PLY",
    "Raleigh": "RDU",
    "Redwood City": "RWC",
    "Reno": "RNO",
    "Rockville": "RKV",
    "Saint Louis": "STL",
    "San Francisco": "SFO",
    "Seattle": "SEA",
    "Spokane": "GEG",
    "St. Louis": "STL",
    "São Paulo": "SAO",
    "Tampa": "TPA",
    "Thibodaux": "TBD",
    "Tysons": "TYS",
    "West Chester": "WCH",
    "West Palm Beach": "PBI",
    "Winston-Salem": "INT",
    "Winter Park": "WPK",
    "Woodbridge": "WBR",

    # Germany
    "Baden-Baden": "BAD",
    "Balgheim": "BGH",
    "Berlin": "BER",
    "Cologne": "CGN",
    "Dresden": "DRS",
    "Dusseldorf": "DUS",
    "Frankfurt": "FRA",
    "Frankfurt, New York": "FRA",
    "Grünwald": "GRW",
    "Hamburg": "HAM",
    "Luzern": "LUZ",
    "Munich": "MUC",
    "Ulm": "ULM",
    "Wiesbaden": "WIE",

    # Spain
    "Barcelona": "BCN",

    # Switzerland
    "Basel": "BSL",
    "Bottighofen": "BTG",
    "Cham": "CHM",
    "Delémont": "DLE",
    "Geneva": "GVA",
    "Jona": "JNA",
    "Kusnacht": "KUS",
    "Lausanne": "LSN",
    "Lugano": "LUG",
    "Malmö": "MMA",
    "Pfaeffikon": "PFA",
    "Rapperswil-Jona": "RJN",
    "Zug": "ZUG",
    "Zurich": "ZRH",

    # Romania
    "Bucharest": "BUH",

    # Canada
    "Calgary": "YYC",
    "Montreal": "YMQ",
    "Saskatoon": "YXE",
    "Toronto": "YYZ",

    # Egypt
    "Carlsbad": "CBD",

    # Denmark
    "Copenhagen": "CPH",
    "Hørsholm": "HOR",

    # Belgium
    "Dilbeek": "DIL",

    # UAE
    "Dubai": "DXB",
    "Kuwait City": "KWI",

    # UK
    "Dundonald": "DUN",
    "Edinburgh": "EDI",
    "London": "LON",
    "Oxford": "OXF",
    "Richmond": "RIC",

    # Italy
    "Florence": "FLR",
    "Milan": "MIL",

    # Australia
    "Goodwood": "GWD",
    "Sydney": "SYD",

    # Finland
    "Helsinki": "HEL",

    # Hong Kong
    "Hong Kong": "HKG",

    # Saudi Arabia
    "Jeddah": "JED",

    # Bahrain
    "Manama": "BAH",

    # Monaco
    "Monaco": "MCM",

    # Portugal
    "Mozelos": "MOZ",

    # Norway
    "Oslo": "OSL",

    # France
    "Paris": "PAR",
    "Roubaix": "RBX",

    # Israel
    "Ramat Gan": "RMG",

    # China
    "Shanghai": "SHA",

    # Singapore
    "Singapore": "SIN",

    # Sweden
    "Stockholm": "STO",
    "Umea": "UME",

    # Austria
    "Vienna": "VIE",

    # Lithuania
    "Vilnius": "VNO",

    # Poland
    "Wrocław": "WRO",

    # Luxembourg
    "Luxembourg": "LUX",
}


def transform_data(input_file, output_file):
    """Transform country and city fields to standardized codes."""

    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    stats = {
        'total': len(rows),
        'countries_mapped': 0,
        'cities_mapped': 0,
        'countries_unmapped': [],
        'cities_unmapped': [],
        'bad_rows': [],
    }

    transformed_rows = []

    for i, row in enumerate(rows):
        country = row.get('fund.country', '').strip()
        city = row.get('fund.city', '').strip()

        # Check for bad data (non-country values)
        if country and country not in COUNTRY_TO_ISO:
            # Check if it looks like a name (bad data)
            if ' ' in country and country.split()[0][0].isupper():
                words = country.split()
                if len(words) == 2 and all(w[0].isupper() for w in words):
                    # Looks like a person's name - bad row
                    stats['bad_rows'].append((i, country))
                    continue
            stats['countries_unmapped'].append(country)

        # Transform country
        if country in COUNTRY_TO_ISO:
            row['fund.country'] = COUNTRY_TO_ISO[country]
            stats['countries_mapped'] += 1
        elif country:
            stats['countries_unmapped'].append(country)

        # Transform city
        if city in CITY_TO_LOCODE:
            row['fund.city'] = CITY_TO_LOCODE[city]
            stats['cities_mapped'] += 1
        elif city:
            stats['cities_unmapped'].append(city)

        transformed_rows.append(row)

    # Write output
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(transformed_rows)

    return stats


def main():
    input_file = 'data.csv'
    output_file = 'data_transformed.csv'

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    print(f"📂 Transforming {input_file} → {output_file}")
    print()

    stats = transform_data(input_file, output_file)

    print(f"📊 Results:")
    print(f"   Total rows: {stats['total']}")
    print(f"   Countries mapped: {stats['countries_mapped']}")
    print(f"   Cities mapped: {stats['cities_mapped']}")

    if stats['bad_rows']:
        print(f"\n⚠️  Bad rows removed: {len(stats['bad_rows'])}")
        for idx, val in stats['bad_rows']:
            print(f"   Row {idx}: fund.country = '{val}'")

    if stats['countries_unmapped']:
        unique = list(set(stats['countries_unmapped']))
        print(f"\n❌ Unmapped countries: {unique}")

    if stats['cities_unmapped']:
        unique = list(set(stats['cities_unmapped']))
        print(f"\n❌ Unmapped cities: {unique}")

    if not stats['countries_unmapped'] and not stats['cities_unmapped']:
        print(f"\n✅ All locations successfully standardized!")
        print(f"   Output: {output_file}")
        print(f"   Records: {len(stats['bad_rows'])} removed, {stats['total'] - len(stats['bad_rows'])} remaining")


if __name__ == '__main__':
    main()

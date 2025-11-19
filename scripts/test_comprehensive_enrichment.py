#!/usr/bin/env python3
"""
Test comprehensive record enrichment with Gemini
- Sends full record as JSON
- Gets back enriched record with all fields filled
- Adds poc.description
- Converts sectors to standardized arrays
- Validates/corrects existing data
"""

import json
import csv
import os
import urllib.request
import time

class ComprehensiveEnricher:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get('GEMINI_API_KEY')
        if not self.api_key:
            raise Exception("GEMINI_API_KEY environment variable required")

        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.model = "gemini-3-pro-preview"

        # Standardized sector list
        self.standard_sectors = [
            "venture-capital", "private-equity", "hedge-funds", "real-estate",
            "technology", "healthcare", "fintech", "cleantech", "biotech",
            "consumer", "enterprise-software", "ai-ml", "crypto-blockchain",
            "infrastructure", "energy", "manufacturing", "retail", "hospitality",
            "education", "media", "telecommunications", "agriculture", "transportation",
            "aerospace", "defense", "public-markets", "fixed-income", "commodities",
            "impact-investing", "esg", "sustainable-finance"
        ]

    def build_enrichment_prompt(self, record):
        """Build comprehensive enrichment prompt"""

        prompt = f"""You are a professional data enrichment specialist. I'm providing an investor contact record that needs enrichment.

CURRENT RECORD (JSON):
{json.dumps(record, indent=2)}

YOUR TASK:
Using Google Search, enrich this record by:

1. **Fill Missing Fields:**
   - If fund.linkedin is empty/missing, find the official LinkedIn company page
   - If fund.crunchbase is empty/missing, find the Crunchbase organization page
   - If fund.website is empty/missing, find the official website
   - If fund.city is empty, try to determine it from company info
   - If fund.sectors is empty, research and populate

2. **Add poc.description:**
   Create a concise 2-3 sentence professional summary of the contact person including:
   - Their role and expertise
   - Years of experience (if findable)
   - Key focus areas or specializations
   - Notable background (if relevant)

   Example: "Managing Partner with 15+ years in venture capital, focusing on early-stage SaaS and fintech investments. Previously led investments at Sequoia Capital and holds an MBA from Stanford."

3. **Standardize fund.sectors:**
   Convert to an array using ONLY these standardized values:
   {', '.join(self.standard_sectors[:15])}... (and similar)

   - Map existing values to closest standard sectors
   - Add any sectors found through research
   - Return as array (e.g., ["venture-capital", "technology", "healthcare"])

4. **Validate & Correct:**
   - Verify all URLs are correct and working
   - Fix any obviously wrong data (like sample #2 in our test)
   - Standardize URL formats (https, no trailing slashes unless needed)

RULES:
- Only add data you find with HIGH confidence
- Use null for fields you cannot verify
- For poc.description, write in third person, professional tone
- For sectors, only use the standardized list provided
- Verify all URLs are official and correct

RETURN FORMAT:
Return ONLY a valid JSON object with this exact structure:
{{
  "fund.title": "string",
  "fund.type": "string",
  "poc.first_name": "string",
  "poc.last_name": "string",
  "poc.role": "string",
  "poc.email": "string or null",
  "poc.description": "string (NEW - your generated description)",
  "fund.email": "string or null",
  "fund.website": "string or null",
  "fund.country": "string",
  "fund.city": "string or null",
  "fund.sectors": ["array", "of", "standardized", "sectors"],
  "fund.preferred_stage": "string or null",
  "poc.linkedin": "string or null",
  "fund.crunchbase": "string or null",
  "fund.linkedin": "string or null",
  "poc.phone": "string or null",
  "fund.phone": "string or null",
  "_enrichment_meta": {{
    "confidence": "high|medium|low",
    "fields_added": ["list of new fields added"],
    "fields_corrected": ["list of corrected fields"],
    "notes": "brief explanation of enrichment"
  }}
}}

IMPORTANT: Return ONLY the JSON, no additional text or explanation."""

        return prompt

    def call_gemini(self, prompt):
        """Call Gemini API"""
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

        request_body = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 4000
            },
            "tools": [
                {
                    "googleSearch": {}
                }
            ]
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(request_body).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )

        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))

                if 'candidates' in result and len(result['candidates']) > 0:
                    content = result['candidates'][0]['content']['parts'][0]['text']
                    metadata = result.get('usageMetadata', {})

                    return {
                        'content': content,
                        'tokens': metadata.get('totalTokenCount', 0)
                    }
                else:
                    return {'error': 'No candidates returned'}

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            return {'error': f'HTTP {e.code}: {error_body}'}
        except Exception as e:
            return {'error': str(e)}

    def extract_json(self, content):
        """Extract JSON from response"""
        import re

        # Remove markdown code blocks
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            parts = content.split('```')
            if len(parts) >= 3:
                content = parts[1].strip()

        # Try to find JSON object
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            content = json_match.group(0)

        return json.loads(content)

    def enrich_record(self, record):
        """Enrich a single record comprehensively"""

        company_name = record.get('fund.title', 'Unknown')

        print(f"\n{'='*80}")
        print(f"ENRICHING: {company_name}")
        print(f"Type: {record.get('fund.type', 'N/A')} | Country: {record.get('fund.country', 'N/A')}")
        print(f"Contact: {record.get('poc.first_name', '')} {record.get('poc.last_name', '')}")
        print(f"{'='*80}")

        # Show current state
        print(f"\nCURRENT STATE:")
        print(f"  LinkedIn: {record.get('fund.linkedin', '(empty)')[:50]}")
        print(f"  Crunchbase: {record.get('fund.crunchbase', '(empty)')[:50]}")
        print(f"  Website: {record.get('fund.website', '(empty)')[:50]}")
        print(f"  Sectors: {record.get('fund.sectors', '(empty)')[:60]}")
        print(f"  Description: {record.get('poc.description', '(empty)')}")

        # Build prompt
        prompt = self.build_enrichment_prompt(record)

        # Call API
        result = self.call_gemini(prompt)

        if 'error' in result:
            print(f"\n❌ Error: {result['error']}")
            return None

        try:
            enriched = self.extract_json(result['content'])

            print(f"\n✅ ENRICHMENT COMPLETE:")
            print(f"   Confidence: {enriched.get('_enrichment_meta', {}).get('confidence', 'unknown')}")
            print(f"   Fields added: {enriched.get('_enrichment_meta', {}).get('fields_added', [])}")
            print(f"   Fields corrected: {enriched.get('_enrichment_meta', {}).get('fields_corrected', [])}")

            print(f"\n   NEW poc.description:")
            desc = enriched.get('poc.description', 'N/A')
            print(f"   {desc[:200]}{'...' if len(desc) > 200 else ''}")

            print(f"\n   SECTORS (standardized):")
            sectors = enriched.get('fund.sectors', [])
            print(f"   {sectors}")

            print(f"\n   URLS:")
            print(f"   LinkedIn: {enriched.get('fund.linkedin', 'null')}")
            print(f"   Crunchbase: {enriched.get('fund.crunchbase', 'null')}")
            print(f"   Website: {enriched.get('fund.website', 'null')}")

            print(f"\n   Tokens: {result['tokens']}")
            print(f"   Notes: {enriched.get('_enrichment_meta', {}).get('notes', '')[:100]}...")

            return {
                'original': record,
                'enriched': enriched,
                'tokens': result['tokens']
            }

        except Exception as e:
            print(f"\n❌ Failed to parse: {e}")
            print(f"   Content preview: {result['content'][:300]}...")
            return None

def main():
    # Check API key
    if not os.environ.get('GEMINI_API_KEY'):
        print("❌ GEMINI_API_KEY not set")
        return

    # Load data
    print("Loading data.csv...")
    records = []
    with open('data.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        records = list(reader)

    print(f"Loaded {len(records)} records\n")

    # Select diverse test samples
    print("Selecting 5 diverse test samples...")

    test_samples = []

    # Sample 1: Missing most fields
    for rec in records:
        if not rec.get('fund.linkedin') and not rec.get('fund.crunchbase'):
            test_samples.append(rec)
            break

    # Sample 2: Has some but not all
    for rec in records:
        if rec.get('fund.linkedin') and not rec.get('fund.crunchbase'):
            test_samples.append(rec)
            break

    # Sample 3: Has most fields
    for rec in records:
        if rec.get('fund.linkedin') and rec.get('fund.website'):
            test_samples.append(rec)
            break

    # Sample 4 & 5: Different countries
    for rec in records:
        if rec.get('fund.country', '').lower() not in ['united states', 'usa']:
            test_samples.append(rec)
            if len(test_samples) >= 5:
                break

    print(f"Selected {len(test_samples)} samples\n")

    enricher = ComprehensiveEnricher()

    results = []
    total_tokens = 0

    for i, sample in enumerate(test_samples, 1):
        print(f"\n{'#'*80}")
        print(f"# TEST SAMPLE {i}/{len(test_samples)}")
        print(f"{'#'*80}")

        result = enricher.enrich_record(sample)

        if result:
            results.append(result)
            total_tokens += result['tokens']

        # Rate limiting
        if i < len(test_samples):
            print(f"\nWaiting 3 seconds before next request...")
            time.sleep(3)

    # Summary
    print(f"\n\n{'='*80}")
    print("COMPREHENSIVE TEST SUMMARY")
    print(f"{'='*80}")

    print(f"\nSuccessful enrichments: {len(results)}/{len(test_samples)}")
    print(f"Total tokens used: {total_tokens:,}")
    print(f"Average tokens per record: {total_tokens / len(results) if results else 0:.0f}")

    # Analyze results
    high_conf = sum(1 for r in results if r['enriched'].get('_enrichment_meta', {}).get('confidence') == 'high')
    print(f"High confidence: {high_conf}/{len(results)}")

    descriptions_added = sum(1 for r in results if r['enriched'].get('poc.description'))
    print(f"Descriptions added: {descriptions_added}/{len(results)}")

    sectors_structured = sum(1 for r in results if isinstance(r['enriched'].get('fund.sectors'), list))
    print(f"Sectors structured: {sectors_structured}/{len(results)}")

    # Estimate for full dataset
    if results:
        avg_tokens = total_tokens / len(results)
        print(f"\n📊 ESTIMATES FOR FULL ENRICHMENT:")
        print(f"   For 544 records: ~{544 * avg_tokens:,.0f} tokens")
        print(f"   For 373 incomplete: ~{373 * avg_tokens:,.0f} tokens")

    # Quality assessment
    print(f"\n💡 QUALITY ASSESSMENT:")
    if descriptions_added == len(results) and high_conf >= len(results) * 0.8:
        print("   ✅ EXCELLENT - Descriptions are good, confidence is high")
        print("   ✅ Safe to proceed with full enrichment")
    elif descriptions_added >= len(results) * 0.6:
        print("   ⚠️  GOOD - Most descriptions generated successfully")
        print("   ✅ Proceed with caution, review sample outputs")
    else:
        print("   ❌ NEEDS IMPROVEMENT - Many descriptions missing")
        print("   ⚠️  Consider adjusting prompt before full run")

    # Save sample results
    if results:
        output_file = 'test_enrichment_samples.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        print(f"\n📁 Sample results saved to: {output_file}")

    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    main()

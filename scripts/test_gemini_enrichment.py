#!/usr/bin/env python3
"""
Test Gemini API enrichment with a few samples
Uses Google Search grounding to find missing LinkedIn, Crunchbase, Website
"""

import json
import csv
import os
import urllib.request
import urllib.parse

class GeminiEnricher:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get('GEMINI_API_KEY')
        if not self.api_key:
            raise Exception("GEMINI_API_KEY environment variable required")

        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.model = "gemini-3-pro-preview"  # Latest model with tons of credits

    def build_enrichment_prompt(self, company_name, company_type, country, existing_linkedin=None, existing_crunchbase=None, existing_website=None):
        """Build prompt to find missing URLs"""

        prompt = f"""You are a research assistant. Find the official URLs for this company using Google Search.

Company Information:
- Name: {company_name}
- Type: {company_type}
- Country: {country}

Current Data:
- LinkedIn: {existing_linkedin or 'MISSING'}
- Crunchbase: {existing_crunchbase or 'MISSING'}
- Website: {existing_website or 'MISSING'}

Task: Find ONLY the missing URLs. Use Google Search to find the official, verified URLs.

Rules:
1. Only return URLs you find with high confidence from search results
2. LinkedIn URL must be company page (linkedin.com/company/...)
3. Crunchbase URL must be organization page (crunchbase.com/organization/...)
4. Website must be the official company website
5. If you cannot find a URL with confidence, return null for that field

Return ONLY valid JSON in this exact format:
{{
  "fund.linkedin": "https://www.linkedin.com/company/example/" or null,
  "fund.crunchbase": "https://www.crunchbase.com/organization/example" or null,
  "fund.website": "https://example.com" or null,
  "confidence": "high|medium|low",
  "notes": "brief note about findings"
}}

Do not return any text outside the JSON."""

        return prompt

    def call_gemini(self, prompt):
        """Call Gemini API with grounding"""

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

        request_body = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,  # Low for consistent results
                "maxOutputTokens": 2000
            },
            "tools": [
                {
                    "googleSearch": {}  # Enable grounding
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

    def enrich_record(self, record):
        """Enrich a single record"""

        company_name = record.get('fund.title', '')
        company_type = record.get('fund.type', '')
        country = record.get('fund.country', '')

        existing_linkedin = record.get('fund.linkedin', '')
        existing_crunchbase = record.get('fund.crunchbase', '')
        existing_website = record.get('fund.website', '')

        # Build prompt
        prompt = self.build_enrichment_prompt(
            company_name, company_type, country,
            existing_linkedin, existing_crunchbase, existing_website
        )

        print(f"\n{'='*70}")
        print(f"Enriching: {company_name}")
        print(f"Type: {company_type} | Country: {country}")
        print(f"Current LinkedIn: {existing_linkedin or '(empty)'}")
        print(f"Current Crunchbase: {existing_crunchbase or '(empty)'}")
        print(f"Current Website: {existing_website or '(empty)'}")
        print(f"{'='*70}")

        # Call API
        result = self.call_gemini(prompt)

        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            return None

        try:
            # Try to extract JSON from the content
            content = result['content']

            # Remove markdown code blocks if present
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()

            # Try to find JSON object
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                content = json_match.group(0)

            enrichment = json.loads(content)
            print(f"\n✅ Enrichment found:")
            print(f"   LinkedIn: {enrichment.get('fund.linkedin', 'null')}")
            print(f"   Crunchbase: {enrichment.get('fund.crunchbase', 'null')}")
            print(f"   Website: {enrichment.get('fund.website', 'null')}")
            print(f"   Confidence: {enrichment.get('confidence', 'unknown')}")
            print(f"   Notes: {enrichment.get('notes', '')}")
            print(f"   Tokens used: {result['tokens']}")

            return enrichment

        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {e}")
            print(f"   Raw content: {result['content'][:200]}...")
            return None

def main():
    # Check for API key
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("❌ Error: GEMINI_API_KEY environment variable not set")
        print("\nTo set it:")
        print("  export GEMINI_API_KEY='your-api-key-here'")
        print("\nOr add to your shell profile (~/.zshrc or ~/.bashrc):")
        print("  echo 'export GEMINI_API_KEY=\"your-api-key-here\"' >> ~/.zshrc")
        return

    # Load data
    print("Loading data.csv...")
    records = []
    with open('data.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        records = list(reader)

    print(f"Loaded {len(records)} records")

    # Find records with missing data for testing
    test_candidates = []
    for rec in records:
        missing_count = 0
        if not rec.get('fund.linkedin', '').strip():
            missing_count += 1
        if not rec.get('fund.crunchbase', '').strip():
            missing_count += 1
        if not rec.get('fund.website', '').strip():
            missing_count += 1

        if missing_count > 0:
            test_candidates.append((missing_count, rec))

    # Sort by most missing
    test_candidates.sort(key=lambda x: x[0], reverse=True)

    print(f"\nFound {len(test_candidates)} records with missing data")
    print(f"\nTesting on 3 sample records with different levels of missing data...")

    # Test on 3 samples
    samples = [
        test_candidates[0][1],  # Most missing
        test_candidates[len(test_candidates)//2][1] if len(test_candidates) > 1 else test_candidates[0][1],  # Middle
        test_candidates[-1][1] if len(test_candidates) > 2 else test_candidates[0][1]  # Least missing
    ]

    enricher = GeminiEnricher(api_key)

    results = []
    for i, sample in enumerate(samples, 1):
        print(f"\n\n{'#'*70}")
        print(f"# TEST SAMPLE {i}/3")
        print(f"{'#'*70}")

        enrichment = enricher.enrich_record(sample)

        if enrichment:
            results.append({
                'original': sample,
                'enrichment': enrichment
            })

        # Small delay between requests
        if i < len(samples):
            print("\nWaiting 2 seconds before next request...")
            import time
            time.sleep(2)

    # Summary
    print(f"\n\n{'='*70}")
    print("SUMMARY OF TEST RESULTS")
    print(f"{'='*70}")
    print(f"\nSuccessful enrichments: {len(results)}/3")

    if len(results) > 0:
        total_tokens = sum(r.get('enrichment', {}).get('tokens', 0) for r in results)
        print(f"Total tokens used: {total_tokens}")
        print(f"Average tokens per record: {total_tokens / len(results):.0f}")

        high_confidence = sum(1 for r in results if r.get('enrichment', {}).get('confidence') == 'high')
        print(f"High confidence results: {high_confidence}/{len(results)}")

        # Estimate for full dataset
        records_with_missing = len(test_candidates)
        estimated_tokens = records_with_missing * (total_tokens / len(results))
        print(f"\nEstimated tokens for all {records_with_missing} records: {estimated_tokens:,.0f}")

        print("\n💡 Recommendation:")
        if high_confidence == len(results):
            print("   ✅ Results look good! Gemini is finding accurate data.")
            print("   ✅ Safe to proceed with full enrichment.")
        elif high_confidence >= len(results) / 2:
            print("   ⚠️  Mixed confidence. Review results carefully.")
            print("   ⚠️  Consider manual verification for low-confidence results.")
        else:
            print("   ❌ Low confidence overall. May need to adjust prompt.")
            print("   ❌ Review and iterate before full enrichment.")

    print("\n" + "="*70)

if __name__ == '__main__':
    main()

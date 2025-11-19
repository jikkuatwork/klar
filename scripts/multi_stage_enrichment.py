#!/usr/bin/env python3
"""
Multi-Stage Enrichment System for Learning Gemini3 Grounding Behavior

This system separates enrichment into configurable stages:
- Stage 1: POC (contact person) enrichment
- Stage 2: Fund (company) enrichment
- Stage 3: Fund deep research (optional)

Goal: Understand Gemini3 grounding depth, search behavior, and optimal query patterns.
"""

import json
import csv
import os
import urllib.request
import time
from typing import Dict, List, Optional, Any

class MultiStageEnricher:
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

    def build_poc_enrichment_prompt(self, record: Dict) -> str:
        """Build POC (contact person) focused enrichment prompt"""

        company_name = record.get('fund.title', '')
        company_type = record.get('fund.type', '')
        first_name = record.get('poc.first_name', '')
        last_name = record.get('poc.last_name', '')
        existing_role = record.get('poc.role', '')
        existing_linkedin = record.get('poc.linkedin', '')

        prompt = f"""You are a professional contact research specialist. Focus ONLY on the PERSON, not the company.

PERSON TO RESEARCH:
- Name: {first_name} {last_name}
- Current role: {existing_role or 'Unknown'}
- Company: {company_name} ({company_type})
- Current LinkedIn: {existing_linkedin or 'MISSING'}

YOUR TASK: Research this PERSON using Google Search and provide:

1. **poc.linkedin** - Personal LinkedIn profile URL (linkedin.com/in/...)
   - Must be the person's profile, NOT the company page
   - Only if you find it with high confidence

2. **poc.role** - Their exact role/title at {company_name}
   - Current position only
   - Verify accuracy

3. **poc.description** - Professional bio (2-3 sentences)
   - Their role and key responsibilities
   - Years of experience (if findable)
   - Previous companies/roles (if notable)
   - Education or specializations (if relevant)
   - Write in third person, professional tone

4. **poc.phone** - Direct phone number (if publicly available)

RULES:
- Focus search on the PERSON, not the company
- Only add data with HIGH confidence
- Use null for fields you cannot verify
- For description: Be specific, factual, professional
- Verify the person works at {company_name}

RETURN FORMAT (JSON only):
{{
  "poc.linkedin": "string or null",
  "poc.role": "string or null",
  "poc.description": "string or null",
  "poc.phone": "string or null",
  "_stage_meta": {{
    "confidence": "high|medium|low",
    "fields_found": ["list of fields found"],
    "search_quality": "excellent|good|limited|poor",
    "notes": "brief explanation"
  }}
}}

Return ONLY valid JSON, no additional text."""

        return prompt

    def build_fund_enrichment_prompt(self, record: Dict) -> str:
        """Build Fund (company) focused enrichment prompt"""

        company_name = record.get('fund.title', '')
        company_type = record.get('fund.type', '')
        country = record.get('fund.country', '')
        city = record.get('fund.city', '')
        existing_linkedin = record.get('fund.linkedin', '')
        existing_crunchbase = record.get('fund.crunchbase', '')
        existing_website = record.get('fund.website', '')
        existing_sectors = record.get('fund.sectors', '')

        prompt = f"""You are a professional company research specialist. Focus ONLY on the COMPANY, not individuals.

COMPANY TO RESEARCH:
- Name: {company_name}
- Type: {company_type}
- Location: {city}, {country}
- Current LinkedIn: {existing_linkedin or 'MISSING'}
- Current Crunchbase: {existing_crunchbase or 'MISSING'}
- Current Website: {existing_website or 'MISSING'}
- Current Sectors: {existing_sectors or 'MISSING'}

YOUR TASK: Research this COMPANY using Google Search and provide:

1. **fund.linkedin** - Company LinkedIn page (linkedin.com/company/...)
   - Must be company page, NOT personal profiles
   - Official page only

2. **fund.crunchbase** - Crunchbase organization page (crunchbase.com/organization/...)
   - Official profile only

3. **fund.website** - Official company website
   - Primary domain only
   - Must NOT be LinkedIn or Crunchbase

4. **fund.sectors** - Investment focus areas as array
   Use ONLY these standardized values:
   {', '.join(self.standard_sectors[:20])}... (and similar)

   - Map existing sectors to standard values
   - Add sectors found through research
   - Return as array: ["sector-1", "sector-2", ...]

5. **fund.preferred_stage** - Investment stage focus
   - Examples: "Seed", "Series A", "Growth", "Late Stage", "All Stages"
   - Only if clearly stated

6. **fund.city** - Headquarters city (if missing: {city or 'MISSING'})

RULES:
- Focus search on the COMPANY and its investment activities
- Only URLs in correct format (https://, no trailing slashes)
- Sectors must use standardized values only
- Use null for fields you cannot verify
- Verify all URLs are official and correct

RETURN FORMAT (JSON only):
{{
  "fund.linkedin": "string or null",
  "fund.crunchbase": "string or null",
  "fund.website": "string or null",
  "fund.city": "string or null",
  "fund.sectors": ["array of standardized sectors"],
  "fund.preferred_stage": "string or null",
  "_stage_meta": {{
    "confidence": "high|medium|low",
    "fields_found": ["list of fields found"],
    "fields_corrected": ["list of corrected fields"],
    "search_quality": "excellent|good|limited|poor",
    "notes": "brief explanation"
  }}
}}

Return ONLY valid JSON, no additional text."""

        return prompt

    def build_fund_deep_research_prompt(self, record: Dict) -> str:
        """Build deep research prompt for strategic company insights"""

        company_name = record.get('fund.title', '')
        company_type = record.get('fund.type', '')
        website = record.get('fund.website', '')
        sectors = record.get('fund.sectors', '')

        prompt = f"""You are a professional investment research analyst. Provide DEEP STRATEGIC insights about this firm.

COMPANY TO RESEARCH:
- Name: {company_name}
- Type: {company_type}
- Website: {website or 'Unknown'}
- Sectors: {sectors or 'Unknown'}

YOUR TASK: Research this investment firm's strategy and portfolio using Google Search:

1. **fund.description** - Company overview (3-4 sentences)
   - What they do and their market position
   - AUM or fund size (if public)
   - Year founded and key milestones
   - Notable achievements or recognition

2. **fund.thesis** - Investment thesis/strategy (2-3 sentences)
   - Investment philosophy and approach
   - What they look for in investments
   - Geographic or sector focus
   - Stage preference and ticket size

3. **fund.portfolio_companies** - Recent notable investments (array of objects)
   Find 3-5 recent portfolio companies:
   [
     {{
       "name": "Company Name",
       "website": "https://...",
       "sector": "sector",
       "description": "1 sentence about the company"
     }}
   ]

4. **fund.aum** - Assets under management (if public)
   - Include currency and year
   - Example: "$500M (2024)"

5. **fund.geographies** - Geographic investment focus (array)
   - Countries or regions they invest in
   - Example: ["North America", "Europe", "Asia-Pacific"]

RULES:
- Only include information you can verify through search
- Use null for fields you cannot find with confidence
- Be specific and factual, no speculation
- Portfolio companies must be real and verified
- Focus on recent, relevant information

RETURN FORMAT (JSON only):
{{
  "fund.description": "string or null",
  "fund.thesis": "string or null",
  "fund.portfolio_companies": [
    {{
      "name": "string",
      "website": "string or null",
      "sector": "string or null",
      "description": "string"
    }}
  ],
  "fund.aum": "string or null",
  "fund.geographies": ["array of regions"],
  "_stage_meta": {{
    "confidence": "high|medium|low",
    "fields_found": ["list of fields found"],
    "search_quality": "excellent|good|limited|poor",
    "notes": "brief explanation"
  }}
}}

Return ONLY valid JSON, no additional text."""

        return prompt

    def call_gemini(self, prompt: str, grounding_config: Optional[Dict] = None) -> Dict:
        """Call Gemini API with configurable grounding"""

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

        # Simple grounding config (API doesn't support advanced options)
        if grounding_config is None:
            grounding_config = {}

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
                    "googleSearch": grounding_config
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
                        'tokens': metadata.get('totalTokenCount', 0),
                        'success': True
                    }
                else:
                    return {'error': 'No candidates returned', 'success': False}

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            return {'error': f'HTTP {e.code}: {error_body}', 'success': False}
        except Exception as e:
            return {'error': str(e), 'success': False}

    def extract_json(self, content: str) -> Dict:
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

    def enrich_record_multistage(
        self,
        record: Dict,
        stages: List[str] = ["poc", "fund"],
        grounding_configs: Optional[Dict[str, Dict]] = None,
        delay_between_stages: int = 2
    ) -> Dict:
        """
        Enrich a record using multiple stages

        Args:
            record: The record to enrich
            stages: Which stages to run (e.g., ["poc", "fund", "deep"])
            grounding_configs: Optional per-stage grounding configurations
            delay_between_stages: Seconds to wait between stages

        Returns:
            Dict with enriched data and metadata from all stages
        """

        company_name = record.get('fund.title', 'Unknown')

        print(f"\n{'='*80}")
        print(f"MULTI-STAGE ENRICHMENT: {company_name}")
        print(f"Type: {record.get('fund.type', 'N/A')} | Country: {record.get('fund.country', 'N/A')}")
        print(f"Contact: {record.get('poc.first_name', '')} {record.get('poc.last_name', '')}")
        print(f"Stages: {', '.join(stages)}")
        print(f"{'='*80}")

        enriched_data = {}
        stage_results = {}
        total_tokens = 0

        grounding_configs = grounding_configs or {}

        # Stage 1: POC Enrichment
        if "poc" in stages:
            print(f"\n🔍 STAGE 1: POC (Contact Person) Enrichment")
            print(f"   Focus: poc.linkedin, poc.role, poc.description, poc.phone")

            prompt = self.build_poc_enrichment_prompt(record)
            result = self.call_gemini(prompt, grounding_configs.get("poc"))

            if result['success']:
                try:
                    poc_data = self.extract_json(result['content'])
                    stage_results['poc'] = poc_data
                    total_tokens += result['tokens']

                    # Merge into enriched_data
                    for key in ['poc.linkedin', 'poc.role', 'poc.description', 'poc.phone']:
                        if key in poc_data and poc_data[key]:
                            enriched_data[key] = poc_data[key]

                    meta = poc_data.get('_stage_meta', {})
                    print(f"   ✅ Confidence: {meta.get('confidence', 'unknown')}")
                    print(f"   ✅ Search Quality: {meta.get('search_quality', 'unknown')}")
                    print(f"   ✅ Fields Found: {meta.get('fields_found', [])}")
                    print(f"   ✅ Tokens: {result['tokens']}")

                    if enriched_data.get('poc.description'):
                        desc = enriched_data['poc.description']
                        print(f"   📝 Description: {desc[:120]}{'...' if len(desc) > 120 else ''}")

                except Exception as e:
                    print(f"   ❌ Failed to parse POC stage: {e}")
                    stage_results['poc'] = {'error': str(e)}
            else:
                print(f"   ❌ POC stage failed: {result.get('error', 'Unknown error')}")
                stage_results['poc'] = {'error': result.get('error')}

            if "fund" in stages:
                print(f"\n   ⏳ Waiting {delay_between_stages}s before next stage...")
                time.sleep(delay_between_stages)

        # Stage 2: Fund Enrichment
        if "fund" in stages:
            print(f"\n🏢 STAGE 2: Fund (Company) Enrichment")
            print(f"   Focus: fund.linkedin, fund.crunchbase, fund.website, fund.sectors")

            prompt = self.build_fund_enrichment_prompt(record)
            result = self.call_gemini(prompt, grounding_configs.get("fund"))

            if result['success']:
                try:
                    fund_data = self.extract_json(result['content'])
                    stage_results['fund'] = fund_data
                    total_tokens += result['tokens']

                    # Merge into enriched_data
                    for key in ['fund.linkedin', 'fund.crunchbase', 'fund.website',
                               'fund.city', 'fund.sectors', 'fund.preferred_stage']:
                        if key in fund_data and fund_data[key]:
                            enriched_data[key] = fund_data[key]

                    meta = fund_data.get('_stage_meta', {})
                    print(f"   ✅ Confidence: {meta.get('confidence', 'unknown')}")
                    print(f"   ✅ Search Quality: {meta.get('search_quality', 'unknown')}")
                    print(f"   ✅ Fields Found: {meta.get('fields_found', [])}")
                    print(f"   ✅ Fields Corrected: {meta.get('fields_corrected', [])}")
                    print(f"   ✅ Tokens: {result['tokens']}")

                    if enriched_data.get('fund.sectors'):
                        print(f"   📊 Sectors: {enriched_data['fund.sectors']}")

                except Exception as e:
                    print(f"   ❌ Failed to parse Fund stage: {e}")
                    stage_results['fund'] = {'error': str(e)}
            else:
                print(f"   ❌ Fund stage failed: {result.get('error', 'Unknown error')}")
                stage_results['fund'] = {'error': result.get('error')}

            if "deep" in stages:
                print(f"\n   ⏳ Waiting {delay_between_stages}s before next stage...")
                time.sleep(delay_between_stages)

        # Stage 3: Deep Research (optional)
        if "deep" in stages:
            print(f"\n🔬 STAGE 3: Fund Deep Research")
            print(f"   Focus: fund.description, fund.thesis, fund.portfolio_companies")

            prompt = self.build_fund_deep_research_prompt(record)
            result = self.call_gemini(prompt, grounding_configs.get("deep"))

            if result['success']:
                try:
                    deep_data = self.extract_json(result['content'])
                    stage_results['deep'] = deep_data
                    total_tokens += result['tokens']

                    # Merge into enriched_data
                    for key in ['fund.description', 'fund.thesis', 'fund.portfolio_companies',
                               'fund.aum', 'fund.geographies']:
                        if key in deep_data and deep_data[key]:
                            enriched_data[key] = deep_data[key]

                    meta = deep_data.get('_stage_meta', {})
                    print(f"   ✅ Confidence: {meta.get('confidence', 'unknown')}")
                    print(f"   ✅ Search Quality: {meta.get('search_quality', 'unknown')}")
                    print(f"   ✅ Fields Found: {meta.get('fields_found', [])}")
                    print(f"   ✅ Tokens: {result['tokens']}")

                    if enriched_data.get('fund.description'):
                        desc = enriched_data['fund.description']
                        print(f"   📄 Description: {desc[:120]}{'...' if len(desc) > 120 else ''}")

                    if enriched_data.get('fund.portfolio_companies'):
                        count = len(enriched_data['fund.portfolio_companies'])
                        print(f"   💼 Portfolio Companies: {count} found")

                except Exception as e:
                    print(f"   ❌ Failed to parse Deep stage: {e}")
                    stage_results['deep'] = {'error': str(e)}
            else:
                print(f"   ❌ Deep stage failed: {result.get('error', 'Unknown error')}")
                stage_results['deep'] = {'error': result.get('error')}

        # Summary
        print(f"\n{'='*80}")
        print(f"ENRICHMENT COMPLETE")
        print(f"Total Tokens: {total_tokens}")
        print(f"Stages Completed: {len([s for s in stage_results if 'error' not in stage_results[s]])}/{len(stages)}")
        print(f"Fields Enriched: {len(enriched_data)}")
        print(f"{'='*80}")

        return {
            'original': record,
            'enriched': enriched_data,
            'stage_results': stage_results,
            'total_tokens': total_tokens,
            'stages_run': stages
        }


def main():
    """Test multi-stage enrichment on sample records"""

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

    # Test configurations
    test_configs = [
        {
            "name": "2-Stage (POC + Fund)",
            "stages": ["poc", "fund"],
            "description": "Separate person and company queries"
        },
        {
            "name": "1-Stage (Fund only)",
            "stages": ["fund"],
            "description": "Company info only, skip person details"
        },
        {
            "name": "3-Stage (POC + Fund + Deep)",
            "stages": ["poc", "fund", "deep"],
            "description": "Full enrichment with strategic insights"
        }
    ]

    # Select diverse test samples
    print("Selecting 3 test samples...")
    test_samples = []

    # Sample with missing data
    for rec in records:
        if not rec.get('fund.linkedin') and not rec.get('poc.description'):
            test_samples.append(rec)
            break

    # Sample with some data
    for rec in records:
        if rec.get('fund.website') and not rec.get('poc.description'):
            test_samples.append(rec)
            if len(test_samples) >= 2:
                break

    # Sample with good data
    for rec in records:
        if rec.get('fund.linkedin') and rec.get('fund.website'):
            test_samples.append(rec)
            if len(test_samples) >= 3:
                break

    print(f"Selected {len(test_samples)} samples\n")

    enricher = MultiStageEnricher()

    # Test each configuration
    all_results = {}

    for config_idx, config in enumerate(test_configs[:1], 1):  # Test first config only
        print(f"\n{'#'*80}")
        print(f"# TESTING CONFIGURATION {config_idx}/{len(test_configs[:1])}")
        print(f"# {config['name']}")
        print(f"# {config['description']}")
        print(f"{'#'*80}")

        config_results = []

        for sample_idx, sample in enumerate(test_samples[:2], 1):  # Test 2 samples
            print(f"\n{'~'*80}")
            print(f"~ Sample {sample_idx}/{len(test_samples[:2])}")
            print(f"{'~'*80}")

            result = enricher.enrich_record_multistage(
                sample,
                stages=config['stages'],
                delay_between_stages=3
            )

            config_results.append(result)

            # Delay between samples
            if sample_idx < len(test_samples[:2]):
                print(f"\n⏳ Waiting 3 seconds before next sample...")
                time.sleep(3)

        all_results[config['name']] = config_results

    # Summary report
    print(f"\n\n{'='*80}")
    print("MULTI-STAGE ENRICHMENT TEST SUMMARY")
    print(f"{'='*80}")

    for config_name, results in all_results.items():
        print(f"\n📊 Configuration: {config_name}")
        print(f"   Samples tested: {len(results)}")

        total_tokens = sum(r['total_tokens'] for r in results)
        avg_tokens = total_tokens / len(results) if results else 0

        print(f"   Total tokens: {total_tokens:,}")
        print(f"   Average tokens/record: {avg_tokens:.0f}")

        # Count successful stages
        successful_stages = 0
        total_stages = 0
        for r in results:
            for stage_name, stage_data in r['stage_results'].items():
                total_stages += 1
                if 'error' not in stage_data:
                    successful_stages += 1

        print(f"   Successful stages: {successful_stages}/{total_stages}")

        # Count fields enriched
        total_fields = sum(len(r['enriched']) for r in results)
        avg_fields = total_fields / len(results) if results else 0
        print(f"   Average fields enriched: {avg_fields:.1f}")

    # Save results
    output_file = 'multi_stage_test_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2)

    print(f"\n📁 Results saved to: {output_file}")
    print(f"\n{'='*80}\n")


if __name__ == '__main__':
    main()

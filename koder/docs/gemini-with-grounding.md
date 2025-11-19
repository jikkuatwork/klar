# Gemini with Google Search Grounding

A comprehensive guide to using Google's Gemini API with Google Search grounding capabilities for research and data extraction tasks.

## Overview

This implementation demonstrates how to use Gemini 2.5 Pro with Google Search grounding to:
- Research startups and companies with up-to-date information
- Extract structured data from research results
- Handle batch processing with parallel requests
- Implement error handling and retry mechanisms

## Environment Setup

### Prerequisites

1. **Node.js** (v18 or higher)
2. **TypeScript** (v4.5+)
3. **npm** or **yarn** package manager
4. **Google Gemini API Key**

### Environment Variables

Create a `.env` file in your project root:

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional (for different models)
GEMINI_MODEL=gemini-2.5-pro

# Optional (for rate limiting)
DEFAULT_DELAY_MS=2000
MAX_PARALLEL_REQUESTS=3
```

### Getting API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and add it to your environment variables

## Dependencies

Install the required packages:

```bash
npm install
# or
yarn install
```

**Required dependencies:**
```json
{
  "dependencies": {
    "node-fetch": "^3.3.0",
    "typescript": "^4.9.0"
  },
  "devDependencies": {
    "@types/node": "^18.0.0",
    "ts-node": "^10.9.0"
  }
}
```

## Project Structure

```
your-project/
├── src/
│   ├── gemini-client.ts          # Core Gemini client implementation
│   ├── research-service.ts      # Research service with grounding
│   ├── data-extractor.ts        # Structured data extraction
│   └── types/                   # TypeScript interfaces
│       ├── gemini.ts
│       └── startup.ts
├── prompts/
│   ├── research.md              # Research prompt template
│   └── extraction.md            # Data extraction template
├── data/
│   ├── input.json               # Input data (startups, companies, etc.)
│   └── output/                  # Research results
├── logs/                        # Error and activity logs
├── .env
├── package.json
└── tsconfig.json
```

## Core Implementation

### 1. Gemini Client with Grounding

```typescript
// src/types/gemini.ts
export interface GeminiMessage {
  role: "user" | "model"
  parts: Array<{
    text: string
  }>
}

export interface GeminiRequest {
  contents: GeminiMessage[]
  generationConfig?: {
    thinkingConfig?: {
      thinkingBudget: number
    }
    maxOutputTokens?: number
    temperature?: number
    responseMimeType?: string
  }
  tools?: Array<{
    googleSearch?: {}
  }>
}

export interface GeminiResponse {
  candidates: Array<{
    content: {
      parts: Array<{
        text: string
      }>
      role: string
    }
    finishReason: string
    index: number
  }>
  usageMetadata: {
    promptTokenCount: number
    candidatesTokenCount: number
    totalTokenCount: number
  }
}
```

```typescript
// src/gemini-client.ts
import { GeminiRequest, GeminiResponse } from './types/gemini'

export class GeminiClient {
  private apiKey: string
  private baseUrl: string = "https://generativelanguage.googleapis.com/v1beta"
  private model: string

  constructor(apiKey?: string, model?: string) {
    this.apiKey = apiKey || process.env.GEMINI_API_KEY!
    this.model = model || process.env.GEMINI_MODEL || "gemini-2.5-pro"

    if (!this.apiKey) {
      throw new Error("GEMINI_API_KEY environment variable is required")
    }
  }

  async generateContent(request: GeminiRequest): Promise<GeminiResponse> {
    const url = `${this.baseUrl}/models/${this.model}:generateContent?key=${this.apiKey}`

    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(
        `Gemini API request failed: ${response.status} ${response.statusText} - ${errorText}`
      )
    }

    return await response.json()
  }

  // Stream version for long responses
  async *generateContentStream(request: GeminiRequest): AsyncGenerator<string> {
    const url = `${this.baseUrl}/models/${this.model}:streamGenerateContent?key=${this.apiKey}`

    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(
        `Gemini API stream request failed: ${response.status} ${response.statusText} - ${errorText}`
      )
    }

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()

    if (!reader) {
      throw new Error("Response body is not readable")
    }

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n').filter(line => line.trim())

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') return

            try {
              const parsed = JSON.parse(data)
              const text = parsed.candidates?.[0]?.content?.parts?.[0]?.text
              if (text) yield text
            } catch (e) {
              // Skip invalid JSON
            }
          }
        }
      }
    } finally {
      reader.releaseLock()
    }
  }
}
```

### 2. Research Service with Grounding

```typescript
// src/research-service.ts
import { GeminiClient } from './gemini-client'
import { GeminiRequest } from './types/gemini'
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs'
import { join } from 'path'

export interface ResearchInput {
  name: string
  website: string
  description: string
  sector: string
  location: string
  year: string
}

export class ResearchService {
  private client: GeminiClient
  private promptTemplate: string

  constructor(
    private promptTemplatePath: string = "./prompts/research.md",
    client?: GeminiClient
  ) {
    this.client = client || new GeminiClient()
    this.promptTemplate = this.loadPromptTemplate()
  }

  private loadPromptTemplate(): string {
    try {
      return readFileSync(this.promptTemplatePath, "utf-8")
    } catch (error) {
      throw new Error(`Failed to load prompt template from ${this.promptTemplatePath}`)
    }
  }

  private buildResearchPrompt(input: ResearchInput): string {
    return this.promptTemplate
      .replace("{COMPANY_NAME}", input.name)
      .replace("{COMPANY_WEBSITE}", input.website)
      .replace("{COMPANY_SECTOR}", input.sector)
      .replace("{COMPANY_LOCATION}", input.location)
      .replace("{COMPANY_YEAR}", input.year)
      .replace("{COMPANY_DESCRIPTION}", input.description)
  }

  async researchEntity(input: ResearchInput): Promise<{ content: string; metadata: any }> {
    const prompt = this.buildResearchPrompt(input)

    const request: GeminiRequest = {
      contents: [
        {
          role: "user",
          parts: [{ text: prompt }],
        },
      ],
      generationConfig: {
        thinkingConfig: {
          thinkingBudget: -1, // Enable thinking/reasoning
        },
        maxOutputTokens: 8000,
        temperature: 0.3,
      },
      tools: [
        {
          googleSearch: {}, // This enables grounding
        },
      ],
    }

    const response = await this.client.generateContent(request)

    if (!response.candidates || response.candidates.length === 0) {
      throw new Error("No candidates returned from Gemini API")
    }

    const content = response.candidates[0].content.parts[0].text

    return {
      content,
      metadata: {
        tokensUsed: response.usageMetadata.totalTokenCount,
        model: "gemini-2.5-pro",
        grounded: true,
      }
    }
  }

  saveResearch(input: ResearchInput, content: string, outputDir: string = "./data/output"): void {
    if (!existsSync(outputDir)) {
      mkdirSync(outputDir, { recursive: true })
    }

    // Create filename from company name
    const filename = input.name.toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '') + '.md'

    const outputPath = join(outputDir, filename)
    writeFileSync(outputPath, content)
  }
}
```

### 3. Structured Data Extraction

```typescript
// src/data-extractor.ts
import { GeminiClient } from './gemini-client'
import { GeminiRequest } from './types/gemini'

export interface ExtractionSchema {
  country?: string | null
  business_models: string[]
  target_countries: string[]
  technologies: string[]
  industry?: string | null
}

export class DataExtractor {
  private client: GeminiClient
  private extractionPrompt: string

  constructor(client?: GeminiClient) {
    this.client = client || new GeminiClient()
    this.extractionPrompt = this.buildExtractionPrompt()
  }

  private buildExtractionPrompt(): string {
    return `
Extract ONLY these fields from the text. Return valid JSON per schema.
Fill only if confident; otherwise null or empty arrays.

Rules:
- country, target_countries[*]: ISO-3166-1 alpha-2 (e.g., US, GB, IN).
- business_models, technologies, industry: lowercase kebab-case using canonical lists.
- Map obvious synonyms to canonical terms.
- Do not invent information.

Schema:
{
  "country": "string|null",
  "business_models": ["string"],
  "target_countries": ["string"],
  "technologies": ["string"],
  "industry": "string|null"
}

Canonical values:
business_models: [saas, api, platform, marketplace, hardware, robotics, services, daas, b2b, b2c, b2b2c, open-source, balance-sheet-lending]
technologies: [ai-ml, llm, nlp, cv, iot, robotics, edge, cloud, blockchain, geospatial, satellite, rfid, ar-vr, data-platform, automation]
industry: [fintech, logtech, maritime, enterprise-saas, healthtech, foodtech, agritech, mobility, climatetech, proptech, edtech, cybersecurity, martech, biotech, media, consumertech, govtech, insurtech, retailtech, energy]

Text to analyze:
{TEXT_TO_ANALYZE}

Return JSON only, no explanation.
`
  }

  async extractStructuredData(text: string): Promise<ExtractionSchema> {
    const prompt = this.extractionPrompt.replace("{TEXT_TO_ANALYZE}", text)

    const request: GeminiRequest = {
      contents: [
        {
          role: "user",
          parts: [{ text: prompt }]
        }
      ],
      generationConfig: {
        temperature: 0.1,
        responseMimeType: "application/json",
      },
      tools: [
        {
          googleSearch: {}, // Enable grounding for verification
        }
      ]
    }

    const response = await this.client.generateContent(request)

    if (!response.candidates || response.candidates.length === 0) {
      throw new Error("No candidates returned from Gemini API")
    }

    const content = response.candidates[0].content.parts[0].text

    try {
      return JSON.parse(content)
    } catch (error) {
      throw new Error(`Failed to parse JSON response: ${content}`)
    }
  }
}
```

### 4. Batch Processing with Error Handling

```typescript
// src/batch-processor.ts
import { ResearchService, ResearchInput } from './research-service'
import { DataExtractor } from './data-extractor'
import { writeFileSync, appendFileSync } from 'fs'

interface ProcessingError {
  timestamp: string
  input: {
    name: string
    website: string
  }
  error: string
}

export class BatchProcessor {
  private researchService: ResearchService
  private dataExtractor: DataExtractor
  private errorLog: ProcessingError[] = []

  constructor(
    researchService?: ResearchService,
    dataExtractor?: DataExtractor
  ) {
    this.researchService = researchService || new ResearchService()
    this.dataExtractor = dataExtractor || new DataExtractor()
  }

  async processBatch(
    inputs: ResearchInput[],
    options: {
      maxParallel?: number
      delayMs?: number
      outputDir?: string
      saveIntermediate?: boolean
    } = {}
  ): Promise<{ successful: number; failed: number }> {
    const {
      maxParallel = 3,
      delayMs = 2000,
      outputDir = "./data/output",
      saveIntermediate = true
    } = options

    let successful = 0
    let failed = 0

    // Process in parallel batches
    for (let i = 0; i < inputs.length; i += maxParallel) {
      const batch = inputs.slice(i, i + maxParallel)

      console.log(`Processing batch ${Math.floor(i/maxParallel) + 1}/${Math.ceil(inputs.length/maxParallel)}`)

      const promises = batch.map(async (input) => {
        try {
          // Research phase
          const researchResult = await this.researchService.researchEntity(input)

          if (saveIntermediate) {
            this.researchService.saveResearch(input, researchResult.content, outputDir)
          }

          // Extraction phase
          const structuredData = await this.dataExtractor.extractStructuredData(researchResult.content)

          // Save combined results
          const combinedResult = {
            input,
            research: researchResult.content,
            structuredData,
            metadata: researchResult.metadata
          }

          const filename = `${input.name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.json`
          require('fs').writeFileSync(
            require('path').join(outputDir, filename),
            JSON.stringify(combinedResult, null, 2)
          )

          successful++
          console.log(`✅ Completed: ${input.name}`)

        } catch (error) {
          failed++
          const errorEntry: ProcessingError = {
            timestamp: new Date().toISOString(),
            input: {
              name: input.name,
              website: input.website
            },
            error: error.message || String(error)
          }

          this.errorLog.push(errorEntry)
          console.error(`❌ Failed: ${input.name} - ${error.message}`)
        }
      })

      await Promise.all(promises)

      // Rate limiting between batches
      if (i + maxParallel < inputs.length) {
        console.log(`Waiting ${delayMs}ms before next batch...`)
        await new Promise(resolve => setTimeout(resolve, delayMs))
      }
    }

    // Save error log
    if (this.errorLog.length > 0) {
      const errorLogContent = this.errorLog
        .map(entry => JSON.stringify(entry))
        .join('\n')

      appendFileSync('./logs/processing-errors.log', errorLogContent + '\n')
    }

    return { successful, failed }
  }

  getErrorLog(): ProcessingError[] {
    return this.errorLog
  }
}
```

## Usage Examples

### Basic Research

```typescript
import { ResearchService } from './src/research-service'

const researcher = new ResearchService()

const startup = {
  name: "StoryBrain",
  website: "https://storybrain.com/",
  description: "AI-powered platform for e-commerce businesses",
  sector: "Technology",
  location: "Singapore",
  year: "2019"
}

const result = await researcher.researchEntity(startup)
console.log(result.content)
researcher.saveResearch(startup, result.content)
```

### Batch Processing

```typescript
import { BatchProcessor } from './src/batch-processor'
import { readFileSync } from 'fs'

// Load startups from JSON file
const startupsData = JSON.parse(readFileSync('./data/input.json', 'utf-8'))

const processor = new BatchProcessor()

const { successful, failed } = await processor.processBatch(startupsData, {
  maxParallel: 5,
  delayMs: 3000,
  outputDir: './data/results',
  saveIntermediate: true
})

console.log(`Processing complete: ${successful} successful, ${failed} failed`)
```

### Data Extraction Only

```typescript
import { DataExtractor } from './src/data-extractor'

const extractor = new DataExtractor()

const researchText = `
StoryBrain is a B2B software company that provides an AI-powered platform
for e-commerce businesses. Based in Singapore, the company uses generative
AI and machine learning to optimize product visualizations...
`

const structuredData = await extractor.extractStructuredData(researchText)
console.log(structuredData)
// Output: { country: "SG", business_models: ["b2b", "saas"], ... }
```

## Configuration Options

### Gemini Generation Config

```typescript
const generationConfig = {
  thinkingConfig: {
    thinkingBudget: -1,        // Enable reasoning (-1 = unlimited)
  },
  maxOutputTokens: 8000,       // Response length limit
  temperature: 0.3,            // Creativity (0.0 = deterministic, 1.0 = creative)
  responseMimeType: "text/plain", // or "application/json" for structured data
}
```

### Grounding Options

```typescript
// Enable Google Search grounding
const tools = [
  {
    googleSearch: {
      // Optional search constraints
      dynamicRetrievalConfig: {
        mode: "MODE_DYNAMIC",     // Enable dynamic grounding
        dynamicThreshold: 0.7,    // Confidence threshold for grounding
      }
    }
  }
]
```

### Rate Limiting

```typescript
const options = {
  maxParallel: 3,      // Concurrent requests
  delayMs: 2000,       // Delay between batches
  retryAttempts: 3,    // Number of retries on failure
  retryDelayMs: 1000,  // Delay between retries
}
```

## Error Handling

### Common Errors and Solutions

1. **API Key Issues**
   ```bash
   Error: GEMINI_API_KEY environment variable is required
   ```
   - Ensure your `.env` file exists with valid API key
   - Check that the API key has proper permissions

2. **Rate Limiting**
   ```bash
   Error: 429 Too Many Requests
   ```
   - Reduce `maxParallel` count
   - Increase `delayMs` between batches
   - Implement exponential backoff

3. **Content Filtering**
   ```bash
   Error: 400 Content was blocked
   ```
   - Review prompt content for policy violations
   - Use more neutral language in prompts

4. **Model Unavailable**
   ```bash
   Error: 404 Model not found
   ```
   - Verify model name (`gemini-2.5-pro`, `gemini-1.5-pro`, etc.)
   - Check model availability in your region

### Logging

Enable detailed logging:

```typescript
const researcher = new ResearchService()
researcher.setDebugMode(true) // Enable prompt/response logging
```

Monitor logs in `./logs/` directory:
- `processing-errors.log` - Failed processing attempts
- `debug.log` - Detailed request/response data (if debug mode enabled)

## Cost Optimization

### Token Usage Tracking

```typescript
const result = await researcher.researchEntity(startup)
console.log(`Tokens used: ${result.metadata.tokensUsed}`)

// Track costs across batch
let totalTokens = 0
results.forEach(result => {
  totalTokens += result.metadata.tokensUsed
})
console.log(`Total tokens: ${totalTokens}`)
```

### Cost-Saving Tips

1. **Use Thinking Mode**: Enable reasoning to reduce follow-up queries
2. **Optimize Prompts**: Be specific and concise in prompts
3. **Batch Processing**: Process multiple items in parallel
4. **Cache Results**: Store and reuse previous research results
5. **Temperature Settings**: Use lower temperature (0.1-0.3) for consistent outputs

## Deployment

### Docker Configuration

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

ENV NODE_ENV=production

CMD ["npm", "start"]
```

### Environment Variables for Production

```bash
# Required
GEMINI_API_KEY=your_production_api_key

# Optional
NODE_ENV=production
LOG_LEVEL=info
MAX_PARALLEL_REQUESTS=2
DEFAULT_DELAY_MS=5000
```

## Monitoring and Analytics

### Performance Metrics

Track these metrics for optimization:

- **Request Latency**: Average response time per request
- **Success Rate**: Percentage of successful requests
- **Token Usage**: Total tokens consumed
- **Cost per Query**: API cost per research request
- **Grounding Quality**: Accuracy of grounded information

### Sample Monitoring Script

```typescript
const metrics = {
  totalRequests: 0,
  successfulRequests: 0,
  totalTokens: 0,
  averageLatency: 0,
  errors: new Map<string, number>()
}

function trackRequest(success: boolean, tokens: number, latency: number, error?: string) {
  metrics.totalRequests++
  if (success) {
    metrics.successfulRequests++
    metrics.totalTokens += tokens
  }
  if (error) {
    const count = metrics.errors.get(error) || 0
    metrics.errors.set(error, count + 1)
  }

  // Update average latency
  metrics.averageLatency = (metrics.averageLatency * (metrics.totalRequests - 1) + latency) / metrics.totalRequests
}
```

## Best Practices

1. **Security**
   - Never expose API keys in client-side code
   - Use environment variables for sensitive configuration
   - Implement proper input validation and sanitization

2. **Performance**
   - Use connection pooling for HTTP requests
   - Implement proper error handling and retry logic
   - Monitor token usage to control costs

3. **Quality**
   - Validate extracted data against expected schemas
   - Use confidence scores for extracted information
   - Implement human review for critical data points

4. **Scalability**
   - Design for horizontal scaling
   - Use queue systems for large batch jobs
   - Implement proper resource cleanup

## Troubleshooting

### Debug Mode

Enable debug mode to see full request/response details:

```typescript
const researcher = new ResearchService()
researcher.setDebugMode(true)
```

### Common Issues

1. **Memory Issues**: Reduce `maxParallel` and implement proper cleanup
2. **Rate Limits**: Implement exponential backoff and request queuing
3. **JSON Parsing**: Ensure response MIME type is set correctly
4. **File Permissions**: Check write permissions for output directories

### Support Resources

- [Google Gemini API Documentation](https://ai.google.dev/docs)
- [Google AI Studio](https://makersuite.google.com)
- [Rate Limits and Pricing](https://ai.google.dev/pricing)
- [Grounding Documentation](https://ai.google.dev/docs grounding)

## License

This implementation is provided as-is for educational and development purposes. Please refer to Google's terms of service for API usage guidelines.
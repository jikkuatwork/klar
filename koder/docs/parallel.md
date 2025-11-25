# Parallel.ai API cURL Examples for LLM.txt

## 1. Search API

### Sample Request (Search)

```bash
curl https://api.parallel.ai/v1beta/search \
  -H "Content-Type: application/json" \
  -H "x-api-key: $PARALLEL_API_KEY" \
  -H "parallel-beta: search-extract-2025-10-10" \
  -d '{
    "objective": "When was the United Nations established? Prefer UN'\''s websites.",
    "search_queries": [
      "Founding year UN",
      "Year of founding United Nations"
    ],
    "max_results": 10,
    "excerpts": {
      "max_chars_per_result": 10000
    }
  }'
```

## 2. Extract API

### Extract API Example (Extract)

```bash
curl https://api.parallel.ai/v1beta/extract \
  -H "Content-Type: application/json" \
  -H "x-api-key: $PARALLEL_API_KEY" \
  -H "parallel-beta: search-extract-2025-10-10" \
  -d '{
    "urls": ["https://www.un.org/en/about-us/history-of-the-un"],
    "objective": "When was the United Nations established?",
    "excerpts": true,
    "full_content": false
  }'
```

## 3. Task API

### Execute your First Task Run (Simple Query -> Simple Answer)

```bash
echo "Creating the run:"
RUN_JSON=$(curl -s "https://api.parallel.ai/v1/tasks/runs" \
-H "x-api-key: ${PARALLEL_API_KEY}" \
-H "Content-Type: application/json" \
-d '{
    "task_spec": {
        "output_schema": "The founding date of the company in the format MM-YYYY"
    },
    "input": "United Nations",
    "processor": "base"
}')
echo "$RUN_JSON" | jq .
RUN_ID=$(echo "$RUN_JSON" | jq -r '.run_id')

echo "Retrieving the run result, blocking until the result is available:"
curl -s "https://api.parallel.ai/v1/tasks/runs/${RUN_ID}/result" \
  -H "x-api-key: ${PARALLEL_API_KEY}" | jq .
```

### Simple Query -> Structured Output

```bash
echo "Creating the run:"
RUN_JSON=$(curl -s 'https://api.parallel.ai/v1/tasks/runs' \
-H "x-api-key: ${PARALLEL_API_KEY}" \
-H 'Content-Type: application/json' \
-d '{
"input": "United Nations",
"processor": "core",
"task_spec": {
"output_schema": {
  "type": "json",
  "json_schema": {
    "type": "object",
    "properties": {
      "founding_date": {
        "type": "string",
        "description": "The official founding date of the company in the format MM-YYYY"
      },
      "employee_count": {
        "type": "string",
        "enum": [
          "1-10 employees",
          "11-50 employees",
          "51-200 employees",
          "201-500 employees",
          "501-1000 employees",
          "1001-5000 employees",
          "5001-10000 employees",
          "10001+ employees"
        ],
        "description": "The range of employees working at the company. Choose the most accurate range possible and make sure to validate across multiple sources."
      },
      "funding_sources": {
        "type": "string",
        "description": "A detailed description, containing 1-4 sentences, of the company's funding sources, including their estimated value."
      }
    },
    "required": ["founding_date", "employee_count", "funding_sources"],
    "additionalProperties": false
  }
}
}
}'
)
echo "$RUN_JSON" | jq .
RUN_ID=$(echo "$RUN_JSON" | jq -r '.run_id')

echo "Retrieving the run result, blocking until the result is available:"
curl -s "https://api.parallel.ai/v1/tasks/runs/${RUN_ID}/result" \
  -H "x-api-key: ${PARALLEL_API_KEY}" | jq .
```

### Structured Input -> Structured Output

```bash
echo "Creating the run:"
RUN_JSON=$(curl -s 'https://api.parallel.ai/v1/tasks/runs' \
-H "x-api-key: ${PARALLEL_API_KEY}" \
-H 'Content-Type: application/json' \
-d '{
"input": {
"company_name": "United Nations",
"company_website": "www.un.org"
},
"processor": "core",
"task_spec": {
"output_schema": {
  "type": "json",
  "json_schema": {
    "type": "object",
    "properties": {
      "founding_date": {
        "type": "string",
        "description": "The official founding date of the company in the format MM-YYYY"
      },
      "employee_count": {
        "type": "string",
        "enum":[
          "1-10 employees",
          "11-50 employees",
          "51-200 employees",
          "201-500 employees",
          "501-1000 employees",
          "1001-5000 employees",
          "5001-10000 employees",
          "10001+ employees"
        ],
        "description": "The range of employees working at the company. Choose the most accurate range possible and make sure to validate across multiple sources."
      },
      "funding_sources": {
        "type": "string",
        "description": "A detailed description, containing 1-4 sentences, of the company's funding sources, including their estimated value."
      }
    },
    "required": ["founding_date", "employee_count", "funding_sources"],
    "additionalProperties": false
  }
},
"input_schema": {
  "type": "json",
  "json_schema": {
    "type": "object",
    "properties": {
      "company_name": {
        "type": "string",
        "description": "The name of the company to research"
      },
      "company_website": {
        "type": "string",
        "description": "The website of the company to research"
      }
    },
    "required": ["company_name", "company_website"]
  }
}
}
}'
)
echo "$RUN_JSON" | jq .
RUN_ID=$(echo "$RUN_JSON" | jq -r '.run_id')

echo "Retrieving the run result, blocking until the result is available:"
curl -s "https://api.parallel.ai/v1/tasks/runs/${RUN_ID}/result" \
  -H "x-api-key: ${PARALLEL_API_KEY}" | jq .
```

## 4. Chat API

### Example Execution (Chat)

```bash
curl -N https://api.parallel.ai/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $PARALLEL_API_KEY" \
  -d '{
    "model": "speed",
    "messages": [
      { "role": "user", "content": "What does Parallel Web Systems do?" }
    ],
    "stream": false,
    "response_format": {
      "type": "json_schema",
      "json_schema": {
        "name": "reasoning_schema",
        "schema": {
          "type": "object",
          "properties": {
            "reasoning": {
              "type": "string",
              "description": "Think step by step to arrive at the answer"
            },
            "answer": {
              "type": "string",
              "description": "The direct answer to the question"
            },
            "citations": {
              "type": "array",
              "items": { "type": "string" },
              "description": "Sources cited to support the answer"
            }
          }
        }
      }
    }
  }'
```

## 5. FindAll API

### Step 1: Ingest (FindAll)

```bash
curl -X POST "https://api.parallel.ai/v1beta/findall/ingest" \
  -H "x-api-key: $PARALLEL_API_KEY" \
  -H "parallel-beta: findall-2025-09-15" \
  -H "Content-Type: application/json" \
  -d '{
    "objective": "FindAll portfolio companies of Khosla Ventures founded after 2020"
  }'
```

### Step 2: Create FindAll Run

```bash
curl -X POST "https://api.parallel.ai/v1beta/findall/runs" \
  -H "x-api-key: $PARALLEL_API_KEY" \
  -H "parallel-beta: findall-2025-09-15" \
  -H "Content-Type: application/json" \
  -d '{
    "objective": "FindAll portfolio companies of Khosla Ventures founded after 2020",
    "entity_type": "companies",
    "match_conditions": [
      {
        "name": "khosla_ventures_portfolio_check",
        "description": "Company must be a portfolio company of Khosla Ventures."
      },
      {
        "name": "founded_after_2020_check",
        "description": "Company must have been founded after 2020."
      }
    ],
    "generator": "core",
    "match_limit": 5
  }'
```

### Step 3: Poll for Status

```bash
curl -X GET "https://api.parallel.ai/v1beta/findall/runs/findall_40e0ab8c10754be0b7a16477abb38a2f" \
  -H "x-api-key: $PARALLEL_API_KEY" \
  -H "parallel-beta: findall-2025-09-15"
```

### Step 4: Get Results

```bash
curl -X GET "https://api.parallel.ai/v1beta/findall/runs/findall_40e0ab8c10754be0b7a16477abb38a2f/result" \
  -H "x-api-key: $PARALLEL_API_KEY" \
  -H "parallel-beta: findall-2025-09-15"
```

## 6. Monitor API

### Step 1. Create Monitor

```bash
curl --request POST \
  --url https://api.parallel.ai/v1alpha/monitors \
  --header 'Content-Type: application/json' \
  --header "x-api-key: $PARALLEL_API_KEY" \
  --data '{
    "query": "Extract recent news about quantum in AI",
    "cadence": "daily",
    "webhook": {
      "url": "https://example.com/webhook",
      "event_types": ["monitor.event.detected"]
    },
    "metadata": { "key": "value" }
  }'
```

### Step 2. Retrieve Events for an Event group

```bash
curl --request GET \
  --url "https://api.parallel.ai/v1alpha/monitors/<monitor_id>/event_groups/<event_group_id>" \
  --header "x-api-key: $PARALLEL_API_KEY"
```

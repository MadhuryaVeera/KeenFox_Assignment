# System Architecture Design - KeenFox Intelligence Engine

## Executive Summary

KeenFox Intelligence Engine is an **AI-powered competitive intelligence system** that automatically analyzes competitor data, extracts strategic signals, and generates actionable campaign recommendations for B2B SaaS companies.

### Key Features
- **Multi-source Data Aggregation**: Web scraping, G2 reviews, Reddit, LinkedIn, pricing pages
- **LLM-powered Analysis**: Google Gemini AI for structured insight extraction
- **JSON Report Generation**: Structured, downloadable reports (JSON, Markdown, PDF, Excel)
- **Campaign Recommendations**: AI-generated messaging, channel strategy, and GTM recommendations
- **Multi-competitor Support**: Analyze 4+ competitors simultaneously per brand

---

## System Architecture

### High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Input (Brand Name)                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Intelligence Engine (Core Service)                  │
│ - Identify competitors for brand                                │
│ - Gather web data for each competitor                           │
└────────────┬──────────────────────────────────────────────────┘
             │
    ┌────────┴──────────────────┬─────────────┐
    │                           │             │
    ▼                           ▼             ▼
┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Web Scraper    │  │  LLM Service     │  │  Database        │
│  - Websites     │  │  - Extract       │  │  - Store brand   │
│  - G2 reviews   │  │    insights      │  │  - Store signals │
│  - Pricing      │  │  - Generate      │  │  - Store reports │
│  - Reddit/      │  │    campaign recs │  │                  │
│    LinkedIn     │  │  - Market        │  │                  │
│                 │  │    analysis      │  │                  │
└────────┬────────┘  └──────────┬───────┘  └──────────────────┘
         │                      │
         └──────────┬───────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│          Report Generator (Output Pipeline)                     │
│ - JSON Report                                                   │
│ - Markdown Report                                               │
│ - PDF Report                                                    │
│ - Excel Report                                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│           API Response + Downloadable Reports                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### Backend (Python + Flask)

#### 1. **Intelligence Engine (`services/intelligence_engine.py`)**
```python
# KeenFox Competitive Intelligence System

## 1. Purpose

KeenFox is a browser-based competitive intelligence platform that turns a brand name into a structured market brief. The system is built for teams that want faster competitive research without manually gathering every signal from websites, review platforms, and scattered public sources.

The central problem is not a lack of data. It is the lack of a workflow that turns raw market noise into something usable. KeenFox addresses that by combining automated discovery, analysis, storage, and report generation in one loop.

### What the system should solve

- Reduce the time needed to study a brand's competitive landscape
- Keep the analysis tied to the actual category and positioning of the brand
- Preserve report history so repeated runs can be compared over time
- Produce outputs that are readable by humans and usable by downstream tools

---

## 2. System Shape

### 2.1 Staged Processing Model

KeenFox uses a five-stage flow. Each stage has a single purpose and returns structured data for the next stage.

```mermaid
flowchart LR
  A[Brand Input] --> B[Discovery]
  B --> C[Collection]
  C --> D[Interpretation]
  D --> E[Strategy]
  E --> F[Reports]

  classDef stage fill:#7f1d1d,stroke:#ef4444,color:#ffffff,stroke-width:2px;
  class A,B,C,D,E,F stage;
```

### 2.2 Why this shape works

The architecture is intentionally split so the system can be debugged and improved one stage at a time.

- Discovery finds the right competitors for the brand
- Collection gathers public web and market signals
- Interpretation turns raw text into structured intelligence
- Strategy converts intelligence into campaign recommendations
- Reports package the result into downloadable formats and history records

This avoids a monolithic prompt that tries to do everything at once and returns generic output.

### 2.3 Component Map

| Component | Job | Input | Output |
|---|---|---|---|
| `intelligence_engine.py` | Select competitors and assemble the analysis pipeline | Brand name | Competitor set and analysis bundle |
| `web_scraper.py` | Gather public competitor signals | URLs and competitor names | Raw text and page data |
| `llm_service.py` | Extract structured insight and strategic meaning | Raw signals and prompt context | JSON insight objects |
| `report_generator.py` | Produce downloadable deliverables | Analysis payload | JSON and PDF files |
| `database.py` | Persist brands, analyses, and reports | Analysis records | SQLite rows |
| `routes.py` | Expose the backend API | HTTP requests | API responses and file links |

---

## 3. Analysis Workflow

### 3.1 Brand to report path

1. A user types a brand into the React dashboard.
2. The frontend sends `POST /api/analyze`.
3. The backend identifies the brand category and chooses competitors.
4. Public signals are collected for those competitors.
5. Gemini-based extraction converts the signals into structured insight.
6. Market synthesis builds a broader competitive picture.
7. Campaign recommendations are generated from the synthesis.
8. The backend writes database records and report files.
9. The frontend receives report links and renders the result in the UI.

### 3.2 What gets analyzed

For each competitor, KeenFox tries to understand:

- Messaging and positioning
- Product strengths and weak spots
- Pricing cues and value framing
- Customer sentiment and complaints
- Market opportunities and gaps
- Strategic moves that signal future direction

### 3.3 Why minimum competitor coverage matters

The system is designed to analyze a broader set of competitors rather than a tiny shortlist. A wider competitive set gives the model more room to compare themes, spot repeated weaknesses, and identify market whitespace.

That choice is important because competitive strategy usually emerges from patterns across the market, not from a single competitor.

---

## 4. Intelligence Layer

### 4.1 Discovery logic

Competitor discovery is brand-aware rather than static. The engine uses category hints and fallback sets so unfamiliar brands still produce a useful result.

The discovery layer is responsible for avoiding generic output like "competitor A, competitor B" without context. It should return competitors that actually matter to the brand's market position.

### 4.2 Signal interpretation

The model is not asked to summarize pages line-by-line. It is asked to identify strategic signals:

- What the competitor claims
- What customers praise or dislike
- Where the market is under-served
- What tactical opportunities the brand can exploit

This is a deliberate design decision. Summary is easy. Strategy is the real value.

### 4.3 Structured output

Every major step returns structured JSON so the next step can reuse it without parsing fragile prose. That keeps the pipeline predictable and easier to test.

---

## 5. Campaign Logic

### 5.1 Two-step reasoning

Campaign output is created in two passes.

**Pass 1: market understanding**

The system first builds a cross-competitor view of the market:

- strongest threats
- best opportunities
- repeated customer pain points
- positioning gaps
- likely white space

**Pass 2: recommendations**

The system then turns that understanding into practical actions:

- headline and messaging angles
- channel choices
- GTM priorities
- short-term actions and longer-term positioning

### 5.2 Why this matters

If the model is pushed directly from raw data to recommendations, the result tends to be broad advice that could apply to any company. The two-stage design forces the system to reason first and recommend second.

---

## 6. Prompting Approach

### 6.1 Prompt principles

The prompt set is designed around a few rules:

- Each prompt has one task
- JSON output is preferred over freeform text
- Strategic context is passed forward between steps
- Answers must be grounded in the collected signals
- Brand-specific placeholders keep the system reusable

### 6.2 Prompt categories

| Prompt type | Purpose |
|---|---|
| Competitor discovery | Find relevant competitors for a brand |
| Brand profiling | Infer category, segment, and framing |
| Signal extraction | Convert raw content into structured insight |
| Market synthesis | Compare competitors and identify patterns |
| Campaign generation | Produce actionable GTM recommendations |
| Ask AI | Answer follow-up questions from the stored analysis |

### 6.3 Model selection

The current app is built around Gemini because it is already integrated into the backend and works well for structured reasoning, extraction, and follow-up Q&A.

The key requirement here is not just model strength. It is predictable JSON output, reasonable latency, and enough reliability for repeated brand analyses.

---

## 7. Data Persistence

### 7.1 Storage model

KeenFox uses SQLite to store the objects created during analysis:

- brands
- competitor analysis rows
- campaign recommendations
- intelligence reports
- web signals

### 7.2 Why persistence is important

Persistence makes the system more than a single-run generator. It allows:

- Report history in the UI
- Comparison against previous runs
- Later review of strategy changes
- File downloads without re-running the analysis

### 7.3 Report files

Each run produces downloadable artifacts in `backend/reports/`. The Reports tab surfaces these files so the user can open, compare, or reuse them later.

---

## 8. Frontend Design

### 8.1 UI structure

The React frontend is organized around a dashboard-style workflow:

- Brand search and start screen
- Signals tab for competitor intelligence
- Campaign tab for recommendations
- Ask AI tab for follow-up questions
- Reports tab for history and downloads

### 8.2 Interaction model

The interface is built to keep the analysis visible after the run completes. The user should be able to move between summary, strategy, and history without losing context.

### 8.3 Ask AI behavior

The Ask AI feature is designed to feel conversational but remain tied to the stored analysis. It returns longer answers, brand-related follow-up questions, and content that is relevant to the current report instead of generic chatbot text.

---

## 9. Operational Trade-offs

### 9.1 Why the system favors structure over speed

The app makes several deliberate trade-offs:

- It analyzes enough competitors to be useful, even if that takes longer
- It stores reports so history is preserved
- It asks the model to reason in structured steps rather than freeform prose
- It chooses predictable output over short but vague answers

### 9.2 Current limitations

- Results depend on the quality of public information available for the brand
- Some web sources may block scraping or provide thin content
- Analysis quality depends on model response quality
- The app is a point-in-time intelligence tool, not a live continuous monitor

---

## 10. Summary

KeenFox is designed as a practical competitive intelligence system, not a generic report generator. Its value comes from a simple idea: take a brand name, collect the right signals, turn them into structured insight, and present the results in a way that can be reviewed and reused.

The current implementation keeps that idea focused through modular backend services, report history, branded analysis, and an Ask AI workflow that stays connected to the latest analysis.
created_at DATETIME
updated_at DATETIME
```

### CompetitorAnalysis
```sql
id STRING PRIMARY KEY
brand_id STRING FOREIGN KEY
competitor_name STRING
features TEXT (JSON)
messaging TEXT (JSON)
customer_sentiment TEXT (JSON)
pricing TEXT (JSON)
weaknesses TEXT (JSON)
market_position STRING
threat_level STRING
sources TEXT (JSON)
created_at DATETIME
updated_at DATETIME
```

### IntelligenceReport
```sql
id STRING PRIMARY KEY
brand_id STRING FOREIGN KEY
report_title STRING
report_data TEXT (JSON)
summary TEXT
key_findings TEXT (JSON array)
competitors_analyzed INTEGER
signals_extracted INTEGER
file_path STRING
file_format STRING
created_at DATETIME
```

### CampaignRecommendation
```sql
id STRING PRIMARY KEY
brand_id STRING FOREIGN KEY
messaging_copy TEXT (JSON)
channel_strategy TEXT (JSON)
gtm_recommendations TEXT (JSON)
overall_strategy TEXT
priority_score FLOAT
created_at DATETIME
```

---

## API Contract

### POST /api/analyze

**Request:**
```json
{
  "brand_name": "Notion"
}
```

**Response (200):**
```json
{
  "status": "success",
  "brand_id": "uuid",
  "brand_name": "Notion",
  "analysis": {
    "brand_name": "Notion",
    "analyzed_at": "2024-01-01T12:00:00",
    "competitors_analyzed": 5,
    "signals_extracted": 47,
    "competitor_data": [
      {
        "competitor_name": "Asana",
        "website": "https://asana.com",
        "insights": {...},
        "threat_level": "high",
        "market_position": "direct_competitor",
        "signals": [...]
      }
    ],
    "market_analysis": {
      "market_position": "Strong Contender",
      "threat_level": "high",
      "key_threats": [...],
      "opportunities": [...]
    },
    "campaign_recommendations": {
      "overall_strategy": "...",
      "messaging_positioning": {...},
      "channel_strategy": {...},
      "gtm_recommendations": [...]
    }
  },
  "reports": {
    "json": "/path/to/notion_report.json",
    "markdown": "/path/to/notion_report.md",
    "pdf": "/path/to/notion_report.pdf",
    "excel": "/path/to/notion_report.xlsx"
  }
}
```

---

## Security Considerations

1. **API Key Management**: Store GOOGLE_API_KEY in .env, never commit
2. **CORS**: Restrict to frontend origin
3. **Rate Limiting**: Add per-IP limits (future)
4. **Input Validation**: Sanitize brand_name input
5. **Error Messages**: Don't leak sensitive info in error responses

---

## Performance Metrics

- **Analysis Time**: ~30-60 seconds per brand (depends on scraping)
- **LLM Response**: ~5-10 seconds per request
- **Database**: SQLite can handle ~1000 brands easily
- **Report Generation**: ~2-5 seconds per format

---

## Testing Strategy

1. **Unit Tests**: LLM parsing, data extraction
2. **Integration Tests**: End-to-end analysis flow
3. **Mock Data**: For CI/CD (no real API calls)
4. **Load Testing**: Concurrent brand analyses

---


## Conclusion

KeenFox Intelligence Engine provides a scalable, AI-powered competitive intelligence pipeline. The modular architecture allows for easy enhancement, custom data sources, and advanced analytics. The JSON report output ensures compatibility with downstream BI tools and dashboards.

**Next Steps:**
1. Add real data source APIs
2. Implement change tracking
3. Build natural language Q&A interface
4. Deploy to production
5. Gather user feedback for improvements

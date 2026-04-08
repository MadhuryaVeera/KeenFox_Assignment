# KeenFox AI Competitive Intelligence System

KeenFox is a full-stack competitive intelligence app that analyzes a brand, discovers relevant competitors, extracts market signals, and generates downloadable JSON and PDF reports. It is designed for live analysis runs, not static demo data, so each report reflects the current state of the market and the selected brand.

## What It Does

KeenFox takes a brand name, finds the most relevant competitors, and builds a strategic view of the market around that brand. The app summarizes strengths, weaknesses, positioning, pricing signals, campaign opportunities, and market threats in a format that is easy to review, download, and compare later.

The Reports tab keeps previous runs visible so you can look back at past analyses instead of only seeing the most recent result.

## Core Features

- Brand-specific competitor discovery with category-aware fallbacks
- Analysis of strengths, weaknesses, pricing, positioning, and market signals
- Campaign recommendations based on competitive gaps and opportunity areas
- Ask AI with longer brand-aware answers and follow-up questions
- Saved report history in the Reports tab
- JSON and PDF downloads for every run
- Report comparison support for repeated analyses of the same brand

## Stack

- Backend: Flask, SQLite, SQLAlchemy, Gemini, ReportLab
- Frontend: React, Axios, CSS

## Project Intent

KeenFox is built to turn a brand name into a practical competitive intelligence brief. The project is meant to help you understand:

- which competitors matter most
- how those competitors position themselves
- where the market is crowded or weak
- what product, messaging, and campaign opportunities exist
- how the same brand changes over time across repeated runs

The focus is on useful analysis output instead of generic AI text. Each run is meant to produce something you can review, compare, and share.

## How the App Works

1. Enter a brand name in the dashboard.
2. The frontend sends the request to the Flask backend.
3. The intelligence engine detects the brand category and selects relevant competitors.
4. The backend gathers signals, runs analysis, and builds campaign recommendations.
5. The analysis is saved in SQLite and written to JSON and PDF files.
6. The UI shows the result in the Signals, Campaign, Ask AI, and Reports tabs.

## Project Structure

```text
KeefoxAI/
├── backend/
│   ├── app.py
│   ├── app/
│   │   └── routes.py
│   ├── models/
│   │   └── database.py
│   ├── services/
│   │   ├── intelligence_engine.py
│   │   ├── llm_service.py
│   │   └── web_scraper.py
│   ├── utils/
│   │   └── report_generator.py
│   ├── reports/
│   └── requirements.txt
├── frontend/
│   ├── package.json
│   ├── public/
│   └── src/
│       ├── components/
│       ├── pages/
│       │   ├── Dashboard.js
│       │   ├── Dashboard.css
│       │   ├── AnalysisDashboard.js
│       │   └── AnalysisDashboard.css
│       └── config/
│           └── api.js
├── README.md
├── DESIGN_DOC.md
├── QUICKSTART.md
└── .gitignore
```

## Repository Notes

- `backend/reports/` stores the generated JSON and PDF outputs.
- `frontend/public/` contains the static assets used by the React app.
- `frontend/src/components/` is available for reusable UI pieces.
- `QUICKSTART.md` is the short setup reference if you do not want the full README.

## Setup

### Backend

```powershell
cd backend
py -3 -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env`:

```env
GOOGLE_API_KEY=your_google_ai_studio_key
```

Run the backend:

```powershell
.\venv\Scripts\python.exe app.py
```

Backend health:

- http://127.0.0.1:5000/api/health

### Frontend

```powershell
cd frontend
npm install
npm start
```

Open the app:

- http://localhost:3000

## Usage

1. Enter a brand name.
2. Run the analysis.
3. Review the Signals, Campaign, Ask AI, and Reports tabs.
4. Download the JSON or PDF report for that run.
5. Return later to compare against saved report history.

## API

### Analyze

```http
POST /api/analyze
```

Example:

```json
{
  "brand_name": "Notion",
  "competitor_count": 8
}
```

### Ask AI

```http
POST /api/ask
```

### Reports

```http
GET /api/reports
GET /api/reports/files/<filename>
GET /api/reports/<report_id>/download
```

## Report Output

Reports are generated in `backend/reports/` and stored in the database as report history. Each run can produce a JSON file for structured data and a PDF file for a readable summary. The Reports tab surfaces those saved runs in the UI.

## Why This Project Exists

This app is meant to help a user quickly understand where a brand stands in its market, who it competes with, what those competitors are doing well, and where the best strategic opportunities are. The goal is not just to list competitors, but to turn the analysis into something useful for product, marketing, and positioning decisions.

## Notes

- Keep `backend/venv/` and `frontend/node_modules/` out of GitHub.
- Set the Gemini API key before running the backend.
- If the backend is running but the UI cannot connect, confirm the API is on `http://127.0.0.1:5000/api`.
- The generated report files are runtime output and should not be committed manually.

## Troubleshooting

- If the backend fails to start, check the `.env` file and confirm the virtual environment is activated.
- If the frontend does not load, run `npm install` again in the frontend folder.
- If report downloads fail, make sure the backend is running and the `backend/reports/` folder exists.

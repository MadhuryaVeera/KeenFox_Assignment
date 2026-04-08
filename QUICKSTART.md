# KeenFox Quick Start

Use this guide to run the current KeenFox web app.

## What You Need

- Python 3.10+ 
- Node.js 18+
- Google Gemini API key for backend analysis

## 1. Backend Setup

```powershell
cd backend
py -3 -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env` and add:

```env
GOOGLE_API_KEY=your_google_ai_studio_key
```

Start the backend:

```powershell
.\venv\Scripts\python.exe app.py
```

Backend health endpoint:

- http://127.0.0.1:5000/api/health

## 2. Frontend Setup

Open a second terminal:

```powershell
cd frontend
npm install
npm start
```

Open the app:

- http://localhost:3000

## 3. Run the App

1. Open http://localhost:3000
2. Enter a brand name such as Notion, Nike, or LG
3. Run analysis
4. Review the Signals tab
5. Check the Campaign tab for recommendations
6. Use Ask AI for brand-specific questions
7. Open the Reports tab to see JSON/PDF downloads and report history

## 4. Expected Behavior

- Backend returns live analysis from `/api/analyze`
- Reports are generated in JSON and PDF formats
- Reports history appears under the Reports tab
- Ask AI returns a longer brand-aware answer with follow-up questions

## 5. Common Commands

### Backend

```powershell
cd backend
.\venv\Scripts\python.exe app.py
```

### Frontend

```powershell
cd frontend
npm start
```

### Health Check

```powershell
Invoke-RestMethod http://127.0.0.1:5000/api/health
```

### Generate a Report

From the UI, analyze a brand. The latest report files will be created in `backend/reports/`.

## 6. Troubleshooting

If the backend does not start:
- Confirm `GOOGLE_API_KEY` is set in `backend/.env`
- Reinstall backend dependencies with `pip install -r requirements.txt`
- Make sure port `5000` is free

If the frontend does not start:
- Reinstall frontend dependencies with `npm install`
- Make sure port `3000` is free

If the Reports tab is empty:
- Run a fresh analysis from the UI
- Refresh the page

## 7. Notes

- The project is now a web app, not a CLI script
- Keep `backend/venv/` and `frontend/node_modules/` out of GitHub
- Generated reports are stored in `backend/reports/`

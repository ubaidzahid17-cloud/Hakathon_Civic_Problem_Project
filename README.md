# CivicSignal — AI Smart Civic Services

An end-to-end civic complaint intake and service-management platform built for the
**AI Smart Civic Services** hackathon (Batch 4 — Statistics benchmark, with full
OOP architecture and AI classification/prioritization/summarization).

## 1. The problem

Citizens face broken streetlights, potholes, water leaks, overflowing garbage bins
and similar local-service issues, but reporting is fragmented and service teams
struggle to tell which complaints are urgent and which department should own them.
CivicSignal turns a free-text complaint into structured, actionable information:
**category, priority, responsible department, and a short summary** — automatically.

## 2. Features

- **Citizen portal** (`/`) — submit a complaint (description + location), get
  instant AI-analyzed feedback (category, priority, assigned department, summary,
  and a plain-language explanation of how the AI reached that result).
- **Service Desk dashboard** (`/admin`) — live stats, category/priority charts,
  full resolution-time statistics (mean, median, mode, variance, std dev, IQR,
  outlier fences), search/filter (category, priority, status, location, keyword),
  and inline status management.
- **Mandatory AI feature**: complaint classification + priority prediction +
  extractive summarization, implemented as an explainable, keyword-weighted NLP
  service (`ai_service.py`) — no external API key required, fully offline.
- **Full OOP architecture**: `Complaint`, `DatabaseManager`, `AIAnalyzer`,
  `ComplaintManager`, `StatisticsService`, `NotificationManager`.
- **Statistics-driven analytics**: mean, median, mode, min, max, range, variance,
  standard deviation, Q1/Q3, IQR and outlier fences on resolution times; frequency
  distributions for category, priority and department.
- **Error handling**: empty/invalid input, unknown complaint IDs, invalid status
  transitions, and AI-failure fallback (defaults to Other/Medium instead of crashing).

## 3. Architecture

```
Citizen / Admin UI  (HTML + vanilla JS + Chart.js)
        │
        ▼
Python API           (Flask — app.py)
        │
        ▼
Complaint Manager    (complaint_manager.py — orchestration layer)
        │        │
        ▼        ▼
  AI Service   Database Manager     (ai_service.py)   (models.py, SQLite)
        │
        ▼
Statistics Service    (stats_service.py)
        │
        ▼
Admin Dashboard        (charts + stat cards + table)
```

Reference flow: `Citizen UI → Python API → Complaint Manager → AI Service → Database → Admin Dashboard`

### File structure

```
civic-app/
├── app.py                 # Flask routes (view + API layer only)
├── models.py               # Complaint entity + DatabaseManager (SQLite)
├── ai_service.py            # AIAnalyzer — the mandatory AI component
├── complaint_manager.py     # Orchestration: AI + DB + notifications
├── stats_service.py         # Descriptive statistics / analytics
├── notification_manager.py  # Status-change event log
├── seed_data.py              # Populates sample complaints for demo/testing
├── requirements.txt
├── templates/                # index.html (citizen), admin.html (dashboard), base.html
├── static/css/style.css      # Design system
├── static/js/                # citizen.js, admin.js, common.js
└── data/civic_services.db     # SQLite database (created on first run)
```

## 4. The AI component (mandatory requirement)

**Input:** raw complaint text (string), e.g.
*"There is a large water leak near the main road and traffic is becoming difficult."*

**Processing:**
1. **Classification** — normalized keyword-overlap scoring against six weighted
   lexicons (Road, Water/Drainage, Waste, Electricity, Safety, Other). The category
   with the highest weighted match wins; confidence is derived from how dominant
   that match is versus the others.
2. **Priority prediction** — a 0–100 heuristic score combining a category base
   severity (e.g. Electricity/Safety start higher than Waste) with urgency-signal
   words ("urgent", "sparking", "children", "since days", etc.), bucketed into
   Low / Medium / High / Critical.
3. **Summarization** — extractive: the sentence with the highest keyword density
   is returned, capped at ~25 words and tagged with the detected category.

**Output:** `{ category, priority, priority_score, confidence, keywords, summary, explanation }`
— stored with the complaint and shown to the citizen immediately.

**Why this approach:** it's fully explainable (every decision traces back to
specific matched words), requires no API key or GPU, runs instantly, and is easy
for a hackathon judge to audit — while still solving the real NLP task (unstructured
text → structured category + urgency + summary).

**Limitations (disclosed):**
- Keyword-based — can misclassify complaints with unusual phrasing, sarcasm, or
  vocabulary outside the lexicon.
- No true image understanding (the "photo available" checkbox is a data flag only;
  swapping in a vision model is the natural extension point — see §6).
- Priority score is a heuristic estimate, not a certified emergency-triage system;
  an admin can always override status manually.

## 5. Statistics implemented (Batch 4 benchmark)

On resolution time (hours) for resolved complaints: **mean, median, mode, min, max,
range, variance, standard deviation, Q1, Q3, IQR, and outlier fences (Q1 − 1.5·IQR,
Q3 + 1.5·IQR)**. Plus frequency distributions (count + %) for category, priority
and department, and top-line counts (open / in-progress / resolved / critical /
resolution rate). All of this is computed in `stats_service.py` and rendered on
the `/admin` dashboard with Chart.js bar charts and a resolution-time stat grid.

## 6. Setup & running locally

```bash
cd civic-app
pip install -r requirements.txt
python seed_data.py     # optional: adds ~17 sample complaints so the dashboard isn't empty
python app.py            # runs on http://localhost:5000
```

Visit `http://localhost:5000/` to submit a complaint, and `http://localhost:5000/admin`
for the dashboard.

## 7. Deployment

The app is a standard Flask application — deploy on Render, Railway, or
PythonAnywhere:
1. Push this folder to a GitHub repo.
2. Set the start command to `python app.py` (or `gunicorn app:app` for production —
   add `gunicorn` to `requirements.txt` first).
3. No environment variables/API keys are required since the AI runs locally.

## 8. Testing evidence (example)

| Input | Category | Priority | Confidence |
|---|---|---|---|
| "There is a large water leak near the main road and traffic is becoming difficult." | Water/Drainage | Medium | 0.53 |
| "Streetlight sparking dangerously near the school, urgent, kids walk here." | Electricity | Critical | high |
| "Minor delay in garbage pickup this week, one day late." | Waste | Low | moderate |

Run `python seed_data.py` then inspect `/admin` for a full spread of categories,
priorities and resolution-time statistics across ~17 sample complaints.

## 9. Suggested next steps (not implemented, called out per the AI-limitations rule)

- Swap `AIAnalyzer.classify` for a trained scikit-learn/Transformer text classifier
  once a labeled complaint dataset is available.
- Add an **AI Vision** hook: accept an uploaded image and route it through an
  image-classification model to corroborate the text-based category.
- Add a **RAG-based citizen assistant** for "what's the status of my complaint"
  natural-language queries.

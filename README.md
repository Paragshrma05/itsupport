# SupportDesk — AI-Powered IT Support & Ticketing System

A modern, portfolio-grade IT helpdesk built with Flask, SQLite, and Claude AI.

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![Flask](https://img.shields.io/badge/Flask-3.0-green) ![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey)

---

## Features

- **Authentication** — Register/login with JWT (cookie + header)
- **Role-Based Access** — Admin and User roles with separate dashboards
- **Ticket Management** — Create, view, update, delete tickets
- **Ticket Fields** — title, description, category, priority, status, timestamps
- **Ticket Filtering** — Filter by status, priority, category; full-text search
- **AI Categorization** — Claude auto-detects category & priority on submission
- **AI Suggestions** — Troubleshooting steps generated per ticket
- **Log Analyzer** — Upload or paste logs; AI detects auth failures, timeouts, API/DB errors
- **Admin Dashboard** — Stats, health score, full ticket queue
- **REST API** — Full JSON API with JWT auth

---

## Project Structure

```
itsupport/
├── app.py              # Flask factory + DB seeding
├── run.py              # Entry point
├── config.py           # Config & env vars
├── extensions.py       # Flask extensions (db, jwt, bcrypt, cors)
├── requirements.txt
├── Procfile            # Render deployment
├── .env.example
├── models/
│   └── models.py       # User, Ticket SQLAlchemy models
├── routes/
│   ├── auth.py         # /register, /login, /logout, /api/auth/*
│   ├── tickets.py      # /tickets/*, /api/tickets/*
│   └── main.py         # /dashboard, /log-analyzer, /api/stats
├── services/
│   └── ai_service.py   # Claude API integration (with rule-based fallback)
└── templates/
    ├── base.html
    ├── login.html / register.html
    ├── dashboard_admin.html / dashboard_user.html
    ├── tickets.html / ticket_detail.html / new_ticket.html
    └── log_analyzer.html
```

---

## Quick Start

```bash
# 1. Clone and enter
git clone https://github.com/youruser/itsupport.git
cd itsupport

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env — add your ANTHROPIC_API_KEY for AI features

# 5. Run
python run.py
# Open http://localhost:5000
```

---

## Demo Credentials

| Role  | Email                    | Password  |
|-------|--------------------------|-----------|
| Admin | admin@itsupport.dev      | admin123  |
| User  | jsmith@itsupport.dev     | user123   |

---

## REST API

All `/api/*` endpoints use JWT Bearer token auth (except login/register).

```bash
# Login
POST /api/auth/login
{"email": "admin@itsupport.dev", "password": "admin123"}

# Get current user
GET /api/auth/me
Authorization: Bearer <token>

# List tickets
GET /api/tickets?status=Open&priority=High
Authorization: Bearer <token>

# Create ticket (AI auto-classifies)
POST /api/tickets
{"title": "...", "description": "..."}

# Update ticket
PATCH /api/tickets/<id>
{"status": "In Progress"}

# Delete ticket
DELETE /api/tickets/<id>

# Analyze log
POST /api/analyze-log
{"log_text": "..."}

# Admin stats
GET /api/stats

# Admin user list
GET /api/users
```

---

## AI Features

Requires `ANTHROPIC_API_KEY` in `.env`. Without it, a rule-based fallback handles categorization and log analysis automatically — the app works fully without an API key.

### Ticket Analysis
- Detects category: Hardware, Software, Network, Security, Database, Authentication, Performance
- Detects priority: Low, Medium, High, Critical
- Generates 3 actionable troubleshooting suggestions

### Log Analyzer
- Detects: auth failures, timeouts, API errors, DB connection issues, memory errors
- Returns health score (0–100), issue list with severity, and recommendations

---

## Deploy to Render

1. Push to GitHub
2. Create new **Web Service** on [render.com](https://render.com)
3. Set environment variables:
   - `SECRET_KEY`
   - `JWT_SECRET_KEY`
   - `ANTHROPIC_API_KEY`
4. Build command: `pip install -r requirements.txt`
5. Start command: `gunicorn run:app`

> **Note**: For production, switch to PostgreSQL by updating `DATABASE_URL`.

---

## Tech Stack

| Layer     | Tech                              |
|-----------|-----------------------------------|
| Backend   | Python 3.10+, Flask 3.0           |
| Database  | SQLite (dev) / PostgreSQL (prod)  |
| ORM       | SQLAlchemy 2.0                    |
| Auth      | Flask-JWT-Extended, Flask-Bcrypt  |
| AI        | Anthropic Claude API              |
| Frontend  | Jinja2, Bootstrap 5, IBM Plex     |
| Deploy    | Gunicorn, Render                  |

---

## License

MIT

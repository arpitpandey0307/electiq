# 🗳️ ElectIQ — Election Process Education Assistant

> *"ElectIQ turns the complex maze of elections into a personalized, conversational, gamified journey — so every citizen walks in informed and walks out empowered."*

## ✨ Features

- 🧠 **AI Chat Assistant** — Gemini-powered, role-aware, streaming responses with source citations
- 🗓️ **Interactive Timeline** — Animated election milestones with detailed side panels
- 🎭 **Role-Based Personalization** — Voter, Candidate, Journalist, or Student personas
- 🧩 **Scenario Simulator** — "What If" decision trees for common election situations
- 🏆 **Gamified Quizzes** — 5 topics, badge system, progress tracking
- 📊 **Visual Glossary** — Key election terms with expandable explanations
- 🌙 **Dark Mode** — Automatic + manual toggle
- 🇮🇳 **Multilingual** — English + Hindi support

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- (Optional) Google Gemini API key for AI chat

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set Gemini API key (optional — app works without it in demo mode)
# Windows:
set GEMINI_API_KEY=your_key_here
# Linux/Mac:
export GEMINI_API_KEY=your_key_here

# Run the server
uvicorn backend.main:app --reload --port 8080

# Open http://localhost:8080
```

### Docker

```bash
docker build -t electiq .
docker run -p 8080:8080 -e GEMINI_API_KEY=your_key electiq
```

## ☁️ Deploy to Google Cloud Run

```bash
gcloud run deploy electiq \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=YOUR_KEY \
  --memory 512Mi \
  --port 8080
```

## 📁 Project Structure

```
electiq/
├── backend/
│   ├── main.py              # FastAPI entrypoint
│   ├── routers/             # API endpoints
│   │   ├── chat.py          # /api/chat (SSE streaming)
│   │   ├── timeline.py      # /api/timeline
│   │   ├── quiz.py          # /api/quiz/{topic}
│   │   └── scenarios.py     # /api/scenarios + /api/glossary
│   ├── services/
│   │   ├── gemini_service.py  # Gemini API wrapper
│   │   └── prompt_builder.py  # Role-aware prompts
│   └── data/                # JSON knowledge base
├── frontend/
│   ├── index.html           # SPA shell
│   ├── css/                 # Design system
│   ├── js/                  # App modules
│   └── assets/              # Translations
├── Dockerfile
├── requirements.txt
└── .github/workflows/deploy.yml
```

## 🔑 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Optional | Google Gemini API key for AI chat |
| `ALLOWED_ORIGINS` | Optional | CORS origins (default: `*`) |
| `APP_ENV` | Optional | `production` or `development` |

## 📄 License

MIT — Built for informed citizens, designed to win. 🗳️

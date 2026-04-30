<div align="center">
  <h1>🗳️ ElectIQ</h1>
  <p><strong>Your Election Process Education Assistant</strong></p>
  <p>
    <em>Turning the complex maze of elections into a personalized, conversational, and gamified journey — so every citizen walks in informed and walks out empowered.</em>
  </p>
  <p>
    <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python 3.11+">
    <img src="https://img.shields.io/badge/FastAPI-0.115.0-009688.svg" alt="FastAPI">
    <img src="https://img.shields.io/badge/Frontend-Vanilla_JS-f7df1e.svg" alt="Vanilla JS">
    <img src="https://img.shields.io/badge/AI-Google_Gemini_2.5_Flash-orange.svg" alt="Google Gemini">
    <img src="https://img.shields.io/badge/Deploy-Google_Cloud_Run-4285F4.svg" alt="Google Cloud Run">
    <img src="https://img.shields.io/badge/Tests-pytest-green.svg" alt="Tests">
    <img src="https://img.shields.io/badge/Security-OWASP-red.svg" alt="OWASP Security">
    <img src="https://img.shields.io/badge/A11y-WCAG_2.1-purple.svg" alt="WCAG 2.1">
    <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License MIT">
  </p>
</div>

<hr>

## ✨ Features

- 🧠 **AI Chat Assistant** — Gemini 2.5 Flash-powered, role-aware, SSE streaming responses with official source citations and safety filters.
- 🗓️ **Interactive Timeline** — Animated election milestones with detailed slide-in panels, key facts, and contextual FAQ.
- 🎭 **Role-Based Personalization** — Tailored experiences for First-Time Voters, Candidates, Journalists, and Students.
- 🧩 **Scenario Simulator** — "What If" interactive decision trees for handling common election situations.
- 🏆 **Gamified Quizzes** — 25 questions across 5 topics, featuring a progressive badge system with celebrations.
- 📊 **Visual Glossary** — Expandable definitions for 10 key electoral terms with "Dig Deeper" details.
- 🌙 **Dark Mode** — Automatic detection (`prefers-color-scheme`) plus manual toggle with preference persistence.
- 🇮🇳 **Multilingual Support** — English and Hindi i18n support out-of-the-box.
- ♿ **Accessible** — WCAG 2.1 compliant: ARIA roles/labels, keyboard navigation, skip links, screen reader support, reduced motion.
- 🔒 **Secure** — OWASP headers (CSP, HSTS, X-Frame-Options), rate limiting, input sanitization, non-root Docker.
- 🧪 **Tested** — Comprehensive pytest suite with 40+ tests covering endpoints, security, models, and data integrity.

---

## 🏗️ System Architecture

ElectIQ is built with a lightweight, cloud-native architecture optimized for speed, security, and low cost.

```mermaid
graph TD
    subgraph Client [Frontend - Vanilla JS/HTML/CSS]
        UI[User Interface]
        Chat[Chat Interface]
        TL[Timeline / Quiz / Scenarios]
        A11y[Accessibility Layer<br>ARIA + Keyboard Nav]
    end

    subgraph Server [Backend - FastAPI]
        MW[Middleware Stack<br>Security + Rate Limit + Logging]
        API[API Routers]
        PB[Prompt Builder]
        GS[Gemini Service<br>Connection Pool + Safety]
        DC[(In-Memory Data Cache)]
    end

    subgraph Google [Google Cloud Services]
        Gemini[Google Gemini 2.5 Flash API]
        CloudRun[Google Cloud Run]
        CloudLog[Google Cloud Logging]
    end

    UI -->|HTTP/SSE| MW
    MW --> API
    Chat -->|SSE Streaming| MW
    TL -->|Fetch JSON| MW

    API --> PB
    API --> DC
    PB --> GS
    GS <-->|REST API + Safety Settings| Gemini
    Server -->|Structured JSON Logs| CloudLog
    Server -->|Deployed on| CloudRun
```

---

## 🛡️ Security Architecture

| Layer | Protection |
|-------|-----------|
| **Transport** | HSTS, Cloud Run managed TLS |
| **Headers** | CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy |
| **Input** | Pydantic validation, HTML escaping, length limits, role pattern matching |
| **Rate Limiting** | 30 req/min per IP on API endpoints |
| **AI Safety** | Gemini content filters (harassment, hate, explicit, dangerous) |
| **Container** | Non-root user, slim base image, no cached packages |
| **Secrets** | Environment variables only, `.env` gitignored |

See [SECURITY.md](SECURITY.md) for full details.

---

## 🧪 Testing

ElectIQ includes a comprehensive pytest test suite with **40+ tests** covering:

- ✅ All API endpoints (happy paths + error cases)
- ✅ Security headers (CSP, HSTS, XSS protection)
- ✅ Input validation (XSS, oversized messages, invalid roles)
- ✅ Data integrity (quiz answers, dates, uniqueness)
- ✅ Pydantic model constraints and sanitization
- ✅ Response timing and performance benchmarks

```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=backend --cov-report=term-missing
```

See [TESTING.md](TESTING.md) for full guide.

---

## ♿ Accessibility (WCAG 2.1)

| Feature | Implementation |
|---------|---------------|
| **Skip Navigation** | Hidden link to main content, visible on focus |
| **Keyboard Navigation** | Arrow keys for tabs (WAI-ARIA pattern), Enter/Space for cards |
| **ARIA Roles** | `tablist`, `tab`, `tabpanel`, `dialog`, `radiogroup`, `log`, `alert` |
| **ARIA States** | `aria-selected`, `aria-checked`, `aria-expanded`, `aria-hidden`, `aria-modal` |
| **Screen Reader** | Live region announcements for tab switches, role changes, badges |
| **Focus Management** | Focus trapped in modals, moved to close button on panel open |
| **Reduced Motion** | `prefers-reduced-motion` media query disables animations |
| **Semantic HTML** | `<header>`, `<nav>`, `<main>`, `<aside>`, proper heading hierarchy |

---

## 🚶‍♂️ User Journey Flow

```mermaid
flowchart TD
    Start([User visits ElectIQ]) --> RoleSelect{Select Persona}
    RoleSelect -->|Voter| Home[Main Dashboard]
    RoleSelect -->|Candidate| Home
    RoleSelect -->|Journalist| Home
    RoleSelect -->|Student| Home

    Home --> ChatTab[💬 AI Chat]
    Home --> TimelineTab[🗓️ Timeline]
    Home --> ScenariosTab[🧩 Scenarios]
    Home --> QuizTab[🏆 Quiz]

    ChatTab --> Ask[Ask Election Questions]
    Ask --> AIStream[Receive Streamed AI Answer]
    AIStream --> Detect[Detect Topic Trigger]
    Detect -->|Relevant| ShowQuizCTA[Show Quiz CTA]

    TimelineTab --> Explore[Explore Election Phases]
    Explore --> ClickMilestone[Click Milestone]
    ClickMilestone --> DetailPanel[View Detailed Facts & FAQs]

    ScenariosTab --> PickScenario[Select 'What-If' Situation]
    PickScenario --> Walkthrough[Step-by-Step Resolution]

    QuizTab --> PickTopic[Select Topic]
    PickTopic --> Answer[Answer Questions]
    Answer --> Result{Score > 80%?}
    Result -->|Yes| Badge[Earn Badge & Celebrate!]
    Result -->|No| Retry[Review & Retry]
```

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+**
- *(Optional)* Google Gemini API key for full AI chat functionality.

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/arpitpandey0307/electiq.git
   cd electiq
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Create a `.env` file in the root directory (this file is ignored by git):
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ALLOWED_ORIGINS=*
   APP_ENV=development
   ```
   > **Note:** If no API key is provided, the app will gracefully fall back to a demo mode with preset responses.

4. **Run the development server:**
   ```bash
   uvicorn backend.main:app --reload --port 8080
   ```
   Navigate to `http://localhost:8080` in your browser.

5. **Run tests:**
   ```bash
   pytest -v
   ```

---

## 🐳 Docker Deployment

ElectIQ is fully containerized with security hardening (non-root user, health checks).

```bash
# Build the image
docker build -t electiq .

# Run the container
docker run -p 8080:8080 -e GEMINI_API_KEY=your_api_key electiq
```

---

## ☁️ Google Cloud Run Deployment

Deploy directly from source to Google Cloud Run:

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

### Google Cloud Services Used

| Service | Purpose |
|---------|---------|
| **Google Cloud Run** | Serverless container hosting with auto-scaling |
| **Google Gemini 2.5 Flash** | AI-powered conversational chat with safety filters |
| **Google Cloud Logging** | Structured JSON log ingestion and monitoring |
| **Google Fonts** | Inter + Playfair Display typography |

---

## 📁 Project Structure

```text
electiq/
├── backend/
│   ├── main.py              # FastAPI entrypoint with middleware stack
│   ├── config.py            # Centralized settings, data cache, logging
│   ├── middleware.py         # Security headers, rate limiting, request logging
│   ├── models.py            # Pydantic request/response models
│   ├── routers/             # API endpoint handlers
│   │   ├── chat.py          # /api/chat (SSE streaming)
│   │   ├── timeline.py      # /api/timeline
│   │   ├── quiz.py          # /api/quiz/{topic}
│   │   └── scenarios.py     # /api/scenarios & /api/glossary
│   ├── services/
│   │   ├── gemini_service.py  # Gemini API wrapper with connection pooling
│   │   └── prompt_builder.py  # Role-aware system prompts
│   └── data/                # JSON knowledge base
├── frontend/
│   ├── index.html           # Accessible SPA shell (WCAG 2.1)
│   ├── css/                 # Design system with a11y utilities
│   ├── js/                  # Modular JS with keyboard navigation
│   └── assets/              # Translations & static assets
├── tests/
│   ├── conftest.py          # Shared test fixtures
│   ├── test_api_endpoints.py  # API endpoint tests
│   ├── test_security.py     # Security & data integrity tests
│   └── test_models.py       # Pydantic model validation tests
├── Dockerfile               # Hardened container (non-root, health check)
├── pyproject.toml           # Project config & pytest settings
├── requirements.txt         # Runtime + test dependencies
├── SECURITY.md              # Security policy & measures
└── TESTING.md               # Testing guide & coverage
```

---

## 📄 License

This project is licensed under the **MIT License**.

<div align="center">
  <em>Built for informed citizens, designed to win. 🗳️</em>
</div>

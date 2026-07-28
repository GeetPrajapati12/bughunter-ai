<p align="center">
  <h1 align="center">🐛 BugHunter AI</h1>
  <p align="center">Universal AI-Powered Web Testing Agent</p>
  <p align="center">
    <img src="https://img.shields.io/badge/python-3.10+-blue?style=flat-square&logo=python" />
    <img src="https://img.shields.io/badge/AI-Anthropic%20%7C%20OpenAI%20%7C%20Gemini%20%7C%20Groq%20%7C%20Ollama-blueviolet?style=flat-square" />
    <img src="https://img.shields.io/badge/browser-Selenium%20%7C%20Playwright-green?style=flat-square" />
    <img src="https://img.shields.io/badge/license-MIT-orange?style=flat-square" />
  </p>
</p>

---

> Give it any website URL.
> It crawls the site, understands every page with AI, generates test cases,
> executes them automatically, finds bugs, captures screenshots, and produces
> a professional HTML/PDF report.
>
> **No hardcoding. No page-specific code. Works on any website. Works with any AI provider.**

---

## ✨ Features

- 🔍 **Universal Crawler** — BFS crawls any website up to configurable depth and page count
- 🧠 **AI Page Understanding** — AI analyses each page's purpose, components, and risk areas
- 📋 **AI Test Generation** — generates functional, security, and accessibility test cases per page
- 🤖 **Generic Test Execution** — Selenium or Playwright runner, zero hardcoded selectors
- 🐛 **AI Bug Analysis** — explains failures with root cause, severity, and suggested fix
- ♿ **Accessibility Checks** — WCAG 2.1 violations (missing alt, labels, heading order, etc.)
- 🔒 **Security Checks** — headers, cookies, CSRF, SSL, exposed files, injection signals
- 📊 **Professional Reports** — self-contained HTML report + optional PDF with screenshots
- 🔐 **Auto Login** — AI detects and fills login forms on any site
- 🌐 **Universal AI Support** — Anthropic, OpenAI, Gemini, Groq, or Ollama
- ⚡ **Two Test Modes** — Basic (no AI tokens) or AI (full analysis)

---

## ⚡ Two Test Modes

BugHunter AI gives you full control over when AI is used.
You don't need an API key to run basic tests.

### 🔵 Basic Mode — Zero AI tokens used

```bash
python main.py --url https://example.com --mode basic
```

Runs everything that doesn't require AI:
- Crawls all pages
- Detects UI components (buttons, forms, tables, dropdowns, etc.)
- Runs 3 generic tests per page (page load, links, title)
- Checks accessibility (WCAG 2.1)
- Checks security (headers, cookies, CSRF, SSL, exposed files)
- Generates HTML/PDF report

✅ No API key needed. Fast. Free. Great for daily checks.

---

### 🟣 AI Mode — Full AI-powered analysis

```bash
python main.py --url https://example.com --mode ai
```

Everything in Basic Mode, plus:
- AI understands the purpose of every page
- AI generates exhaustive test cases (functional, security, accessibility, negative)
- AI explains every bug with root cause, severity, and fix suggestion
- AI writes a professional executive summary with deployment recommendation

⚠️ Requires an API key from your chosen AI provider. Uses API tokens per page.

---

### Mode Comparison

| Feature | Basic Mode | AI Mode |
|---|---|---|
| Crawler | ✅ | ✅ |
| UI Detection | ✅ | ✅ |
| Generic Tests (3/page) | ✅ | ✅ |
| Accessibility Checks | ✅ | ✅ |
| Security Checks | ✅ | ✅ |
| HTML / PDF Report | ✅ | ✅ |
| AI Page Understanding | ❌ | ✅ |
| AI Test Case Generation | ❌ | ✅ |
| AI Bug Explanation | ❌ | ✅ |
| AI Executive Summary | ❌ | ✅ |
| API Key Required | ❌ No | ✅ Yes |
| API Tokens Used | **0** | Yes |

---

## 🤖 Supported AI Providers

Only needed for `--mode ai`. You only need **one**.

| Provider | Models | Free Tier | Get Key |
|---|---|---|---|
| **Anthropic** | Claude Sonnet, Opus, Haiku | ❌ Paid | [console.anthropic.com](https://console.anthropic.com) |
| **OpenAI** | GPT-4o, GPT-4 Turbo | ❌ Paid | [platform.openai.com](https://platform.openai.com/api-keys) |
| **Google Gemini** | Gemini 1.5 Pro, Flash | ✅ Free tier | [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| **Groq** | openai/gpt-oss-120b, etc. | ✅ Free tier | [console.groq.com](https://console.groq.com) |
| **Ollama** | Any local model (Llama3, Mistral…) | ✅ Completely free | [ollama.com](https://ollama.com) |

> **Note:** Always check your provider's docs for the latest supported model names,
> as models are occasionally deprecated and replaced.

---

## 🚀 Quick Start

### 1. Clone

```bash
git clone https://github.com/GeetPrajapati12/bughunter-ai.git
cd bughunter-ai
```

### 2. Create virtual environment

```bash
python -m venv .venv

# Mac / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Then install **only** the package for your chosen AI provider (only needed for `--mode ai`):

```bash
# Anthropic (already in requirements.txt)
pip install anthropic

# OpenAI
pip install openai

# Google Gemini
pip install google-generativeai

# Groq
pip install groq

# Ollama — no pip needed, download from https://ollama.com
```

### 4. Configure

```bash
cp .env.example .env
```

For **Basic Mode**, no API key is needed — just run.

For **AI Mode**, open `.env` and set your provider and key:

```bash
AI_PROVIDER=groq
AI_MODEL=openai/gpt-oss-120b
GROQ_API_KEY=gsk_your_key_here
```

### 5. Run

```bash
# Basic mode (no API key needed)
python main.py --url https://example.com --mode basic

# AI mode (requires API key)
python main.py --url https://example.com --mode ai
```

The report is saved to the `reports/` folder.

---

## 📖 Full Usage

```bash
python main.py --url <URL> [options]
```

| Option | Default | Description |
|---|---|---|
| `--url` | required | Target website URL |
| `--mode` | `basic` | `basic` (no AI) or `ai` (full AI analysis) |
| `--username` | — | Login username (optional) |
| `--password` | — | Login password (optional) |
| `--login-url` | — | Login page if different from `--url` |
| `--engine` | `selenium` | `selenium` or `playwright` |
| `--report` | `html` | `html`, `pdf`, or `both` |
| `--max-pages` | `50` | Maximum pages to crawl |
| `--max-depth` | `3` | Maximum crawl depth |
| `--headless` / `--no-headless` | headless | Show/hide browser window |
| `--no-accessibility` | — | Skip WCAG checks |
| `--no-security` | — | Skip security checks |

### Examples

```bash
# Basic test — no API key needed
python main.py --url https://example.com

# Basic test with login
python main.py --url https://app.example.com \
               --username admin@example.com \
               --password yourpassword \
               --mode basic

# Full AI test with login and PDF report
python main.py --url https://app.example.com \
               --username admin@example.com \
               --password yourpassword \
               --mode ai \
               --report both

# Fast smoke test — 5 pages, no AI
python main.py --url https://example.com \
               --max-pages 5 --max-depth 1 \
               --mode basic

# Deep full-site AI test
python main.py --url https://example.com \
               --max-pages 200 --max-depth 6 \
               --mode ai \
               --report both

# Use Playwright instead of Selenium
python main.py --url https://example.com \
               --engine playwright \
               --mode basic
```

---

## ⚙️ Provider Setup Examples (AI Mode only)

### Anthropic (Claude)
```bash
AI_PROVIDER=anthropic
AI_MODEL=claude-sonnet-4-6
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### OpenAI (GPT-4o)
```bash
AI_PROVIDER=openai
AI_MODEL=gpt-4o
OPENAI_API_KEY=sk-your-key-here
```

### Google Gemini
```bash
AI_PROVIDER=gemini
AI_MODEL=gemini-1.5-pro
GEMINI_API_KEY=AIza-your-key-here
```

### Groq (Free)
```bash
AI_PROVIDER=groq
AI_MODEL=openai/gpt-oss-120b
GROQ_API_KEY=gsk_your-key-here
```

### Ollama (Free, Local, No Key)
```bash
AI_PROVIDER=ollama
AI_MODEL=llama3
OLLAMA_BASE_URL=http://localhost:11434
```
> Make sure Ollama is running: `ollama serve`
> Pull a model first: `ollama pull llama3`

---

## 🏗️ Architecture

```
User URL
  │
  ▼
Master Agent
  │
  ├── Crawler                discovers all pages (BFS)
  ├── UI Detection Engine    finds buttons, forms, tables, dropdowns, etc.
  ├── Accessibility Checker  WCAG 2.1 checks (always runs)
  ├── Security Scanner       headers, CSRF, SSL, exposure (always runs)
  │
  ├── [Basic Mode only]
  │     └── Generic Test Runner   3 tests per page, no AI
  │
  └── [AI Mode only]
        ├── LLM Client        universal AI layer (any provider)
        ├── Page Understanding AI interprets each page
        ├── Test Case Generator AI writes exhaustive test cases
        ├── Bug Explainer       AI analyses every failure
        ├── Report Writer       AI writes executive summary
        └── Selenium / Playwright Runner  executes AI-generated tests
```

---

## 📁 Project Structure

```
bughunter-ai/
│
├── config/
│   ├── settings.py        all configuration (reads .env)
│   ├── browser.py         browser factory (Selenium / Playwright)
│   └── prompts.py         all AI prompt templates
│
├── crawler/
│   ├── crawler.py         BFS web crawler
│   ├── sitemap.py         PageInfo + SiteMap data classes
│   └── navigation.py      engine-agnostic browser helpers
│
├── detector/              UI component detectors
│   ├── __init__.py        UIDetectionEngine (orchestrator)
│   ├── buttons.py
│   ├── forms.py
│   ├── tables.py
│   ├── dropdowns.py
│   ├── searchbox.py
│   ├── pagination.py
│   ├── uploads.py
│   ├── charts.py
│   └── calendar.py
│
├── ai/                    AI agents
│   ├── llm_client.py      universal AI provider client
│   ├── master_agent.py    master orchestrator (basic + ai mode)
│   ├── page_understanding.py
│   ├── testcase_generator.py
│   ├── bug_explainer.py
│   └── report_writer.py
│
├── executor/
│   ├── selenium_runner.py
│   └── playwright_runner.py
│
├── modules/
│   ├── login.py           AI-powered login handler
│   ├── accessibility.py   WCAG 2.1 checks
│   ├── security.py        security testing module
│   └── responsiveness.py  multi-viewport checks
│
├── reporter/
│   ├── html_report.py     self-contained HTML report
│   ├── pdf_report.py      PDF via WeasyPrint
│   └── screenshots.py     screenshot manager
│
├── tests/                 unit tests (no browser or API key needed)
│   ├── test_detectors.py
│   └── test_accessibility.py
│
├── reports/               generated reports (git-ignored)
├── screenshots/           failure screenshots (git-ignored)
├── logs/                  run logs (git-ignored)
├── .env.example           configuration template — copy to .env
├── .gitignore
├── requirements.txt
└── main.py                CLI entry point
```

---

## ⚙️ Full Configuration

Copy `.env.example` to `.env` and edit:

```bash
# ── AI Provider (only needed for --mode ai) ───────────────────────────────────
AI_PROVIDER=groq                  # anthropic | openai | gemini | groq | ollama
AI_MODEL=openai/gpt-oss-120b
AI_MAX_TOKENS=4096
AI_TEMPERATURE=0.2

# ── API Keys (only fill in the one you use) ───────────────────────────────────
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GEMINI_API_KEY=
GROQ_API_KEY=
OLLAMA_BASE_URL=http://localhost:11434

# ── Browser ───────────────────────────────────────────────────────────────────
BROWSER_ENGINE=selenium           # selenium | playwright
BROWSER_HEADLESS=true
PAGE_LOAD_TIMEOUT=30

# ── Crawler ───────────────────────────────────────────────────────────────────
MAX_PAGES=50
MAX_DEPTH=3
CRAWL_DELAY_SECONDS=1.0

# ── Reporting ─────────────────────────────────────────────────────────────────
REPORT_FORMAT=html                # html | pdf | both
SCREENSHOT_ON_FAIL=true

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL=INFO
```

---

## 🧪 Run Unit Tests

No browser or API key needed:

```bash
pip install pytest
pytest tests/ -v
```

---

## 🗺️ Roadmap

| Phase | Status | Features |
|---|---|---|
| 1 | ✅ Done | Crawler, UI detector, Selenium runner, HTML report |
| 2 | ✅ Done | AI page understanding, AI test generation, failure analysis |
| 3 | ✅ Done | Multi-agent orchestration, accessibility, PDF reports, login |
| 4 | ✅ Done | Universal AI provider support (Anthropic, OpenAI, Gemini, Groq, Ollama) |
| 5 | ✅ Done | Security testing module (headers, CSRF, SSL, injection signals) |
| 6 | ✅ Done | Basic vs AI mode — run without API tokens |
| 7 | 🔜 Planned | API testing (Swagger/OpenAPI), visual regression, CI/CD |
| 8 | 🔜 Planned | Self-healing locators, parallel execution, trend dashboards |

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit: `git commit -m "Add your feature"`
4. Push: `git push origin feature/your-feature`
5. Open a Pull Request

Please make sure:
- New detectors go in `detector/` and are registered in `detector/__init__.py`
- New AI prompts go in `config/prompts.py`
- New AI provider support goes in `ai/llm_client.py`
- Unit tests go in `tests/`
- No API keys, `.env`, reports, or screenshots are committed

---

## 📄 License

MIT — free to use, modify, and distribute. See [LICENSE](LICENSE).

---

## ⚠️ Disclaimer

This tool performs automated interactions with websites. Always ensure you have
permission to test the target website. Do not run against sites you don't own
or have explicit written permission to test.
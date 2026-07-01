<p align="center">
  <h1 align="center">🐛 BugHunter AI</h1>
  <p align="center">Universal AI-Powered Web Testing Agent</p>
  <p align="center">
    <img src="https://img.shields.io/badge/python-3.10+-blue?style=flat-square&logo=python" />
    <img src="https://img.shields.io/badge/AI-Claude%20(Anthropic)-blueviolet?style=flat-square" />
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
> **No hardcoding. No page-specific code. Works on any website.**

---

## ✨ Features

- 🔍 **Universal Crawler** — BFS crawls any website up to configurable depth and page count
- 🧠 **AI Page Understanding** — Claude analyses each page's purpose, components, and risk areas
- 📋 **AI Test Generation** — generates functional, security, and accessibility test cases per page
- 🤖 **Generic Test Execution** — Selenium or Playwright runner, zero hardcoded selectors
- 🐛 **AI Bug Analysis** — explains failures with root cause, severity, and suggested fix
- ♿ **Accessibility Checks** — WCAG 2.1 violations (missing alt, labels, heading order, etc.)
- 📊 **Professional Reports** — self-contained HTML report + optional PDF with screenshots
- 🔐 **Auto Login** — AI detects and fills login forms on any site
- 📱 **Responsive Testing** — checks layout across 6 common viewport sizes

---

## 🚀 Quick Start

### 1. Clone

```bash
git clone https://github.com/your-username/bughunter-ai.git
cd bughunter-ai
```

### 2. Install dependencies

```bash
python -m venv .venv

# Mac / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Add your API key

```bash
cp .env.example .env
```

Open `.env` and set your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx
```

> **Get a free key at:** https://console.anthropic.com
> The free tier is enough to test small sites.

### 4. Run

```bash
python main.py --url https://example.com
```

The report is saved to the `reports/` folder.

---

## 🔑 API Key — Important Notes

- BugHunter AI uses the **Anthropic Claude API** for all AI features.
- You **must supply your own API key** — no key is bundled with this project.
- Your key is stored in your local `.env` file, which is in `.gitignore` and **will never be committed to git**.
- Without a key the tool still runs but falls back to generic (non-AI) test cases and basic bug descriptions.
- Typical cost for a 50-page site: **~$0.10–$0.50** depending on page complexity.

---

## 📖 Usage

```bash
python main.py --url <URL> [options]
```

| Option | Default | Description |
|---|---|---|
| `--url` | required | Target website URL |
| `--username` | — | Login username (optional) |
| `--password` | — | Login password (optional) |
| `--login-url` | — | Login page if different from `--url` |
| `--engine` | `selenium` | `selenium` or `playwright` |
| `--report` | `html` | `html`, `pdf`, or `both` |
| `--max-pages` | `50` | Maximum pages to crawl |
| `--max-depth` | `3` | Maximum crawl depth |
| `--headless` / `--no-headless` | headless | Show/hide browser window |
| `--no-accessibility` | — | Skip WCAG checks |

### Examples

```bash
# Basic test
python main.py --url https://example.com

# With login
python main.py --url https://app.example.com \
               --username admin@example.com \
               --password yourpassword

# Full site, both report formats
python main.py --url https://example.com \
               --max-pages 200 --max-depth 6 \
               --report both

# Fast smoke test (5 pages)
python main.py --url https://example.com \
               --max-pages 5 --max-depth 1

# Use Playwright instead of Selenium
python main.py --url https://example.com --engine playwright
```

---

## 🏗️ Architecture

```
User URL
  │
  ▼
Master Agent
  │
  ├── Crawler              discovers all pages (BFS)
  ├── UI Detection Engine  finds buttons, forms, tables, dropdowns, etc.
  ├── Page Understanding   Claude AI interprets each page
  ├── Test Case Generator  Claude AI writes exhaustive test cases
  ├── Selenium / Playwright Runner  executes tests generically
  ├── Bug Explainer        Claude AI analyses every failure
  ├── Report Writer        Claude AI writes executive summary
  └── HTML / PDF Reporter  renders the final report
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
│   ├── master_agent.py    master orchestrator
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

## ⚙️ Configuration

Copy `.env.example` to `.env` and edit:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-your-key-here

# AI model
AI_MODEL=claude-sonnet-4-6

# Browser
BROWSER_ENGINE=selenium        # or playwright
BROWSER_HEADLESS=true
PAGE_LOAD_TIMEOUT=30

# Crawler
MAX_PAGES=50
MAX_DEPTH=3
CRAWL_DELAY_SECONDS=1.0

# Reporting
REPORT_FORMAT=html             # html | pdf | both
SCREENSHOT_ON_FAIL=true

# Logging
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
| 4 | 🔜 Planned | API testing (Swagger/OpenAPI), visual regression, CI/CD |
| 5 | 🔜 Planned | Self-healing locators, parallel execution, trend dashboards |

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

# Contributing to BugHunter AI

Thank you for your interest in contributing! This document explains how to get
started and what we expect from contributors.

---

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/your-username/bughunter-ai.git
   cd bughunter-ai
   ```
3. **Set up** your environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env        # add your own ANTHROPIC_API_KEY
   ```
4. **Run the tests** to make sure everything is working:
   ```bash
   pytest tests/ -v
   ```

---

## What to Work On

Check the [Issues](../../issues) tab for open bugs and feature requests.
The roadmap in `README.md` lists planned features for Phases 4 and 5.

Good first contributions:
- Add a new UI detector (e.g. `detector/modals.py`, `detector/tooltips.py`)
- Improve an existing prompt in `config/prompts.py`
- Add more unit tests in `tests/`
- Improve the HTML report design in `reporter/html_report.py`
- Add a new generic test module in `modules/`

---

## Code Guidelines

- **One responsibility per module** — follow the existing pattern
- **No hardcoded selectors or site-specific logic** — everything must work generically on any website
- **Type hints** on all function signatures
- **Docstrings** on all classes and public methods
- **New AI prompts** go in `config/prompts.py` only — never inline in agent files
- **New detectors** must be registered in `detector/__init__.py`
- **Log with loguru** — `from loguru import logger` — not `print()`

---

## Pull Request Checklist

Before opening a PR, make sure:

- [ ] `pytest tests/ -v` passes with no failures
- [ ] All Python files pass `python -m py_compile <file>.py`
- [ ] No `.env` file, API keys, report files, screenshots, or logs are committed
- [ ] New detector modules are registered in `detector/__init__.py`
- [ ] New prompts are in `config/prompts.py`
- [ ] PR description explains what changed and why

---

## What NOT to Commit

The `.gitignore` handles most of this, but as a reminder — never commit:

- `.env` (your real API key)
- `reports/` folder contents
- `screenshots/` folder contents
- `logs/` folder contents
- `cache/` folder contents
- Any `__pycache__` directories

---

## Questions?

Open a [GitHub Discussion](../../discussions) or file an [Issue](../../issues).

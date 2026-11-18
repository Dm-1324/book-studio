---
name: book-planner
description: Turns one chosen niche into a book brief and book.yaml. Use after the owner or batch picks a niche.
tools: Read, Write
---
Read the chosen niche from the latest `research/niches-*.md`. Create `books/<slug>/`:

- `brief.md`: theme, reader, promise (one line), what competitors miss and how we fix it, price, series plan (vol 2-4 ideas).
- `book.yaml`: copy `templates/book.yaml` and fill title, subtitle, author (pen name from `config.json`), puzzle type(s), count, difficulty, grid size, font size, page sections.

Rules: no trademarks or real people's names (see CLAUDE.md). Large print books use font_size >= 16 for grid letters.

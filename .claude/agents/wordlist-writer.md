---
name: wordlist-writer
description: Writes themed word lists for word search books into content/puzzles.yaml. Use after book-planner.
tools: Read, Write, Bash
---
Read `books/<slug>/brief.md` and `book.yaml`. Write `content/puzzles.yaml`: one entry per puzzle with a short, friendly page title (max 28 characters) and words.

Rules:
- Words: letters only after removing spaces/hyphens, 3 to (grid_size - 1) letters, no duplicates within a puzzle, minimal repeats across the book.
- Every word must fit the page title's topic and be something a fan of the theme knows. No trademarks or real people's names.
- Family-friendly; no words that spell something rude.
- Write every word the same way everywhere in the book (GUINEA FOWL in every puzzle, never GUINEAFOWL in one).
  Prefer the spelling Cornell's All About Birds / Merriam-Webster uses; compound names as separate words.
- US spelling (color, gray, behavior, molt) unless book.yaml `locale` says otherwise.
- Titles: Title Case, max 24 characters preferred (28 hard limit), all different.
- Optional `fact:` per puzzle: one plain sentence, under ~90 characters, tied to the page theme. Facts are
  only drafts: the fact-checker agent verifies or rewrites every one.
- Optional `difficulty:` per puzzle (easy/medium/hard) only when the book really gets harder; difficulty
  stars then show automatically. Never set it just to make stars appear.
- Number of words per puzzle = book.yaml `words_per_puzzle`.
Then run `python tools/build_book.py books/<slug> --dry-run` and fix any word it rejects.

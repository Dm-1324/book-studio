# Book Studio

Makes books for Amazon KDP, one folder per book under `books/<slug>/`.
Track 1 (now): themed puzzle books (word search, sudoku, mazes), paperback.
Track 2 (later): niche non-fiction. Track 3 (later): genre fiction via Book Genesis.

## Hard rules (protect the KDP account above everything)

1. **Never upload to KDP, never automate the KDP website.** The owner uploads by hand.
2. **Weekly limit: 2 new titles per format per week** (resets Sunday 00:00 UTC = 05:30 IST).
   The weekly batch produces at most 2 READY books. Drafts count, so never create KDP drafts.
3. **AI disclosure: when in doubt, disclose.** Every `listing.md` states exactly which parts
   are AI-generated (text / images / translation) so the owner ticks the right boxes.
   Puzzle grids made by ordinary code are not AI-generated, but word lists, titles or any
   text written by an AI agent ARE AI-generated text. Any AI cover art = AI-generated image.
4. **No trademarks or real people's names** in titles, subtitles, keywords or covers
   (league names like IPL, team names, famous players, brands, Disney, etc.).
5. **Every book must be distinct and useful.** No near-duplicate books. A new volume
   needs new puzzles and a new word set.
6. **No review manipulation** of any kind in listings, back pages or marketing.

## Pipeline for one book

| Step | Who | Reads | Writes |
|---|---|---|---|
| 1 Niche | `niche-scout` agent | `research/seeds.md` | `research/niches-<date>.md` (scored) |
| 2 Plan | `book-planner` agent | chosen niche | `books/<slug>/brief.md`, `book.yaml` |
| 3 Content | `wordlist-writer` agent + `tools/build_book.py` | brief, book.yaml | `content/puzzles.yaml`, `dist/interior.pdf` |
| 4 Cover | `cover-artist` agent + Fooocus + `tools/build_cover.py` | brief, interior page count | `assets/cover-art.png`, `dist/cover.pdf` |
| 5 Check | `tools/check_book.py` then `book-checker` agent (views pages) | dist/ | `QA.md` |
| 6 Listing | `listing-writer` agent | brief, research | `listing.md` |
| 7 Ready | batch | QA pass | empty file `READY` (or `REJECTED.md` with reasons) |

Each step only reads files the previous step wrote. A failed check sends the book
back to the step that broke, at most 2 retries, then `REJECTED.md`.

## Commands

```
python tools/build_book.py books/<slug>          # puzzles + interior.pdf + answer keys
python tools/build_cover.py books/<slug>         # wrap cover sized from the interior's page count
python tools/check_book.py books/<slug>          # automatic KDP checks -> QA.md (auto part)
python tools/render_pages.py books/<slug> 1,5,30 # PNGs of pages for the book-checker to look at
```

## KDP print facts used by the tools (paperback, black & white, white paper)

- Trim 8.5 x 11 in, no bleed. Inside (gutter) margin >= 0.375 in for 24-150 pages,
  >= 0.5 in for 151-300 pages; outside margins >= 0.25 in. We use 0.75 in / 0.6 in.
- Minimum 24 pages. Page count is even.
- Spine width = pages x 0.002252 in. Cover = 0.125 bleed + back + spine + front + 0.125 bleed,
  height 11.25 in. Spine text only when the book has 79+ pages.
- All fonts embedded (the tools only use the TTFs in `assets/fonts`, all SIL OFL).

## Interior design

`tools/design.py` ("framed" style, the default): page frame, header band with puzzle-number badge and a theme
icon, word-list panel, leafy footer with page number, worked example on the how-to page.
Set per book in `book.yaml` -> `design: {style, icon, badge}`; per puzzle `icon:` in `content/puzzles.yaml`.
Icons: our own `bird`, `sprig`, or any Material Icons name (Apache 2.0). Never brand/mascot icons (see BANNED).
Colour: `ink: standard_color` uses the `design.palette` colours (each puzzle page takes the next colour).
Standard colour needs 72+ pages (check_book.py enforces it), so colour books have about 60+ puzzles and are
priced around $12.99. `ink: bw` turns the same design into greys.
Repeat-purchase pages: `tracker` (colour-in progress circles), "Collect the whole series" cards,
`certificate`, `bonus_url` (QR code page for the free-puzzles email list).
`fact:` lines ("Did you know?") are AI text: every fact must be checked true before the book is READY.

## Pinterest

`python tools/make_pins.py books/<slug>` -> 10 pins (1000x1500) in dist/pins + pins.json: 1 cover, 1 look-inside,
4 "can you find these 5 words?" mini puzzles (fresh grids, never book answers), 4 bird-fact pins with the cover.
`python tools/post_pins.py` (daily) tops the Buffer Pinterest queue up to 8 (free plan cap is 10), 2 pins a day,
round-robin across live books. A book is live only when book.yaml `amazon_url` is set.

## Writing style for anything a buyer reads

Plain, warm, short sentences. Large print books: never below 14 pt for words to find.

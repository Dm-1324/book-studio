# QA

## Automatic checks

| Result | Check | Detail |
|---|---|---|
| PASS | Page count even and >= 72 (standard_color) | 82 pages |
| PASS | Page count matches build.json |  |
| PASS | Every page is the trim size | 8.5 x 11 in |
| PASS | All fonts embedded |  |
| PASS | Every wordsearch puzzle solvable exactly one way |  |
| PASS | Puzzle count matches book.yaml | 60 puzzles |
| PASS | Cover size matches page count | 17.435 x 11.250 in (spine 0.185 in) |
| PASS | Royalty is positive | $12.99 x 60% - $4.30 print = $3.50 per copy |
| PASS | Layout: no text overlaps or runs past its box |  |
| PASS | Word lists: each word written the same way everywhere |  |
| PASS | Word lists: clean words and titles (letters only, titles <= 28 chars) |  |
| PASS | Puzzle titles are all different |  |
| PASS | Puzzles are distinct (no two share 5+ words) |  |
| PASS | No word used in more than 3 puzzles |  |
| WARN | Facts: no fact repeats another (book-checker decides) | 1&10 (eat/food), 3&54 (falcon/peregrine), 5&44 (feather/oil), 10&32 (color/get), 18&46 (find/way), 37&43 (build/nest) |
| PASS | Same grid size on every puzzle page | sizes [27.3] |
| PASS | Cover: tagline doesn't repeat the subtitle |  |
| PASS | Spelling: US English throughout (book is for Amazon.com) |  |
| PASS | Vocabulary: no UK-only names outside region pages |  |
| PASS | No placeholder or TODO text left |  |
| PASS | Listing: puzzle count matches the book | listing says [60], book has 60 |
| PASS | Listing: AI disclosure filled in |  |
| PASS | Listing: pen name matches book.yaml |  |
| PASS | Facts: all 60 verified with a source (FACTS.md) |  |

**PASS** (24/24 passed)

Print cost uses Amazon.com rates for this ink; confirm in KDP's pricing calculator before publishing.

## Visual check

**PASS** (2026-11-20, book-checker re-run on commit ef05476). check_book.py 23/23 PASS + 1 WARN. All 82 interior pages and the cover were re-rendered (PNGs dated 13:44, newer than interior.pdf and cover.pdf) and every page image was viewed, in order, no sampling.

- Collisions: none. No word-list text touches a checkbox, column, icon or frame; long entries (BURROWING OWL, COCK OF THE ROCK, OYSTERCATCHER, MURMURATION, GREAT GRAY OWL) fit. Header titles do not crowd the icons (longest: "Birds of North America", "Giants of the Bird World").
- Grids: all 60 puzzle pages show the same 13x13 grid at the same size; word lists are 14-15 words on 3-4 columns.
- Consistency: US spelling throughout (Colorful, Behavior, OCHER, Gray, Shoveler). Two-part names are written the same way everywhere (GUINEA FOWL, BEE EATER, BLUE JAY). Title case is consistent, no punctuation in titles. Colors cycle teal/coral/green/amber/purple with no repeats in a row. Page numbers run 5-64 without gaps; answers 65-80; series page 81; certificate 82.
- Icons: fit their themes (rainforest = leaf, night = moon, sea/pond = waves, desert = sun, winter = snowflake, migration = plane, nests/eggs = egg). Several pages use the generic bird icon (1, 2, 10, 17, 18, 28, 31, 42, 44, 56), acceptable.
- Difficulty stars: none shown, nothing stuck at a default.
- Answers: grid numbers match their puzzles (spot-compared first rows of 1, 17, etc. against the puzzle pages; every circled word is a real list word, all list words are circled).
- Front/back matter: tracker has 60 circles = 60 puzzles; series cards correct (this book ticked-in list, 2 coming soon); certificate title on two clean lines; no placeholders.
- Cover: title/subtitle spelled right, tagline "60 PUZZLES - ANSWERS INCLUDED" is no longer a repeat, readable at 160 px (thumb), nothing trademarked, nothing near the trim, no spine text (0.185 in spine).
- Facts WARN (1&10, 3&54, 5&44, 10&32, 18&46, 37&43): all six are shared-keyword matches, NOT real repeats. 1 = chickadees cache food, 10 = flamingo color comes from diet; 3 = peregrine dive speed, 54 = peregrines nest on city buildings; 5 = preen-oil waterproofing, 44 = dust baths remove excess oil; 10 = flamingo color, 32 = structural blue; 18 = homing pigeons, 46 = star navigation by night migrants; 37 = weaver hanging nests, 43 = swiftlet saliva nests. Different facts, accepted.

### Non-blocking notes (owner may fix, not a reject)
- cover: the decorative puzzle grid circles diagonal words (an X shape), but the book promises "no diagonals, no backwards words" -> tools/build_cover.py cover grid art: circle only horizontal/vertical words.
- page 34 (puzzle 30): BIRD TABLE is a UK term (US: platform feeder) -> content/puzzles.yaml puzzle 30.
- page 19 (puzzle 15): POCHARD and MANDARIN are rare/ornamental in the US -> content/puzzles.yaml puzzle 15 (optional).
- pages 2, 7, 23, 51: the font draws zero with a slash/dot ("2026", "100", "50", "1900"); consistent, but check it looks intended in the print proof.

Add an automatic check for: cover art words must only run left-to-right or top-to-bottom when the book promises no diagonals/backwards words.

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
| PASS | Spelling: US English throughout (book is for Amazon.com) |  |
| PASS | No placeholder or TODO text left |  |
| PASS | Listing: puzzle count matches the book | listing says [60], book has 60 |
| PASS | Listing: AI disclosure filled in |  |
| PASS | Listing: pen name matches book.yaml |  |
| PASS | Facts: all 60 verified with a source (FACTS.md) |  |

**PASS** (18/18 passed)

Print cost uses Amazon.com rates for this ink; confirm in KDP's pricing calculator before publishing.

## Visual check

**FAIL** (book-checker; all 82 interior pages, the cover and the 160 px thumbnail were looked at individually; check_book.py was 18/18 PASS)

No text collisions, cut-off text, wrong answer numbers, tracker/series-card/certificate or placeholder problems were found. Answer grids match their puzzles and the circled words are real list words. The rejection is for content and consistency problems:

1. page 5-6, 28-29, 43-44, 60-61 (puzzles 1, 2, 24, 25, 40, 56, 57; also 3, 52, 53, 51): UK-only bird names in a book sold on Amazon.com as "Backyard Birds" for US readers: BLUE TIT, DUNNOCK, BLACKCAP, LINNET, CHAFFINCH, GREENFINCH, SISKIN, BRAMBLING, FIELDFARE, REDWING, YELLOWHAMMER, HAWFINCH, REED BUNTING, HOUSE MARTIN, SAND MARTIN, TAWNY OWL, TREECREEPER, WOODCOCK, PARTRIDGE, PIPIT, HEDGEROW, MOORHEN, HOBBY. Puzzle 1 (the first page a buyer sees) has BLUE TIT, and the how-to page explains BLUETIT. Puzzles 2 and 56 are almost entirely UK finches. -> content/puzzles.yaml puzzles 1, 2, 3, 24, 25, 51, 52, 53, 56, 57 (swap for US birds: Blue Jay, Titmouse, Goldfinch, Purple Finch, House Finch, Pine Siskin, Bunting, Purple Martin, Barn Swallow, Bobwhite, Meadowlark ...)
2. page 16 (puzzle 12) and page 38 (puzzle 34): two near-identical puzzles, 6 of 14 words shared (CURLEW, DUNLIN, OYSTERCATCHER, PLOVER, SANDPIPER, WAVES), same icon. -> content/puzzles.yaml puzzle 12 or 34 (rework one).
3. page 9 (puzzle 5) and page 55 (puzzle 51): 6 of 14 words shared (COOT, GREBE, HERON, KINGFISHER, LOON, MOORHEN), same icon. -> content/puzzles.yaml puzzle 5 or 51.
4. page 8 (puzzle 4) and page 37 (puzzle 33): "Owls at Night" and "Birds of the Night" overlap (BARN OWL, DUSK, SILENT, same moon icon). Also 24 vs 55 (JUNCO, REDPOLL, SNOW BUNTING, FROST) and 11/24/25/55 all seasonal. -> content/puzzles.yaml puzzle 33 (and 55).
5. page 11, 51, 64 (puzzles 7, 47, 60): the dawn chorus fact is repeated three times in different words (plus page 29, spring singing); "waterproof" facts on pages 9 and 48. -> content/puzzles.yaml facts for puzzles 47, 60, 44.
6. page 36 (puzzle 32): OCHRE is the UK spelling (US: ocher). -> content/puzzles.yaml puzzle 32.
7. page 37 (puzzle 33), page 54 (puzzle 50), page 60 (puzzle 56): the word list is 3 columns x 5 rows, so the grid is drawn about 5% smaller than on all other puzzle pages (an "extra large print" book should keep one grid size). -> tools/design.py word list layout / grid sizing when the list is long.
8. page 25 (puzzle 21 Rainforest Birds), page 17, 56: pine-tree icon used for a rainforest page. Page 16/27 egg and drop icons look alike. -> tools/design.py icon map / book.yaml icon choice for puzzle 21.
9. page 82: certificate wraps the book title as "Backyard / Birds Word Search for Seniors" (breaks the title mid-name). -> tools/design.py certificate text box (balance the line or use a non-breaking space).
10. cover: "NO BACKWARDS WORDS" appears twice (subtitle and the amber tagline under it). Cover is otherwise readable at 160 px, nothing near the trim, no spine text. -> tools/build_cover.py tagline.

Add an automatic check for:
- Cross-puzzle overlap: flag any two puzzles sharing 5 or more words, and any word used in more than 3 puzzles.
- US vs UK vocabulary: a word list of UK-only bird names (BLUE TIT, DUNNOCK, CHAFFINCH, GREENFINCH, LINNET, YELLOWHAMMER, ...) and OCHRE/GREY/COLOUR spellings when the market is Amazon.com.
- Repeated or near-duplicate "Did you know" facts (same key words, e.g. "dawn chorus").
- Grid cell size equal on all puzzle pages (layout.json), and the same icon not used on pages that are thematically different.

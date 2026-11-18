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

**PASS** (8/8 passed)

Print cost uses Amazon.com rates for this ink; confirm in KDP's pricing calculator before publishing.
## Visual check (full edition, 60 puzzles)

Pages viewed: 1, 3, 4 (tracker, 60 circles), 6, 10, 36 (two-line fact), 45, 54 (long words), 57, 77 (answers), 82, cover.
- PASS: every page framed, colours cycle, facts readable, answers match puzzle numbers.
- FIXED: spine text removed (0.185 in spine is too thin for KDP's 0.0625 in clearance); "Colour" -> "Color" for the US.
- Facts: 60 widely documented bird facts, checked by Claude from general knowledge (no web check). Run the fact-checker agent on dm-1324 before upload.

**PASS**

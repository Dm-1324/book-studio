# QA

## Automatic checks

| Result | Check | Detail |
|---|---|---|
| PASS | Page count even and >= 24 (bw) | 32 pages |
| PASS | Page count matches build.json |  |
| PASS | Every page is the trim size | 8.5 x 11 in |
| PASS | All fonts embedded |  |
| PASS | Every wordsearch puzzle solvable exactly one way |  |
| PASS | Puzzle count matches book.yaml | 20 puzzles |
| PASS | Cover size matches page count | 17.322 x 11.250 in (spine 0.072 in) |
| PASS | Royalty is positive | $9.99 x 60% - $2.84 print = $3.15 per copy |
| PASS | Layout: no text overlaps or runs past its box |  |
| PASS | Word lists: each word written the same way everywhere |  |
| PASS | Word lists: clean words and titles (letters only, titles <= 28 chars) |  |
| PASS | Puzzle titles are all different |  |
| FAIL | Spelling: US English throughout (book is for Amazon.com) | honour -> honor |
| PASS | No placeholder or TODO text left |  |
| FAIL | Listing: puzzle count matches the book | listing says [20, 100], book has 20 |
| FAIL | Listing: AI disclosure filled in |  |
| PASS | Listing: pen name matches book.yaml |  |

**FAIL** (14/17 passed)

Print cost uses Amazon.com rates for this ink; confirm in KDP's pricing calculator before publishing.

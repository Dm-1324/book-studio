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
| PASS | Same grid size on every puzzle page | sizes [27.15] |
| PASS | Cover: tagline doesn't repeat the subtitle |  |
| PASS | Spelling: US English throughout (book is for Amazon.com) |  |
| PASS | Vocabulary: no UK-only names outside region pages |  |
| PASS | No doubled words in titles, pins or listing |  |
| PASS | No placeholder or TODO text left |  |
| PASS | Listing: puzzle count matches the book | listing says [60], book has 60 |
| PASS | Listing: AI disclosure filled in |  |
| PASS | Listing: pen name matches book.yaml |  |
| PASS | Facts: all 60 verified with a source (FACTS.md) |  |

**PASS** (25/25 passed)

Print cost uses Amazon.com rates for this ink; confirm in KDP's pricing calculator before publishing.

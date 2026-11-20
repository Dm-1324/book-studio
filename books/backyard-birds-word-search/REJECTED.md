# REJECTED: Backyard Birds Word Search for Seniors

Layout, answers, tracker, series cards, certificate and cover pass visual review. Fix the content below, rebuild, re-run check_book.py and book-checker.

## Page-by-page fixes
- page 5 (puzzle 1): BLUE TIT is a UK bird; replace (e.g. TITMOUSE) and drop the BLUETIT how-to note on page 3 if no two-word names remain -> content/puzzles.yaml puzzle 1, book.yaml how_to_play
- page 6 (puzzle 2): DUNNOCK, BLACKCAP, LINNET, CHAFFINCH, GREENFINCH are UK-only -> content/puzzles.yaml puzzle 2 (US songbirds)
- page 7 (puzzle 3): HOBBY (UK) -> content/puzzles.yaml puzzle 3
- page 9 and page 55 (puzzles 5, 51): 6 shared words (COOT, GREBE, HERON, KINGFISHER, LOON, MOORHEN); rework puzzle 51, replace MOORHEN (US: gallinule) and SAND MARTIN -> content/puzzles.yaml
- page 8 and page 37 (puzzles 4, 33): overlapping night/owl puzzles; rework 33 -> content/puzzles.yaml puzzle 33
- page 11, 51, 64 (puzzles 7, 47, 60): dawn chorus fact repeated; page 48 vs 9 waterproof fact repeated -> content/puzzles.yaml facts 47, 60, 44
- page 16 and page 38 (puzzles 12, 34): 6 shared words; rework one -> content/puzzles.yaml
- page 25 (puzzle 21): pine-tree icon on a rainforest page -> icon choice for puzzle 21
- page 28, 29 (puzzles 24, 25): BRAMBLING, FIELDFARE, REDWING, REDPOLL, SISKIN; 24 vs 55 overlap (JUNCO, REDPOLL, SNOW BUNTING, FROST) -> content/puzzles.yaml
- page 36 (puzzle 32): OCHRE -> OCHER (US) -> content/puzzles.yaml
- page 37, 54, 60 (puzzles 33, 50, 56): grid drawn smaller than other pages because the word list has 5 rows -> tools/design.py word list / grid sizing
- page 56, 57 (puzzles 52, 53): TAWNY OWL, TREECREEPER, WOODCOCK, HEDGEROW, PARTRIDGE, PIPIT are UK-centric -> content/puzzles.yaml
- page 60 (puzzle 56): GREENFINCH, CHAFFINCH, LINNET, YELLOWHAMMER, HAWFINCH, REED BUNTING; mostly UK -> content/puzzles.yaml puzzle 56
- page 61 (puzzle 57): HOUSE MARTIN, SAND MARTIN, FORKED TAIL -> content/puzzles.yaml puzzle 57 (PURPLE MARTIN, BARN SWALLOW, CHIMNEY SWIFT)
- page 82: certificate title wraps mid-name -> tools/design.py certificate text
- cover: "NO BACKWARDS WORDS" shown twice -> tools/build_cover.py tagline

See QA.md "Visual check" for details and suggested automatic checks.

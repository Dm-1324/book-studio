"""Word search generator with a built-in self-check.

make_wordsearch(words, size, directions, rng) -> dict with grid, placements.
Every word is placed exactly once and is findable exactly once in the final grid.
"""
import re
import string

DIRS = {
    "E": (0, 1), "S": (1, 0), "SE": (1, 1), "NE": (-1, 1),
    "W": (0, -1), "N": (-1, 0), "NW": (-1, -1), "SW": (1, -1),
}
DIFFICULTY_DIRS = {
    "easy": ["E", "S"],
    "medium": ["E", "S", "SE", "NE"],
    "hard": list(DIRS),
}
# Fill letters are checked so the random filler never spells these by accident.
BLOCKLIST = {"FUCK", "SHIT", "CUNT", "DICK", "COCK", "PISS", "TWAT", "SLUT", "WHORE",
             "FAG", "NAZI", "RAPE", "PORN", "ANAL", "TITS", "BOOB", "ARSE", "DAMN", "HELL", "KILL"}
# Weighted toward common English letters so filler looks natural.
FILL = "EEEEAAAAIIIOOOTTTNNNSSSRRRLLLHHDDCCUUMMPPGGBBFFYWKVXJQZ"


def clean(word):
    w = re.sub(r"[^A-Za-z]", "", word).upper()
    return w


def _lines(grid):
    n = len(grid)
    for r in range(n):
        yield "".join(grid[r])
    for c in range(n):
        yield "".join(grid[r][c] for r in range(n))
    for d in range(-n + 1, n):
        yield "".join(grid[r][r - d] for r in range(n) if 0 <= r - d < n)
        yield "".join(grid[r][n - 1 - r + d] for r in range(n) if 0 <= n - 1 - r + d < n)


def count_occurrences(grid, word):
    total = 0
    for line in _lines(grid):
        for s in (line, line[::-1]):
            total += sum(1 for i in range(len(s) - len(word) + 1) if s[i:i + len(word)] == word)
    if word == word[::-1]:
        total //= 2  # palindromes are counted twice (forward and reversed line)
    return total


def _try_place(grid, word, rng, dirs):
    n = len(grid)
    options = []
    for d in dirs:
        dr, dc = DIRS[d]
        for r in range(n):
            for c in range(n):
                er, ec = r + dr * (len(word) - 1), c + dc * (len(word) - 1)
                if not (0 <= er < n and 0 <= ec < n):
                    continue
                overlap, ok = 0, True
                for i, ch in enumerate(word):
                    g = grid[r + dr * i][c + dc * i]
                    if g is None:
                        continue
                    if g != ch:
                        ok = False
                        break
                    overlap += 1
                if ok and overlap < len(word):
                    options.append((overlap, rng.random(), r, c, d))
    if not options:
        return None
    # Prefer some crossings (looks professional) but keep randomness.
    options.sort(key=lambda o: (-min(o[0], 1), o[1]))
    pick = options[0] if rng.random() < 0.5 else rng.choice(options)
    _, _, r, c, d = pick
    dr, dc = DIRS[d]
    for i, ch in enumerate(word):
        grid[r + dr * i][c + dc * i] = ch
    return {"row": r, "col": c, "dir": d}


def make_wordsearch(words, size, difficulty, rng, attempts=200):
    dirs = DIFFICULTY_DIRS[difficulty]
    cleaned = [(w, clean(w)) for w in words]
    for w, cw in cleaned:
        if len(cw) < 3 or len(cw) > size:
            raise ValueError(f"word '{w}' does not fit a {size}x{size} grid")
    if len({cw for _, cw in cleaned}) != len(cleaned):
        raise ValueError("duplicate words in puzzle")
    for cw_a in [c for _, c in cleaned]:
        for cw_b in [c for _, c in cleaned]:
            if cw_a != cw_b and (cw_a in cw_b or cw_a in cw_b[::-1]):
                how = "inside" if cw_a in cw_b else "backwards inside"
                raise ValueError(f"'{cw_a}' is {how} '{cw_b}', it would be found twice")
    order = sorted(cleaned, key=lambda x: -len(x[1]))
    for _ in range(attempts):
        grid = [[None] * size for _ in range(size)]
        placements = {}
        for w, cw in order:
            p = _try_place(grid, cw, rng, dirs)
            if p is None:
                break
            placements[w] = {**p, "len": len(cw)}
        else:
            for r in range(size):
                for c in range(size):
                    if grid[r][c] is None:
                        grid[r][c] = rng.choice(FILL)
            if _valid(grid, cleaned):
                return {"grid": grid, "placements": placements, "words": [w for w, _ in cleaned]}
    raise RuntimeError("could not build this word search; use fewer or shorter words")


def _valid(grid, cleaned):
    for _, cw in cleaned:
        if count_occurrences(grid, cw) != 1:
            return False
    for bad in BLOCKLIST:
        if any(bad in cw or bad in cw[::-1] for _, cw in cleaned):
            continue  # e.g. SHELL contains HELL; the theme word itself is fine
        if count_occurrences(grid, bad):
            return False
    return True


if __name__ == "__main__":
    import random
    ws = make_wordsearch(["Wicket", "Bowler", "Umpire", "Boundary", "Spinner", "Stumps"], 12, "hard", random.Random(1))
    for row in ws["grid"]:
        print(" ".join(row))
    print(ws["placements"])

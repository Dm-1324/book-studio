"""Sudoku generator: every puzzle has exactly one solution (checked by a solver)."""

GIVENS = {"easy": 40, "medium": 32, "hard": 27}


def _candidates(g, i):
    r, c = divmod(i, 9)
    used = set(g[r * 9:(r + 1) * 9]) | set(g[c::9])
    br, bc = 3 * (r // 3), 3 * (c // 3)
    for rr in range(br, br + 3):
        used |= set(g[rr * 9 + bc: rr * 9 + bc + 3])
    return [d for d in range(1, 10) if d not in used]


def count_solutions(g, limit=2):
    g = list(g)
    best, best_c = None, None
    for i, v in enumerate(g):
        if v == 0:
            cands = _candidates(g, i)
            if not cands:
                return 0
            if best is None or len(cands) < len(best_c):
                best, best_c = i, cands
                if len(cands) == 1:
                    break
    if best is None:
        return 1
    total = 0
    for d in best_c:
        g[best] = d
        total += count_solutions(g, limit - total)
        if total >= limit:
            break
    return total


def _fill(g, rng):
    try:
        i = g.index(0)
    except ValueError:
        return True
    cands = _candidates(g, i)
    rng.shuffle(cands)
    for d in cands:
        g[i] = d
        if _fill(g, rng):
            return True
    g[i] = 0
    return False


def make_sudoku(difficulty, rng):
    solution = [0] * 81
    _fill(solution, rng)
    puzzle = list(solution)
    target = GIVENS[difficulty]
    cells = list(range(81))
    rng.shuffle(cells)
    for i in cells:
        if sum(1 for v in puzzle if v) <= target:
            break
        j = 80 - i  # remove in symmetric pairs, like published puzzles
        keep = (puzzle[i], puzzle[j])
        puzzle[i] = puzzle[j] = 0
        if count_solutions(puzzle) != 1:
            puzzle[i], puzzle[j] = keep
    assert count_solutions(puzzle) == 1
    return {"puzzle": puzzle, "solution": solution, "givens": sum(1 for v in puzzle if v)}

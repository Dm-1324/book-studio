"""Rectangular maze generator (perfect maze: exactly one path between any two cells)."""
from collections import deque

SIZES = {"easy": (12, 15), "medium": (18, 23), "hard": (25, 32)}  # cols, rows


def make_maze(difficulty, rng):
    cols, rows = SIZES[difficulty]
    # walls[r][c] = set of open sides of cell (r, c): subset of N S E W
    open_ = [[set() for _ in range(cols)] for _ in range(rows)]
    seen = [[False] * cols for _ in range(rows)]
    stack = [(0, 0)]
    seen[0][0] = True
    moves = {"N": (-1, 0, "S"), "S": (1, 0, "N"), "E": (0, 1, "W"), "W": (0, -1, "E")}
    while stack:
        r, c = stack[-1]
        nbrs = [(d, r + dr, c + dc, back) for d, (dr, dc, back) in moves.items()
                if 0 <= r + dr < rows and 0 <= c + dc < cols and not seen[r + dr][c + dc]]
        if not nbrs:
            stack.pop()
            continue
        d, nr, nc, back = rng.choice(nbrs)
        open_[r][c].add(d)
        open_[nr][nc].add(back)
        seen[nr][nc] = True
        stack.append((nr, nc))
    start, end = (0, 0), (rows - 1, cols - 1)
    path = _solve(open_, start, end)
    return {"cols": cols, "rows": rows, "open": [[sorted(s) for s in row] for row in open_],
            "start": start, "end": end, "path": path}


def _solve(open_, start, end):
    moves = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "W": (0, -1)}
    prev = {start: None}
    q = deque([start])
    while q:
        cur = q.popleft()
        if cur == end:
            break
        r, c = cur
        for d in open_[r][c]:
            dr, dc = moves[d]
            nxt = (r + dr, c + dc)
            if nxt not in prev:
                prev[nxt] = cur
                q.append(nxt)
    path, cur = [], end
    while cur is not None:
        path.append(cur)
        cur = prev[cur]
    return path[::-1]

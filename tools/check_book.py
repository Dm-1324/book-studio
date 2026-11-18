"""Automatic KDP checks for a built book. Writes the first part of QA.md.

usage: python tools/check_book.py books/<slug>
Exit code 1 if any check FAILs.
"""
import json
import sys
from pathlib import Path

import yaml
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from puzzles.sudoku import count_solutions  # noqa: E402
from puzzles.wordsearch import clean, count_occurrences  # noqa: E402
from build_cover import PER_PAGE  # noqa: E402

PT = 72.0


MIN_PAGES = {"bw": 24, "standard_color": 72, "premium_color": 24}


def print_cost(pages, trim, ink="bw"):
    """Amazon.com paperback print cost (USD), KDP help page G201834340. Check KDP's calculator before pricing."""
    large = trim[0] > 6.12 or trim[1] > 9
    if ink == "standard_color":
        return 1.00 + pages * (0.0402 if large else 0.0255)
    if ink == "premium_color":
        if pages <= 40:
            return 4.20 if large else 3.60
        return 1.00 + pages * (0.08 if large else 0.065)
    if pages <= 110:
        return 2.84 if large else 2.30
    return 1.00 + pages * (0.017 if large else 0.012)


def royalty(price, cost):
    rate = 0.60 if price >= 9.99 else 0.50  # paperbacks under $9.99 earn 50%
    return round(price * rate - cost, 2), rate


def run(book_dir):
    book_dir = Path(book_dir)
    cfg = yaml.safe_load((book_dir / "book.yaml").read_text(encoding="utf-8"))
    info = json.loads((book_dir / "dist" / "build.json").read_text(encoding="utf-8"))
    puzzles = json.loads((book_dir / "dist" / "puzzles.json").read_text(encoding="utf-8"))
    results = []

    def check(name, ok, detail=""):
        results.append(("PASS" if ok else "FAIL", name, detail))

    # interior
    r = PdfReader(str(book_dir / "dist" / "interior.pdf"))
    n = len(r.pages)
    tw, th = cfg["trim"]
    ink = cfg.get("ink", "bw")
    check(f"Page count even and >= {MIN_PAGES[ink]} ({ink})", n >= MIN_PAGES[ink] and n % 2 == 0, f"{n} pages")
    check("Page count matches build.json", n == info["pages"])
    bad = [i + 1 for i, p in enumerate(r.pages)
           if abs(float(p.mediabox.width) - tw * PT) > 0.5 or abs(float(p.mediabox.height) - th * PT) > 0.5]
    check("Every page is the trim size", not bad, f"{tw} x {th} in" + (f"; wrong: {bad[:10]}" if bad else ""))
    unembedded = set()
    for p in r.pages:
        fonts = (p.get("/Resources") or {}).get("/Font") or {}
        for f in fonts.values():
            f = f.get_object()
            desc = f.get("/FontDescriptor")
            if f.get("/Subtype") == "/Type0":
                desc = f["/DescendantFonts"][0].get_object().get("/FontDescriptor")
            if desc is None or not any(k in desc.get_object() for k in ("/FontFile", "/FontFile2", "/FontFile3")):
                unembedded.add(str(f.get("/BaseFont")))
    check("All fonts embedded", not unembedded, ", ".join(sorted(unembedded)))

    # puzzles
    kind = cfg["puzzle_type"]
    problems = []
    for p in puzzles:
        if kind == "wordsearch":
            for w in p["words"]:
                k = count_occurrences(p["grid"], clean(w))
                if k != 1:
                    problems.append(f"puzzle {p['num']}: '{w}' found {k} times")
        elif kind == "sudoku":
            if count_solutions(p["puzzle"]) != 1:
                problems.append(f"sudoku {p['num']} does not have exactly one solution")
            if any(a and a != b for a, b in zip(p["puzzle"], p["solution"])):
                problems.append(f"sudoku {p['num']} solution does not match its givens")
        elif kind == "maze":
            if tuple(p["path"][0]) != tuple(p["start"]) or tuple(p["path"][-1]) != tuple(p["end"]):
                problems.append(f"maze {p['num']} path does not join start to finish")
    check(f"Every {kind} puzzle solvable exactly one way", not problems, "; ".join(problems[:5]))
    check("Puzzle count matches book.yaml", len(puzzles) == cfg["count"], f"{len(puzzles)} puzzles")

    # cover
    cover = book_dir / "dist" / "cover.pdf"
    if cover.exists():
        cp = PdfReader(str(cover)).pages[0]
        spine = n * PER_PAGE[cfg.get("paper", "white")]
        want_w, want_h = 0.25 + 2 * tw + spine, th + 0.25
        got_w, got_h = float(cp.mediabox.width) / PT, float(cp.mediabox.height) / PT
        check("Cover size matches page count", abs(got_w - want_w) < 0.01 and abs(got_h - want_h) < 0.01,
              f"{got_w:.3f} x {got_h:.3f} in (spine {spine:.3f} in)")
    else:
        check("Cover built", False, "run tools/build_cover.py")

    # money
    cost = print_cost(n, cfg["trim"], ink)
    price = float(cfg.get("price_usd", 9.99))
    earn, rate = royalty(price, cost)
    check("Royalty is positive", earn > 0, f"${price:.2f} x {int(rate * 100)}% - ${cost:.2f} print = ${earn:.2f} per copy")

    failed = [x for x in results if x[0] == "FAIL"]
    lines = ["# QA", "", "## Automatic checks", "", "| Result | Check | Detail |", "|---|---|---|"]
    lines += [f"| {a} | {b} | {c} |" for a, b, c in results]
    lines += ["", f"**{'FAIL' if failed else 'PASS'}** ({len(results) - len(failed)}/{len(results)} passed)", "",
              "Print cost uses Amazon.com rates for this ink; confirm in KDP's pricing calculator before publishing.", ""]
    (book_dir / "QA.md").write_text("\n".join(lines), encoding="utf-8")
    for a, b, c in results:
        print(f"{a}  {b}  {c}")
    return 1 if failed else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    sys.exit(run(sys.argv[1]))

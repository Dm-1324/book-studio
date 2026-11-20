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


UK_TO_US = {
    "colour": "color", "colours": "colors", "coloured": "colored", "colourful": "colorful", "favourite": "favorite",
    "honour": "honor", "grey": "gray", "centre": "center", "theatre": "theater", "behaviour": "behavior",
    "neighbour": "neighbor", "organise": "organize", "realise": "realize", "travelling": "traveling",
    "jewellery": "jewelry", "catalogue": "catalog", "programme": "program", "cosy": "cozy", "mould": "mold",
    "moult": "molt", "plough": "plow", "harbour": "harbor", "flavour": "flavor", "metre": "meter",
    "litre": "liter", "defence": "defense", "licence": "license", "armour": "armor", "labour": "labor",
    "rumour": "rumor", "savour": "savor", "parlour": "parlor", "vapour": "vapor", "practise": "practice",
    "ochre": "ocher", "sombre": "somber", "manoeuvre": "maneuver", "aluminium": "aluminum",
}
# Birds a US buyer won't know: only allowed on pages marked `region:` (e.g. a "Birds of Europe" page)
UK_ONLY_BIRDS = {
    "BLUETIT", "GREATTIT", "COALTIT", "DUNNOCK", "BLACKCAP", "LINNET", "CHAFFINCH", "GREENFINCH", "HAWFINCH",
    "YELLOWHAMMER", "REEDBUNTING", "BRAMBLING", "FIELDFARE", "REDWING", "SISKIN", "HOUSEMARTIN", "SANDMARTIN",
    "TAWNYOWL", "LITTLEOWL", "TREECREEPER", "PARTRIDGE", "PIPIT", "MOORHEN", "HOBBY", "REDSHANK", "SKYLARK",
    "SONGTHRUSH", "MISTLETHRUSH", "WOODPIGEON", "COLLAREDDOVE", "TURTLEDOVE", "JACKDAW", "ROOK", "CHOUGH",
    "GOLDCREST", "FIRECREST", "NIGHTINGALE", "WHITETHROAT", "STONECHAT", "WHEATEAR", "WAGTAIL", "ROBINREDBREAST",
}
PLACEHOLDERS = ["placeholder", "lorem", "todo", "tbd", "xxx", "fixme", "<new-slug>"]


def proofread(book_dir, cfg, info, puzzles, check):
    """Automatic proofreading. Each problem found here once needed a human to spot it."""
    import re
    entries = []
    pz = book_dir / "content" / "puzzles.yaml"
    if pz.exists():
        entries = yaml.safe_load(pz.read_text(encoding="utf-8")).get("puzzles", [])

    # 1. layout report from the builder (text past a panel edge, titles that don't fit, word-list collisions)
    lay = book_dir / "dist" / "layout.json"
    issues = json.loads(lay.read_text(encoding="utf-8")) if lay.exists() else [{"msg": "layout.json missing"}]
    check("Layout: no text overlaps or runs past its box", not issues,
          "; ".join(f"p{i.get('page', '?')}: {i['msg']}" for i in issues[:5]))

    # 2. the same word written two ways in different puzzles (GUINEAFOWL vs GUINEA FOWL)
    forms = {}
    for e in entries:
        for w in e.get("words", []):
            forms.setdefault(clean(w), set()).add(re.sub(r"\s+", " ", w.strip()).upper())
    mixed = {k: sorted(v) for k, v in forms.items() if len(v) > 1}
    check("Word lists: each word written the same way everywhere", not mixed,
          "; ".join(" vs ".join(v) for v in list(mixed.values())[:5]))

    # 3. odd characters / double spaces in words and titles
    bad = [w for e in entries for w in e.get("words", []) if not re.fullmatch(r"[A-Za-z][A-Za-z' -]*[A-Za-z]", w)
           or "  " in w]
    bad += [e["title"] for e in entries if len(e.get("title", "")) > 28 or "  " in e.get("title", "")]
    check("Word lists: clean words and titles (letters only, titles <= 28 chars)", not bad, ", ".join(bad[:8]))
    titles = [e.get("title") for e in entries]
    dup_titles = sorted({t for t in titles if titles.count(t) > 1})
    check("Puzzle titles are all different", not dup_titles, ", ".join(dup_titles))

    # 3b. near-duplicate puzzles and over-used words (a buyer notices repeats)
    sets = [(i + 1, {clean(w) for w in e.get("words", [])}) for i, e in enumerate(entries)]
    pairs = [f"{a}&{b} ({len(sa & sb)})" for k, (a, sa) in enumerate(sets) for b, sb in sets[k + 1:]
             if len(sa & sb) >= 5]
    check("Puzzles are distinct (no two share 5+ words)", not pairs, ", ".join(pairs[:8]))
    use = {}
    for n, st in sets:
        for w in st:
            use.setdefault(w, []).append(n)
    over = [f"{w} x{len(v)}" for w, v in sorted(use.items()) if len(v) > 3]
    check("No word used in more than 3 puzzles", not over, ", ".join(over[:10]))

    # 3c. repeated "Did you know?" facts: two facts sharing 2+ topic words (e.g. "dawn" + "chorus",
    #     "ostrich" + "largest") say the same thing twice
    generic = set("a an the and or of to in on at for from with by is are was be it its their they them this that "
                  "as can many some most often more than into out up so very which who when while bird birds other "
                  "any kind use uses used per hour hours miles mile fly flies flying live living one two year years "
                  "called help helps keep keeps make makes about over".split())
    def topic(t):
        return {re.sub(r"(es|s)$", "", w) for w in re.findall(r"[a-z]+", t.lower()) if w not in generic and len(w) > 2}
    fl = [(i + 1, e["fact"]) for i, e in enumerate(entries) if e.get("fact")]
    dupes = [f"{a}&{b2} ({'/'.join(sorted(topic(fa) & topic(fb)))})" for k, (a, fa) in enumerate(fl)
             for b2, fb in fl[k + 1:] if len(topic(fa) & topic(fb)) >= 2]
    check("Facts: no fact repeats another (book-checker decides)", not dupes, ", ".join(dupes[:8]), warn=True)

    # 3d. one grid size on every puzzle page (layout drift looks careless in a large-print book)
    cells = info.get("grid_cells", [])
    check("Same grid size on every puzzle page", len(cells) <= 1, f"sizes {cells}")

    # 3e. cover tagline must not repeat the subtitle
    cy = book_dir / "assets" / "cover.yaml"
    if cy.exists():
        feats = (yaml.safe_load(cy.read_text(encoding="utf-8")) or {}).get("features", "") or ""
        sub = cfg.get("subtitle", "").lower()
        phrases = [p.strip().lower() for p in re.split(r"[\u00b7|,]", feats) if p.strip()]
        rep = [p for p in phrases if len(p.split()) >= 2 and p in sub]
        check("Cover: tagline doesn't repeat the subtitle", not rep, ", ".join(rep))

    # 4. US or UK spelling, matching the main marketplace (amazon.com -> en-US)
    locale = cfg.get("locale", "en-US")
    if locale == "en-US":
        texts = [cfg.get("title", ""), cfg.get("subtitle", ""), cfg.get("how_to_play", ""), cfg.get("back_page", ""),
                 cfg.get("back_blurb", ""), (cfg.get("design") or {}).get("badge", "")]
        for e in entries:
            texts += [e.get("title", ""), e.get("fact", "")] + list(e.get("words", []))
        listing = book_dir / "listing.md"
        if listing.exists():
            texts.append(listing.read_text(encoding="utf-8"))
        found = sorted({m.lower() for t in texts for m in re.findall(r"[A-Za-z]+", t or "") if m.lower() in UK_TO_US})
        check("Spelling: US English throughout (book is for Amazon.com)", not found,
              ", ".join(f"{w} -> {UK_TO_US[w]}" for w in found))
        uk = sorted({f"{clean(w)} (p{i + 1})" for i, e in enumerate(entries) if not e.get("region")
                     for w in e.get("words", []) if clean(w) in UK_ONLY_BIRDS})
        check("Vocabulary: no UK-only names outside region pages", not uk, ", ".join(uk[:10]))

    # 5. leftovers: placeholder text anywhere a buyer could see it
    blobs = {"book.yaml": (book_dir / "book.yaml").read_text(encoding="utf-8")}
    for name in ("listing.md", "content/puzzles.yaml"):
        f = book_dir / name
        if f.exists():
            blobs[name] = f.read_text(encoding="utf-8")
    left = [f"{n}: '{w}'" for n, t in blobs.items() for w in PLACEHOLDERS
            if re.search(rf"\b{re.escape(w)}\b", t, re.I) and not (n == "book.yaml" and w == "todo")]
    check("No placeholder or TODO text left", not left, "; ".join(left[:5]))

    # 6. listing matches the book
    listing = book_dir / "listing.md"
    if listing.exists():
        lt = listing.read_text(encoding="utf-8")
        counts = {int(x) for x in re.findall(r"\b(\d+)\s+(?:extra-large-print\s+|large-print\s+|full-color\s+)?"
                                             r"(?:puzzles|word searches)\b", lt, re.I)}
        check("Listing: puzzle count matches the book", counts <= {info["count"]},
              f"listing says {sorted(counts)}, book has {info['count']}")
        check("Listing: AI disclosure filled in", "AI-generated content" in lt and "Text:" in lt)
        check("Listing: pen name matches book.yaml", cfg["author"] in lt)

    # 7. "Did you know?" facts must be verified by the fact-checker agent (FACTS.md, with a source link)
    facts = [e["fact"] for e in entries if e.get("fact")]
    if facts:
        fm = book_dir / "FACTS.md"
        text = fm.read_text(encoding="utf-8") if fm.exists() else ""
        rows = [ln for ln in text.splitlines() if ln.startswith("|")]
        missing = [f for f in facts if not any(f in ln and "VERIFIED" in ln and "http" in ln for ln in rows)]
        check(f"Facts: all {len(facts)} verified with a source (FACTS.md)", not missing,
              (f"{len(missing)} not verified, e.g. '{missing[0]}'" if missing else ""))


def run(book_dir):
    book_dir = Path(book_dir)
    cfg = yaml.safe_load((book_dir / "book.yaml").read_text(encoding="utf-8"))
    info = json.loads((book_dir / "dist" / "build.json").read_text(encoding="utf-8"))
    puzzles = json.loads((book_dir / "dist" / "puzzles.json").read_text(encoding="utf-8"))
    results = []

    def check(name, ok, detail="", warn=False):
        results.append(("PASS" if ok else ("WARN" if warn else "FAIL"), name, detail))

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

    # ---- proofreading: everything a human proofreader used to catch ----
    proofread(book_dir, cfg, info, puzzles, check)

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

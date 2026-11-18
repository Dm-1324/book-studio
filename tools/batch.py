"""Weekly batch: research -> plan -> content -> build -> cover -> check -> listing.

usage: python tools/batch.py            # run for real (Windows Task Scheduler calls this)
       python tools/batch.py --dry-run  # print what would run

Makes at most `weekly_new_titles` (config.json) READY books that are not uploaded yet.
Never touches KDP. Agent steps run through Claude Code in headless mode (config.json claude_cmd).
"""
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
DRY = "--dry-run" in sys.argv
LOG = ROOT / "logs" / f"batch-{dt.date.today()}.log"


def log(msg):
    line = f"{dt.datetime.now():%H:%M:%S} {msg}"
    print(line)
    if not DRY:
        LOG.parent.mkdir(exist_ok=True)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")


def run(cmd, what):
    log(f"-> {what}")
    if DRY:
        log("   " + " ".join(cmd))
        return 0
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    with LOG.open("a", encoding="utf-8") as f:
        f.write(r.stdout[-4000:] + "\n" + r.stderr[-4000:] + "\n")
    if r.returncode:
        log(f"   FAILED ({r.returncode})")
    return r.returncode


def agent(prompt, what):
    return run(CFG["claude_cmd"] + [prompt], what)


def tool(name, *args):
    return run([sys.executable, f"tools/{name}.py", *args], f"{name} {' '.join(args)}")


def waiting_books():
    """READY books not yet marked Uploaded in research/published.md."""
    published = (ROOT / "research" / "published.md").read_text(encoding="utf-8")
    out = []
    for d in sorted((ROOT / "books").iterdir()):
        if (d / "READY").exists() and not re.search(rf"\|\s*{d.name}\s*\|.*Uploaded", published):
            out.append(d.name)
    return out


def make_book(slug):
    book = f"books/{slug}"
    for attempt in range(1, 3):
        if agent(f"Use the wordlist-writer agent for {book}.", f"word lists ({slug}, try {attempt})"):
            continue
        if tool("build_book", book):
            continue
        agent(f"Use the cover-artist agent for {book}.", "cover art")
        if tool("build_cover", book):
            continue
        tool("check_book", book)
        agent(f"Use the book-checker agent for {book}.", "visual check")
        if (ROOT / book / "READY").exists() or DRY:
            agent(f"Use the listing-writer agent for {book}.", "listing")
            return True
        log(f"   {slug} rejected, see {book}/REJECTED.md")
    return False


def main():
    limit = CFG.get("weekly_new_titles", 2)
    ready = waiting_books()
    need = limit - len(ready)
    log(f"waiting to upload: {ready or 'none'}; making {max(need, 0)} new")
    if need <= 0:
        return
    today = dt.date.today()
    research = ROOT / "research" / f"niches-{today}.md"
    if not research.exists():
        agent("Use the niche-scout agent to research new puzzle-book niches.", "niche research")
    for i in range(need):
        before = {d.name for d in (ROOT / "books").iterdir()}
        agent(f"Use the book-planner agent: take the highest-scoring niche in research/niches-{today}.md "
              f"that is not in research/published.md and create its book folder.", f"plan book {i + 1}")
        new = sorted({d.name for d in (ROOT / "books").iterdir()} - before)
        if not new and not DRY:
            log("   planner made no new book folder; stopping")
            return
        slug = new[0] if new else "<new-slug>"
        if make_book(slug):
            log(f"READY: {slug}")


if __name__ == "__main__":
    main()

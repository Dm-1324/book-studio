"""Keep the Pinterest queue in Buffer topped up with pins from all live books.

usage: python tools/post_pins.py            # run daily from Task Scheduler (after the reel batch)
       python tools/post_pins.py --dry-run

Rules
- Only books with amazon_url set in book.yaml (= live on Amazon) are posted; their pins come from dist/pins/pins.json.
- Buffer free plan: max 10 scheduled posts per channel at a time, so this tops the queue up to
  config.json pinterest.queue_target (default 8) and never more.
- Spread: at most pinterest.per_day pins a day (default 2), alternating between books, newest books first.
- Pin images must be at a public URL for Buffer to fetch: they are copied into the public media repo
  (config.json pinterest.image_repo_dir, e.g. the reel-media repo) and pushed; image URL = image_base_url + file name.
- State in research/pins-posted.json, so a pin is never queued twice.

Wiring on dm-1324 (one time): point BUFFER_ADAPTER at Reel Studio's existing Buffer client
(config.json pinterest.buffer_adapter = "module:function" taking (channel_id, text, image_url, link, when)).
"""
import datetime as dt
import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8")).get("pinterest", {})
STATE = ROOT / "research" / "pins-posted.json"
DRY = "--dry-run" in sys.argv


def live_books():
    for d in sorted((ROOT / "books").iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        y = d / "book.yaml"
        pins = d / "dist" / "pins" / "pins.json"
        if y.exists() and pins.exists():
            cfg = yaml.safe_load(y.read_text(encoding="utf-8"))
            if cfg.get("amazon_url"):
                yield d, cfg, json.loads(pins.read_text(encoding="utf-8"))


def adapter():
    spec = CFG.get("buffer_adapter")
    if not spec:
        return None
    mod, fn = spec.split(":")
    sys.path.insert(0, str(Path(CFG.get("adapter_path", ".")).resolve()))
    return getattr(importlib.import_module(mod), fn)


def main():
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"posted": [], "scheduled": []}
    done = set(state["posted"])
    now = dt.datetime.now()
    # pins still waiting in Buffer = those scheduled for the future
    waiting = sorted(t for t in state.get("scheduled", []) if dt.datetime.fromisoformat(t) > now)
    target = CFG.get("queue_target", 8)
    per_day = CFG.get("per_day", 2)
    room = max(0, target - len(waiting))
    todo = []
    books = list(live_books())
    # round-robin across books so every live book keeps getting pins
    queues = [[(d, cfg, p) for p in pins if f"{d.name}/{p['image']}" not in done] for d, cfg, pins in books]
    while any(queues) and len(todo) < room:
        for q in queues:
            if q and len(todo) < room:
                todo.append(q.pop(0))
    if not todo:
        print("nothing to queue (no live books with unposted pins, or queue full)")
        return
    post = adapter()
    # continue after the last waiting pin; evening IST slots = US morning
    last = dt.datetime.fromisoformat(waiting[-1]) if waiting else now
    start = (last + dt.timedelta(days=1)).replace(hour=19, minute=0, second=0, microsecond=0)
    for i, (d, cfg, pin) in enumerate(todo):
        when = start + dt.timedelta(days=i // per_day, hours=(i % per_day) * 3)
        name = f"{d.name}-{pin['image']}"
        url = CFG.get("image_base_url", "").rstrip("/") + "/" + name
        print(f"queue {name} at {when:%Y-%m-%d %H:%M} -> {pin['link']}")
        if DRY:
            continue
        repo = Path(CFG["image_repo_dir"])
        shutil.copy(d / "dist" / "pins" / pin["image"], repo / name)
        subprocess.run(["git", "add", name], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-m", f"pin {name}"], cwd=repo, check=True)
        subprocess.run(["git", "push"], cwd=repo, check=True)
        text = f"{pin['title']}\n\n{pin['description']}"
        if post is None:
            raise SystemExit("config.json pinterest.buffer_adapter is not set (see this file's docstring)")
        post(CFG["channel_id"], text, url, pin["link"], when)
        done.add(f"{d.name}/{pin['image']}")
        waiting.append(when.isoformat())
    state["posted"] = sorted(done)
    state["scheduled"] = waiting
    if not DRY:
        STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

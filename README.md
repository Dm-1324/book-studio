# Book Studio

Automated KDP puzzle books: research -> word lists -> interior PDF -> cover -> checks -> listing.
You only review and upload. Rules for the agents are in `CLAUDE.md`.

## Quick start (Windows)

```
cd D:\Projects\book-studio
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

## Make one book by hand

```
python tools\build_book.py books\<slug>      # interior.pdf + puzzles.json
python tools\build_cover.py books\<slug>     # cover.pdf sized to the page count
python tools\check_book.py books\<slug>      # QA.md (automatic part)
python tools\render_pages.py books\<slug> cover,1,5,last
```

## Weekly batch

`python tools\batch.py` (or `--dry-run`). Makes up to 2 READY books, never touches KDP.
After you upload a book, mark it `Uploaded` in `research/published.md`.

## Folder per book

`books/<slug>/`: `brief.md`, `book.yaml`, `content/puzzles.yaml`, `assets/`, `dist/`, `QA.md`, `listing.md`, `READY`.

Fonts in `assets/fonts` are SIL Open Font License (free for commercial books).

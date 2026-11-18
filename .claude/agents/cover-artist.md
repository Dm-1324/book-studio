---
name: cover-artist
description: Designs the cover art prompt, runs Fooocus, and builds the wrap cover. Use after the interior is built.
tools: Read, Write, Bash
---
1. Read `brief.md`. Look at the top competitor covers listed in the research file and note the genre look (colours, layout).
2. Write 3 Fooocus prompts for front-cover art with NO text in the image (text is added by code). Save to `assets/cover-prompts.md`.
3. Run Fooocus (see config.json `fooocus`) to make 2 images per prompt into `assets/art/`.
4. Pick the best one (clear at thumbnail size, matches the theme, nothing trademarked), copy to `assets/cover-art.png`.
5. Run `python tools/build_cover.py books/<slug>`. Then render `dist/cover-preview.png` and look at it at thumbnail size.
Record in `listing.md` that the cover art is AI-generated.

# CLAUDE.md

Guidance for working on this repo. See `README.md` for setup/usage; this file is about
decisions made, gotchas hit, and how to verify changes.

## Project shape

- `app.py` — Streamlit frontend (image gallery + chat sidebar).
- `api.py` — FastAPI backend (`/images/list`, `/images/<file>`, `/chat` via local Ollama `moondream`).
- `download_images.py` — one-off scraper populating `images/`.
- Plain venv workflow (`make venv`), no other package manager.

## Decisions made in `app.py` and why

- **Gallery tiles are buttons whose label is a markdown image** (`st.button(f"![{id}]({url})", ...)`),
  not `st.image` + a separate "Select" button. This makes the whole image clickable without any
  extra dependency. Rejected alternative: `streamlit-image-select` — it has a **confirmed upstream
  bug** (its shipped compiled JS hardcodes the initial "selected" tile to index 0, ignoring the
  `index` prop; verified by diffing its own `frontend/src` against its `frontend/build`). Don't
  reintroduce that package without patching the bundle.
- **Selected border is same thickness as unselected** (`TILE_BORDER_WIDTH = 3`, unselected uses
  `3px solid transparent`), so a tile's box size never shifts when selected. Earlier version used
  a thinner unselected border and it caused the whole grid to jiggle on selection.
- **Gallery grid and nav row use a hand-built fixed-width flex layout** (`st.container(key=...)`
  styled with `display:flex; flex-wrap:wrap; gap:{GRID_GAP}px; width:{GRID_WIDTH}px`), not
  `st.columns(COLUMNS)`. Reason: `st.columns` divides width *proportionally* to the viewport and
  left-aligns fixed-size content inside each column, leaving asymmetric leftover space that shifts
  with window width. That made "align the Next button with the last picture" and "center the page
  label between columns 2 and 3" impossible to get pixel-exact with plain CSS — the offset between
  the "abstract column boundary" and the "visual gap between tiles" changes with viewport width.
  Switching to a fixed-width flex row with an explicit `GRID_GAP` made every position a fixed,
  computable pixel value (`TILE_WIDTH`, `GRID_WIDTH`), independent of viewport.
- `GRID_WIDTH = COLUMNS * TILE_WIDTH + (COLUMNS - 1) * GRID_GAP` is the single source of truth for
  both the nav row and the gallery grid width — keep them driven by this constant, don't hardcode
  pixel positions.
- Sidebar preview image still uses a plain `<div class="img-box">` (not a button — it's not
  clickable) with `object-fit: contain` letterboxing, sized via `PREVIEW_SIZE`.

## Streamlit/CSS gotchas hit (useful if touching styling again)

- `st.container(key="foo")` and any widget with `key="foo"` get a `st-key-foo` class on their
  wrapper `data-testid="stElementContainer"`/`stVerticalBlock` div — that's the reliable hook for
  scoped CSS (`div[class*="st-key-foo"] ...`), not `key` itself as a DOM id.
- Streamlit's own base CSS sets `flex-direction: column` on every `stVerticalBlock`. If you make one
  `display:flex` for a custom layout, you **must** also set `flex-direction: row !important` or
  children just stack vertically instead of wrapping into a row.
- Streamlit's own CSS caps markdown-rendered `<img>` (e.g. inside a button label) to
  `max-height: 1em` (`.st-emotion-cache-* img { max-height: 1em; ... }`) — meant for inline icons.
  To get a real-size image you must override **both** `height` and `max-height` (not just
  `height`) with `!important`.
- A widget's own `.stButton` div often carries Streamlit's own `width: 100%` rule. If you nest it
  inside a container you've given an explicit fixed width, that rule will make the child fill it —
  fine when you want that (e.g. nav row buttons use `width: auto !important` to stay natural-sized
  instead).
- Emotion-generated class names (`st-emotion-cache-xxxx`) are unstable across Streamlit versions/
  reruns — never target those directly; always go through stable `data-testid` attributes
  (`stElementContainer`, `stButton`, `stColumn`, `stHorizontalBlock`, `stVerticalBlock`) or our own
  `st-key-*` classes.
- Two full-width `st.columns(N)` calls made in the *same* script run **do** end up with visually
  identical column boundaries (Streamlit divides the same content width the same way each time) —
  but that boundary is not where a left-aligned, fixed-size widget *inside* one of those columns
  visually ends, because of leftover unused column space. Don't assume "same `st.columns` call
  shape" implies "same visual edges" for fixed-size content.

## How to verify UI changes

This is a Streamlit app — type-checking or running the script headless proves nothing about layout/
alignment/clickability. Actually verify in a browser before calling a UI change done:

1. Start the API (`make api` or `.venv/bin/fastapi run api.py`) and the app
   (`.venv/bin/streamlit run app.py --server.port 8501 --server.headless true &`), polling
   `curl -sf http://127.0.0.1:8501` until it's up rather than sleeping.
2. Drive it with Playwright (`npx playwright install chromium` once, then a small script using
   `chromium.launch()` — no `chromium-cli` available in this environment). Dismiss the Streamlit
   "Install skills" nudge (`Don't show again`) before clicking anything, or it intercepts clicks.
3. For pixel-alignment claims ("X's right edge matches Y", "centered between columns"), don't eyeball
   a screenshot — pull `getBoundingClientRect()` on both elements via `page.evaluate` and compare
   numbers. Screenshots are for a final human-readable sanity check, not for confirming exact
   alignment.
4. Remember `st.columns(...)` groups DOM output **by column**, not by row: all of `cols[0]`'s
   elements across every loop iteration render together, then all of `cols[1]`'s, etc. Don't assume
   `nth(i)` on a button locator corresponds to the i-th visual (row-major) position.
5. Kill/restart the Streamlit process between edits if testing — it does not reliably hot-reload
   custom CSS/component changes, and there's no `watchdog` installed in this venv so file-watching
   is the slow poll-based fallback.

## Working conventions for this repo

- Only two real "state" things in `app.py`: `st.session_state.page` and `.selected_image` (plus
  `.chat_history`, cleared whenever the selected image changes). Any new feature that touches
  pagination or selection should go through `select_image()`, not set `selected_image` directly,
  so chat history stays consistent.
- Ask before adding a new pip dependency for a UI nicety — we already hit one real bug in a
  third-party Streamlit component this way (see above); a CSS-only/pure-Streamlit approach has so
  far always been achievable and keeps `requirements.txt` minimal.
- Prefer fixed Python constants (`THUMB_SIZE`, `TILE_WIDTH`, `GRID_GAP`, `GRID_WIDTH`,
  `NAV_BUTTON_WIDTH`, `SELECTED_BORDER`/`TILE_UNSELECTED_BORDER`) over ad hoc pixel values sprinkled
  in CSS strings, so sizing stays derivable and single-sourced.

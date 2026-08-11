# Ersilia repository search

A search engine for the `ersilia-os` repository estate. All 180 repositories are on screen from
the moment the page loads, as a sortable table; typing narrows and re-ranks it. Searched entirely
in the browser, with no server and no build step.

Built to the Ersilia [`html-formatting`](https://github.com/ersilia-os/ersilia-skills) house style.

## The table

Six columns — **Repository · Title · Type · Status · Project · Created** — **strictly one line per
repository**, about 25 on screen at a time, inside a single bordered frame that also holds the
toolbar and the filters. Matched text is highlighted in every column.

**Hovering a row opens a card** with everything the row cannot fit: the full title, the
description, *all* types and statuses rather than the first plus a `+1`, every linked project, the
date and the URL. It follows the `↑`/`↓` selection too, so it is not a mouse-only feature. It
replaces the native `title` tooltip entirely — there are no `title` attributes on rows, because a
browser tooltip would surface on top of the card a second later.

Click any column header to sort by it, click again to reverse. With no query the table is newest
first; with a query it is ranked by relevance, and the toolbar offers a way back to that ranking
if you have sorted by a column.

Clicking a row opens the repository on GitHub. Private repositories are the exception: they are
fully searchable and carry a `private` badge, but are not linked, since the URL 404s for anyone
outside the organisation.

A repository may carry two types or two statuses (5 and 3 of them do). Two badges will not fit
those columns and wrapping would break the one-line rule, so the cell shows the first badge and a
`+1`, with all labels in its tooltip.

### Type and spacing scales

Both are declared as tokens at the top of the page stylesheet. **Pick a step; do not invent one** —
that is the whole point of having them. Before they existed the page had nine font sizes inside an
11px range (12 / 12.5 / 13 all doing row text) and 23 distinct spacing values.

| Token | Size | Used for |
|---|---|---|
| `--fs-1` | 11px | badges, filter chips, column headers, `kbd`, counts, labels |
| `--fs-2` | 12px | project and date cells, footer |
| `--fs-3` | 13px | the row itself — slug and title — the lede, body copy |
| `--fs-4` | 15px | the search input; empty-state and dialog headings |
| `--fs-5` | 28px | the hero heading |

Spacing is `--s1`…`--s8` on a 4/8 grid (4, 8, 12, 16, 24, 32, 48, 64). Weights are 400 body, 500
labels and identifiers, 600 the heading — plus the theme's own 450 on bare buttons, which is a
house-style rule and is left alone. Radii use only the theme's `--radius-sm`, `--radius` and 999px.

### The hero, and why this one works

An earlier hero was a centred 640px stack above a 1240px table. It never belonged to the page, and
tuning its margins never helped, because **the problem was alignment, not spacing**. This one is
left-aligned to the table's own edge and the search field spans the same full measure, so the two
read as one column: the org name, the heading, a line of links out to the rest of the ecosystem
(ersilia.io, the GitHub organisation, the model catalog), then the field.

That line used to be a lede restating figures — "180 repositories across 30 projects" — which is
filler when the same numbers are already in the search field and the footer. Pointing somewhere is
worth a line; repeating yourself is not.

**The field is its own sticky bar.** `.searchdock` is `position: sticky`, so as the hero scrolls
away the field stays as a slim pinned bar — carrying the live result count, which lives inside the
field for exactly this reason. It is the *same* input, not a second one, so there is no duplicate
query state to keep in sync, and no morphing collapse animation. The table's column headers pin
beneath it via `--headh`, which is measured from the dock.

Several theme components sat just off the scale — the eyebrow at 11.5px/600, the filter chips at
11.5px/450, the footer credit at 11.5px — and are pulled onto it. That is deliberate, not drift.

**Mono now means exactly four things:** repository slugs, dates, counts and filter tokens. Badges
moved to sans, which is what makes the house rule ("mono earns its place on numbers, not on
chrome") true rather than aspirational.

### Badge colour

Two encodings doing two different jobs:

**Type is categorical** — one hue per kind of work, so the shape of the estate reads at a glance:
Analysis lime · Package cobalt · Automation tangerine · App orchid · Workshop amber ·
Template turquoise · Documentation fuchsia. The two dominant types (Analysis 71, Package 71) take
the two most separated hues, because "analysis or package?" is the distinction a reader actually
makes. **Crimson is deliberately absent** so no repository type can read as a warning.

**Status is semantic** — planned cobalt, active periwinkle, completed green, idle amber, and the
two deliberate endings in neutral grey. **Archived is never red.** Closing a research repository
down is a normal ending, not a failure, and the page is not scored against a target.

`private` is **outlined rather than filled**, in red. Filled, it was the loudest thing in the
table; outlined, it reads as a marker instead of an alert — and it earns the red, because it is
the one row state that means *you cannot open this*.

**The filter chips carry the same colours as the badges they select**, so "Package" in the panel
and "Package" in a row are visibly the same thing. Pressing a chip moves along its own hue rather
than switching to periwinkle, which would otherwise flatten all seven types to one colour the
moment you selected one.

Badges use a stronger mix than the theme default (32% background / 80% text / 50% border, up from
20/72/34) — at the default tint seven hues still read as one pale wash.

## Searching

Free text matches the repository name, title, description and project. Results rank by **where**
the match lands — the name outranks the title, which outranks the project and the description —
so typing `chembl` puts the `chembl-*` repositories above anything that merely mentions ChEMBL in
prose. Hyphens, underscores and spaces are the same separator, so `chembl antimicrobial` finds
`chembl-antimicrobial-tasks`. Every term has to match somewhere; matched text is highlighted.

Narrow with tokens, alone or alongside free text:

| Token | Example |
|---|---|
| `type:` | `type:package` |
| `status:` | `status:archived` |
| `project:` | `project:"Ersilia Model Hub"` |
| `year:` | `year:2025` |
| `is:` | `is:private`, `is:public` |

The filter chips write exactly these tokens into the box, so the query bar is always the whole
query — there is no hidden filter state to get out of sync with what you can see.

### The filters are inclusion toggles, and some start off

Each chip is on by default and **unchecking it hides those repositories** — colour means enabled,
grey means not. Five start off, so the page opens on live public work rather than on everything
ever created: **Idle, Discontinued, Todo, Archived** and **Private**. That is **94 of 180**.

An enabled chip is styled with the *exact* mixes of the badge it enables (32% background, 50%
border, 80% text), so a chip and its badge are indistinguishable in format. The visibility pair is
the exception, and deliberately so: both are **outlined rather than filled** — Private red, Public
blue — matching how `Private` is drawn in the table itself.

**Because filters are on by default, a search can match something currently hidden** — 86
repositories are outside the default view, so a search for a discontinued repository would
otherwise look like a dead end. When that happens a line appears under the filters saying how many
matches are hidden, with a **Show all** button. It is deliberately suppressed on the landing view,
where the defaults are the point and the chips already say which are off.

Typing a token scopes its group explicitly and overrides the chips; clicking a chip afterwards
folds that token into the chip state and removes it from the query, so the two can never disagree.

### How the controls are organised

- **Project sits beside the search field, not among the chips.** It is a *scope* — it narrows what
  you are searching rather than describing a property of a result — so it belongs with the query.
  Sorted alphabetically, since you scan it for a known name. It is styled to match the field
  exactly (same surface, border, radius and height) with `appearance: none` and a chevron drawn
  from two rotated borders, because the native select arrow is painted by the browser inside its
  own padding box and cannot be spaced properly.
- **The chip groups run in the table's own column order**: Type, then Status, then Visibility.
  They used to run Status-first, against the table.
- **The filter labels are inset by 13px** — the table's border plus its cell padding — so they line
  up with the `Repository` column header rather than sitting a few pixels off it.
- **The sort note sits on the last filter row, right-aligned**, directly above the table's own sort
  arrow instead of in a band of its own.
- **There are no active-filter pills.** Filter state was being shown three times over — pressed
  chips, tokens in the query bar, and the pills. The chips and the query text are enough.

**Keyboard:** `⌘K` / `Ctrl+K` or `/` focuses the field · `↑` `↓` move through rows ·
`Enter` opens the selected repository on GitHub · `Esc` clears the search.

## Where the data comes from

The *Repositories* table of Ersilia's **Ersilia Content** Airtable base
(`app1iYv78K6xbHkmL` / `tbluZtI3W9pseCSPH`), which a nightly cron action keeps in step with the
GitHub organisation. Nothing is fetched from GitHub directly, so there are no tokens, no rate
limits and no live dependencies.

## Responsive behaviour

Three layouts, not one that shrinks:

| Width | Layout |
|---|---|
| > 1080px | all six columns |
| 760–1080px | Project and Created drop — both are still in the hover card |
| < 760px | **the table stops being a table.** Each repository becomes a card: name and title on their own lines, badges and metadata flowing beneath. Nothing scrolls sideways. |

The header stacks below 760px and the hover card is gated behind
`(hover: hover) and (pointer: fine)`, so it never fires on touch.

## Running it

No build step and no server needed — open `index.html`. It also works over
`python -m http.server` and on GitHub Pages.

## Refreshing the data

```bash
export AIRTABLE_API_KEY=pat...        # PAT with data.records:read on the Ersilia Content base
python scripts/fetch_repositories.py --date 2026-08-11
```

This rewrites `data/repositories.js` and `data/repositories.json`. The page picks the change up on
reload; `index.html` never needs rebuilding for a data refresh.

The snapshot date is passed in rather than read from the clock, so a run is reproducible — the
same convention as the other scripts in the Ersilia skills repos.

### Private repositories

38 of the 180 repositories are private. They are **included by default**: fully searchable, shown
with a `private` badge, and not linked, since the URL would 404 for anyone outside the
organisation.

**If this site is published publicly, their names and descriptions go public with it.** To drop
them from the data entirely:

```bash
python scripts/fetch_repositories.py --date 2026-08-11 --exclude-private
```

That is a data-level exclusion, not a display toggle — the private records never reach the browser.

## Rebuilding the page

`index.html` is generated from `src/index.src.html`. Edit the source, then:

```bash
python scripts/build.py              # index.html
python scripts/build.py --artifact   # + dist/artifact.html
```

`build.py` runs `apply_theme.py` from the `html-formatting` skill in retrofit mode: it inlines the
canonical `ersilia.css` and the SVG favicon into the document head, and hoists the source file's
own style block so it cascades after the theme. Re-running it after the skill's theme changes is
how this page picks up a house-style update.

If the skill lives somewhere other than `~/.claude/skills/html-formatting`, pass `--skill`.

> **Note when editing `src/index.src.html`:** the assembler hoists styles with a regex, so never
> write a literal opening `style` tag inside a comment — it will swallow everything up to the real
> one and silently break the page.

## Design choices worth knowing

**The theme is inlined; the data is not.** `ersilia.css` is ~14 KB and effectively static, so
inlining keeps the page a single file. The data changes nightly, so it stays separable.

**The data is a `.js` file, not JSON loaded with `fetch()`.** `fetch()` on a local file is blocked
by CORS, which would leave `index.html` blank when opened straight from disk. A same-origin
`<script src>` defining one global behaves identically from `file://` and from GitHub Pages.
`data/repositories.json` ships alongside for anything else that wants the data.

Same-origin `<script src>` is correct for a hosted site and is *not* a self-containment violation
under the skill's rules — that check targets off-document hosts. The Artifact build
(`dist/artifact.html`) inlines the data instead, because Artifacts block all external hosts via
CSP and have no sibling files.

**Status is the only categorical colour, and it is semantic** — planned in cobalt, active in
periwinkle, completed in green, idle in amber, and the two deliberate endings (archived,
discontinued) in neutral grey. Archived work is never drawn in red: closing down a research
repository is a normal ending, not a failure. Everything else is one accent. No colour outside the
Ersilia palette is used anywhere.

**Counts do not all sum to 180.** Status and type are Airtable multi-select fields: 3 repositories
carry two statuses and 5 carry two types. Filter chip counts are computed against every *other*
active filter, so a chip always predicts what picking it would actually yield.

**Three CSS traps this page has already fallen into.** All three are load-bearing, so read them
before editing the table styles:

1. **Backgrounds and separators go on the cells, never the row.** A background on a `<tr>` is
   overpainted by its own cells, and `box-shadow` on a row does not render at all. The three row
   states are equal-specificity, so their order in the stylesheet decides which wins.
2. **Nothing above the table may have `overflow`.** An ancestor with `overflow: auto` becomes the
   scroll container for `position: sticky` and silently stops the column headers pinning. That is
   why the frame's rounded corners come from the corner *cells* rather than from clipping the
   container, and why the wrapper only scrolls under the mobile breakpoint — where sticky headers
   are turned off anyway.
3. **Absolutely-positioned descendants need a positioned ancestor.** The visually-hidden
   description spans resolve against the nearest positioned ancestor; with none, that is the
   viewport, so they escape the table's horizontal scroll clipping and drag ~300px of phantom page
   width at narrow viewports. The cells are `position: relative` to contain them.

## House-style check

Checked with the skill's own `check_html.py` against the **rendered** DOM (the page is
JS-rendered, so checking the source file alone would inspect an empty results region):
**no blockers and no should-fix findings.**

One nice-to-have residual, deliberately left:

- **`T2-ACCENT-SPRAWL` — 9 accent hues.** This is the documented trade, not an oversight.
  Seven of those hues are the Type encoding: one per kind of work, which is the palette doing real
  work rather than decoration — exactly the carve-out `design-system.md` makes for per-category
  hues that identify something. Two more (`--purple`, `--mint`) are not used by this page at all;
  they come from the inlined `ersilia.css` (`.cbar`, and one inside a CSS comment), so every page
  built with this skill starts at two.

  The check exists to stop flat accents being sprinkled across chrome, and the reason it does not
  apply here is that **every badge carries its own text label** — unlike a chart mark, colour is a
  redundant channel, never the only one. Do not "fix" this by repainting the badges periwinkle;
  that removes the encoding and returns the table to the flat wash it started as.

```bash
python ~/.claude/skills/html-formatting/scripts/check_html.py index.html --date 2026-08-11
```

## Layout

```
index.html                    the search engine (generated — edit src/, not this)
src/index.src.html            page source: markup, styles, search logic
data/repositories.js          window.ERSILIA_REPOS — what the page loads
data/repositories.json        the same payload, for machine consumers
dist/artifact.html            single-file build for publishing as a Claude Artifact
scripts/fetch_repositories.py Airtable → data files
scripts/build.py              src/ → index.html (and --artifact)
```

## Status of the refresh script

`scripts/fetch_repositories.py` has been verified against all 180 real records: its normalisation
and payload assembly reproduce `data/repositories.json` byte for byte, and `--exclude-private`
correctly yields 142. Its HTTP layer has **not** been exercised end to end, because the initial
data was captured through the Airtable MCP connector rather than a personal access token. The
first person to run it with `AIRTABLE_API_KEY` set should sanity-check the record count.

---

Brought to you by the [Ersilia Open Source Initiative](https://ersilia.io) — a tech-nonprofit
fueling sustainable research in the Global South.

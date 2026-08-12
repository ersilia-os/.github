#!/usr/bin/env python3
"""build.py — assemble index.html from src/index.src.html.

Thin wrapper around apply_theme.py from Ersilia's `html-formatting` skill, run in
retrofit mode: it swaps in the canonical Ersilia <head> (ersilia.css inlined plus
the inline-SVG target favicon) and hoists the source file's own <style> so it
cascades after the theme.

    python scripts/build.py
    python scripts/build.py --skill /path/to/ersilia-skills/skills/html-formatting

Edit src/index.src.html, then rebuild. Re-running after the skill's theme changes
is how this page picks up a house-style update.

Standard library only.
"""

from __future__ import annotations

import argparse
import re
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SKILL = Path.home() / "Documents/GitHub/ersilia-skills/skills/html-formatting"

TITLE = "Search repositories in the Ersilia ecosystem"
SOURCE_URL = "https://github.com/ersilia-os/.github/tree/main/repository-browser"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument(
        "--skill",
        default=str(DEFAULT_SKILL),
        help=f"path to the html-formatting skill (default: {DEFAULT_SKILL})",
    )
    p.add_argument("--src", default=str(ROOT / "src/index.src.html"))
    p.add_argument("--out", default=str(ROOT / "index.html"))
    p.add_argument(
        "--artifact",
        nargs="?",
        const=str(ROOT / "dist/artifact.html"),
        help="also emit a single-file build with the data inlined, for publishing as a "
        "Claude Artifact (Artifacts block external hosts via CSP, so the same-origin "
        "data/repositories.js the hosted site uses would never load). "
        "Default: dist/artifact.html",
    )
    args = p.parse_args(argv)

    skill = Path(args.skill).expanduser().resolve()
    theme = skill / "scripts/apply_theme.py"
    if not theme.exists():
        print(
            f"ERROR: apply_theme.py not found at {theme}\n"
            "Pass --skill with the path to ersilia-skills/skills/html-formatting.",
            file=sys.stderr,
        )
        return 2

    # apply_theme.py imports its sibling _common and resolves assets relative to
    # itself, so run it in place with the argv it expects.
    sys.path.insert(0, str(theme.parent))
    sys.argv = [
        str(theme),
        args.src,
        "--mode", "retrofit",
        "--out", args.out,
        "--title", TITLE,
        "--source-url", SOURCE_URL,
        # Pinned rather than left to the skill's title-derived default: this page
        # is the organisation's front door, so its tab keeps the identity colour
        # even if the title is later reworded.
        "--favicon", "plum",
    ]
    try:
        runpy.run_path(str(theme), run_name="__main__")
    except SystemExit as exc:  # apply_theme.py ends with raise SystemExit(main())
        if exc.code:
            return int(exc.code)

    if args.artifact:
        inline_data(Path(args.out), Path(args.artifact))
    return 0


DATA_TAG = '<script src="data/repositories.js"></script>'


def inline_data(page: Path, out: Path) -> None:
    """Emit the Claude Artifact build: data inlined, document skeleton removed.

    Two differences from the hosted page, both forced by how Artifacts work:

    * The data travels inside the document. An Artifact has no sibling files and
      blocks every external host via CSP, so the same-origin data/repositories.js
      the hosted site loads would never resolve. The hosted site keeps the
      external file on purpose — it lets a data refresh skip rebuilding the page.
    * No <!doctype>/<html>/<head>/<body>. The Artifact host wraps the file in its
      own skeleton at publish time, so those tags would nest inside it. The
      <title>, <meta>, <link rel=icon> and <style> are kept — the host hoists
      them — which is why this file is publish-ready rather than standalone.
    """
    html = page.read_text(encoding="utf-8")
    if DATA_TAG not in html:
        raise SystemExit(f"ERROR: {page} does not contain {DATA_TAG!r}")
    data = (page.parent / "data/repositories.js").read_text(encoding="utf-8")
    if "</script" in data.lower():
        raise SystemExit("ERROR: data file contains '</script' and cannot be inlined as-is")
    html = html.replace(DATA_TAG, "<script>\n" + data + "</script>")

    head = re.search(r"<head\b[^>]*>(.*?)</head>", html, re.S)
    body = re.search(r"<body\b[^>]*>(.*?)</body>", html, re.S)
    if not head or not body:
        raise SystemExit(f"ERROR: could not find <head>/<body> in {page}")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(head.group(1).strip() + "\n" + body.group(1).strip() + "\n", encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size:,} bytes, data inlined, skeleton stripped)",
          file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())

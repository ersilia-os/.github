#!/usr/bin/env python3
"""build.py — assemble index.html from src/index.src.html.

Thin wrapper around apply_theme.py from Ersilia's `html-formatting` skill, run in
retrofit mode: it swaps in the canonical Ersilia <head> (ersilia.css inlined plus
the inline-SVG target favicon) and hoists the source file's own <style> so it
cascades after the theme.

    python scripts/build.py
    python scripts/build.py --shot     # also refresh og-image.png, the social preview
    python scripts/build.py --skill /path/to/ersilia-skills/skills/html-formatting

Edit src/index.src.html, then rebuild. Re-running after the skill's theme changes
is how this page picks up a house-style update.

Standard library only.
"""

from __future__ import annotations

import argparse
import re
import runpy
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SKILL = Path.home() / "Documents/GitHub/ersilia-skills/skills/html-formatting"

TITLE = "Search repositories in the Ersilia ecosystem"
SOURCE_URL = "https://github.com/ersilia-os/.github/tree/main/repository-browser"

# Social preview. The URLs are hard-coded and absolute because that is the only form a
# social crawler can use: LinkedIn fetches og:image from its own servers, with no page
# context to resolve a relative path against. This repo is served from a Pages sub-path
# (no CNAME), so the site root includes /.github/.
SITE_URL = "https://ersilia-os.github.io/.github/"
OG_IMAGE = SITE_URL + "og-image.png"
DESCRIPTION = (
    "Search, filter and browse every repository in Ersilia's open-source ecosystem — "
    "models, packages, apps, analyses and workshops."
)
OG_IMAGE_ALT = (
    "The Ersilia repository browser: a searchable, filterable table of the "
    "organisation's open-source repositories."
)
# 1.4x rather than a true 1:1 viewport crop — LinkedIn renders the card a few hundred
# pixels wide, where 13px table text is unreadable. See make_og_image.py --zoom.
OG_ZOOM = 1.4
# The card geometry, single-sourced: these feed both make_og_image.py and the declared
# og:image:width/height, so the tags can never disagree with the PNG on disk.
OG_CARD = (1200, 630)  # 1.91:1, what every platform crops to
OG_RETINA = 2
OG_IMAGE_PATH = ROOT / "og-image.png"
OG_IMAGE_SIZE = f"{OG_CARD[0] * OG_RETINA}x{OG_CARD[1] * OG_RETINA}"


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
    p.add_argument(
        "--shot",
        action="store_true",
        help="also regenerate og-image.png, the social preview card, by screenshotting the "
        "built page with headless Chrome. Opt-in: the daily data refresh runs in CI with no "
        "browser, and the card only goes stale when the page's design changes, not its data.",
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
        "--description", DESCRIPTION,
        "--url", SITE_URL,
        "--og-image", OG_IMAGE,
        "--og-image-alt", OG_IMAGE_ALT,
        # A crawler lays the card out from these before it has fetched the image, so they
        # must describe the PNG that --shot actually writes, not the CSS card size.
        "--og-image-size", OG_IMAGE_SIZE,
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

    if args.shot:
        rc = make_og_image(skill, Path(args.out), OG_IMAGE_PATH)
        if rc:
            return rc
        actual = png_size(OG_IMAGE_PATH)
        if actual != OG_IMAGE_SIZE:
            print(
                f"WARNING: og-image.png is {actual} but the page declares {OG_IMAGE_SIZE}; "
                "fix OG_CARD/OG_RETINA and rebuild.",
                file=sys.stderr,
            )
    if args.artifact:
        inline_data(Path(args.out), Path(args.artifact))
    return 0


def png_size(path: Path) -> str:
    """Read "WxH" out of a PNG's IHDR chunk (bytes 16-24). No Pillow needed."""
    try:
        header = path.read_bytes()[:24]
        if header[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError("not a PNG")
        width, height = struct.unpack(">II", header[16:24])
        return f"{width}x{height}"
    except (OSError, ValueError, struct.error) as exc:
        return f"unreadable ({exc})"


def make_og_image(skill: Path, page: Path, out: Path) -> int:
    """Screenshot the built page into og-image.png via the skill's make_og_image.py."""
    script = skill / "scripts/make_og_image.py"
    if not script.exists():
        print(f"ERROR: make_og_image.py not found at {script}", file=sys.stderr)
        return 2
    sys.argv = [
        str(script),
        str(page),
        "--out", str(out),
        "--zoom", str(OG_ZOOM),
        "--width", str(OG_CARD[0]),
        "--height", str(OG_CARD[1]),
        "--retina", str(OG_RETINA),
    ]
    try:
        runpy.run_path(str(script), run_name="__main__")
    except SystemExit as exc:
        if exc.code:
            return int(exc.code)
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

    The Open Graph tags ride along into the artifact. They are inert there — the
    browser never fetches og:image, so the Artifact CSP is not involved — and they
    keep pointing at the hosted site, which is the canonical home of this page.
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

#!/usr/bin/env python3
"""fetch_repositories.py — refresh the browser's data from Airtable.

Reads the Repositories table of the Ersilia Content base and writes two files:

  data/repositories.js    window.ERSILIA_REPOS = {...}   ← what index.html loads
  data/repositories.json  the same payload, for anything else that wants it

The page loads a .js file rather than fetching the .json because fetch() on a
local file is blocked by CORS: a <script src> works identically from file:// and
from GitHub Pages, so the browser needs no server.

Usage:
    export AIRTABLE_API_KEY=pat...
    python scripts/fetch_repositories.py --date 2026-08-11

The snapshot date is passed in rather than read from the clock (repo convention:
these scripts never call datetime.now(), so a run is reproducible).

Private repositories are included by default and flagged in the page. Pass
--exclude-private to drop them from the data entirely — worth doing if this site
is published somewhere the names and descriptions of private work should not go.

Standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE_ID = "app1iYv78K6xbHkmL"  # Ersilia Content
TABLE_ID = "tbluZtI3W9pseCSPH"  # Repositories
API_ROOT = "https://api.airtable.com/v0"

# Airtable field IDs → the keys the page uses. Field IDs are stable across
# renames; field *names* are not, so we address by ID.
FIELDS = {
    "fldtnOlLM2rqUZQpr": "name",  # primary field: the repo slug
    "fldYNOnc9KYHcQb7B": "title",
    "fldBrXumaKuyUcgnH": "description",
    "fldvMLxQibv9YiJ1t": "url",  # formula: github.com/ersilia-os/<name>
    "fldbqy6izSeIK4L7M": "status",  # multi-select
    "fldaYAL5URJa3gnRB": "type",  # multi-select
    "fldXhoqkmBs6ZRhnn": "visibility",  # single select: Public | Private
    "fldBH2270474FY9XW": "created",  # date
    "fldLxYAsHn1MDlOh4": "projects",  # linked records
}

LIST_KEYS = ("status", "type", "projects")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def fetch_page(token: str, offset: str | None) -> dict:
    params = {"pageSize": "100", "returnFieldsByFieldId": "true"}
    if offset:
        params["offset"] = offset
    url = f"{API_ROOT}/{BASE_ID}/{TABLE_ID}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:  # surface Airtable's own message
        body = exc.read().decode("utf-8", "replace")
        raise SystemExit(f"Airtable returned {exc.code}: {body}") from exc


def fetch_all(token: str) -> list[dict]:
    records: list[dict] = []
    offset = None
    while True:
        page = fetch_page(token, offset)
        records.extend(page.get("records", []))
        offset = page.get("offset")
        if not offset:
            return records


def normalise(record: dict) -> dict:
    """Flatten one Airtable record to the page's shape.

    Multi-selects and linked records come back either as plain strings (the REST
    API) or as {id, name} objects (the MCP connector); accept both. Missing cells
    are omitted by Airtable entirely, so every key gets an explicit empty default
    — the page must never see `undefined`.
    """
    raw = record.get("fields", {})
    out: dict[str, object] = {key: ([] if key in LIST_KEYS else "") for key in FIELDS.values()}
    for field_id, key in FIELDS.items():
        if field_id not in raw:
            continue
        value = raw[field_id]
        if key in LIST_KEYS:
            items = value if isinstance(value, list) else [value]
            out[key] = [i.get("name", "") if isinstance(i, dict) else str(i) for i in items if i]
        elif isinstance(value, dict):  # single select as an object
            out[key] = value.get("name", "")
        else:
            out[key] = value if value is not None else ""
    return out


def build_payload(records: list[dict], snapshot: str, exclude_private: bool) -> dict:
    repos = [normalise(r) for r in records]
    repos = [r for r in repos if r["name"]]
    if exclude_private:
        repos = [r for r in repos if r["visibility"] != "Private"]
    repos.sort(key=lambda r: str(r["name"]).lower())
    return {
        "snapshot": snapshot,
        "count": len(repos),
        "source": {
            "base": "Ersilia Content",
            "baseId": BASE_ID,
            "table": "Repositories",
            "tableId": TABLE_ID,
            "note": "Maintained by a nightly cron action against the ersilia-os GitHub organisation.",
        },
        "repositories": repos,
    }


def write_outputs(payload: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    blob = json.dumps(payload, indent=2, ensure_ascii=False)
    (out_dir / "repositories.json").write_text(blob + "\n", encoding="utf-8")
    (out_dir / "repositories.js").write_text(
        "/* Generated by scripts/fetch_repositories.py — do not edit by hand.\n"
        "   Loaded via <script src> rather than fetch() so the page also works from file://. */\n"
        "window.ERSILIA_REPOS = " + blob + ";\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--date", required=True, help="snapshot date, YYYY-MM-DD (shown in the page)")
    p.add_argument(
        "--out-dir",
        default=str(Path(__file__).resolve().parent.parent / "data"),
        help="where to write repositories.js / .json (default: ../data)",
    )
    p.add_argument(
        "--exclude-private",
        action="store_true",
        help="drop private repositories from the data entirely",
    )
    args = p.parse_args(argv)

    if not DATE_RE.match(args.date):
        p.error("--date must be YYYY-MM-DD")

    token = os.environ.get("AIRTABLE_API_KEY") or os.environ.get("AIRTABLE_TOKEN")
    if not token:
        p.error("set AIRTABLE_API_KEY (a personal access token with data.records:read on the base)")

    records = fetch_all(token)
    payload = build_payload(records, args.date, args.exclude_private)
    write_outputs(payload, Path(args.out_dir).expanduser().resolve())

    private = sum(1 for r in payload["repositories"] if r["visibility"] == "Private")
    print(
        f"wrote {payload['count']} repositories "
        f"({payload['count'] - private} public, {private} private) to {args.out_dir}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

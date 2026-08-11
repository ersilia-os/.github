#!/usr/bin/env python3
"""apply_refresh.py — decide whether a freshly fetched snapshot should replace the committed one.

`fetch_repositories.py` writes into a staging directory; this compares that
against what is committed and copies it over only if the repository data actually
changed. Two problems it exists to solve:

1. **The snapshot date changes every day even when nothing else does.** It is
   stamped from `--date`, so a naive `git diff` is always dirty and the scheduled
   job would land 365 pointless commits a year in the organisation's most visible
   repository. Only the `repositories` array is compared.

2. **A partial response would silently gut the site.** An Airtable hiccup mid
   pagination yields a valid-looking file with too few records. Anything below
   `--min-ratio` of the committed count is refused rather than committed.

Exits non-zero on a refusal, so the workflow fails loudly instead of shipping a
truncated table. Prints `changed=true|false` and, under Actions, writes it to
`$GITHUB_OUTPUT` and a human summary to `$GITHUB_STEP_SUMMARY`.

Standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

RECORD_ID_RE = re.compile(r"^rec[A-Za-z0-9]{14}$")


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as exc:
        sys.exit(f"REFUSED: {path} is not valid JSON ({exc})")


def emit(changed: bool, summary_lines: list[str]) -> None:
    print(f"changed={'true' if changed else 'false'}")
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(f"changed={'true' if changed else 'false'}\n")
    step = os.environ.get("GITHUB_STEP_SUMMARY")
    if step and summary_lines:
        with open(step, "a", encoding="utf-8") as fh:
            fh.write("\n".join(summary_lines) + "\n")
    for line in summary_lines:
        print(line)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--staged", required=True, help="directory fetch_repositories.py wrote to")
    p.add_argument("--dest", required=True, help="the committed data directory")
    p.add_argument("--min-ratio", type=float, default=0.9,
                   help="refuse if the new record count falls below this fraction "
                        "of the committed one (default: 0.9)")
    args = p.parse_args(argv)

    staged_dir, dest_dir = Path(args.staged), Path(args.dest)
    new = load(staged_dir / "repositories.json")
    old = load(dest_dir / "repositories.json")

    new_repos = new.get("repositories")
    if not isinstance(new_repos, list) or not new_repos:
        sys.exit("REFUSED: the fetched payload has no repositories")
    if new.get("count") != len(new_repos):
        sys.exit(f"REFUSED: count says {new.get('count')} but there are {len(new_repos)} records")

    # A field-level regression the count check cannot see. The REST API returns
    # linked records as record IDs, and a fetch that forgets to resolve them
    # produces a full-size, valid-looking payload whose Project column reads
    # `recTJG9wk4nf0YB2t`. That shipped once; it does not ship again.
    unresolved = [r["name"] for r in new_repos
                  if any(RECORD_ID_RE.match(str(p)) for p in r.get("projects") or [])]
    if unresolved:
        sys.exit(
            f"REFUSED: {len(unresolved)} records have unresolved linked-record IDs in "
            f"'projects' (e.g. {unresolved[0]}). fetch_repositories.py must resolve them to "
            f"names via link_names()."
        )

    old_repos = old.get("repositories") or []
    if old_repos and len(new_repos) < len(old_repos) * args.min_ratio:
        sys.exit(
            f"REFUSED: {len(new_repos)} records is below {args.min_ratio:g}× the committed "
            f"{len(old_repos)} — this looks like a truncated response, not a real deletion. "
            f"Re-run manually, or lower --min-ratio if the drop is genuine."
        )

    # Only the data decides; the snapshot date on its own is not a change.
    if new_repos == old_repos:
        emit(False, [f"No change — {len(new_repos)} repositories, identical to the committed data. "
                     "Nothing committed."])
        return 0

    old_names = {r.get("name") for r in old_repos}
    new_names = {r.get("name") for r in new_repos}
    added, removed = sorted(new_names - old_names), sorted(old_names - new_names)
    edited = sorted(
        r.get("name") for r in new_repos
        if r.get("name") in old_names
        and r != next(o for o in old_repos if o.get("name") == r.get("name"))
    )

    lines = [f"### Data refreshed — {len(new_repos)} repositories "
             f"(was {len(old_repos)})", ""]
    for label, names in (("Added", added), ("Removed", removed), ("Edited", edited)):
        if names:
            shown = ", ".join(f"`{n}`" for n in names[:15])
            more = f" … and {len(names) - 15} more" if len(names) > 15 else ""
            lines.append(f"- **{label} ({len(names)})**: {shown}{more}")

    dest_dir.mkdir(parents=True, exist_ok=True)
    for name in ("repositories.json", "repositories.js"):
        shutil.copyfile(staged_dir / name, dest_dir / name)

    emit(True, lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

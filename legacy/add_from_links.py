#!/usr/bin/env python3
"""
add_from_links.py — turn job-posting URLs into companies.yaml entries.

Paste in one or more job links (from Greenhouse, Lever, Ashby, etc.) and this
extracts the ATS platform and company slug straight from the URL — no network
call needed — and adds any new company to companies.yaml.

The ATS and slug live in the URL itself, e.g.:
  https://boards.greenhouse.io/mollie/jobs/123   -> greenhouse, slug=mollie
  https://jobs.lever.co/personio/abc-def         -> lever, slug=personio
  https://jobs.ashbyhq.com/miro/uuid             -> ashby, slug=miro

Usage:
    python add_from_links.py URL [URL ...]      # add from links on the command line
    python add_from_links.py --file links.txt   # one URL per line in a file
    python add_from_links.py --dry-run URL       # show what it found, write nothing

After adding, run scan.py or report.py as usual — the new companies are included
automatically. Their tier defaults to "Other" so you can tell them apart from
your original hand-picked target list.
"""

import argparse
import re
import sys
from urllib.parse import urlparse

import yaml

COMPANIES_FILE = "companies.yaml"


def parse_url(url: str):
    """Return (ats, slug) extracted from a job-posting URL, or (None, None)."""
    url = url.strip()
    if not url:
        return None, None
    p = urlparse(url if "://" in url else "https://" + url)
    host = p.netloc.lower()
    parts = [seg for seg in p.path.split("/") if seg]

    # Greenhouse: boards.greenhouse.io/{slug}/jobs/...  OR
    #             job-boards.greenhouse.io/{slug}/jobs/...  OR
    #             boards.eu.greenhouse.io/{slug}/...
    if "greenhouse.io" in host:
        if parts:
            return "greenhouse", parts[0]

    # Lever: jobs.lever.co/{slug}/{id}
    if "lever.co" in host:
        if parts:
            return "lever", parts[0]

    # Ashby: jobs.ashbyhq.com/{slug}/{id}
    if "ashbyhq.com" in host:
        if parts:
            return "ashby", parts[0]

    # SmartRecruiters: jobs.smartrecruiters.com/{slug}/{id} OR
    #                  careers.smartrecruiters.com/{slug}
    if "smartrecruiters.com" in host:
        if parts:
            return "smartrecruiters", parts[0]

    # Recruitee: {slug}.recruitee.com/o/...
    if "recruitee.com" in host:
        sub = host.split(".")[0]
        if sub and sub != "recruitee":
            return "recruitee", sub

    # Workable: apply.workable.com/{slug}/... OR {slug}.workable.com
    if "workable.com" in host:
        if host.startswith("apply.") and parts:
            return "workable", parts[0]
        sub = host.split(".")[0]
        if sub not in ("apply", "www", "workable"):
            return "workable", sub

    # Personio: {slug}.jobs.personio.de/... OR {slug}.jobs.personio.com
    if "personio.de" in host or "personio.com" in host:
        sub = host.split(".")[0]
        if sub and sub != "jobs":
            return "personio", sub

    return None, None


def guess_name(slug: str) -> str:
    """Human-friendly company name guess from a slug. You can edit it after."""
    # split on hyphens/underscores, title-case
    words = re.split(r"[-_]+", slug)
    return " ".join(w.capitalize() for w in words if w)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urls", nargs="*", help="job posting URLs")
    ap.add_argument("--file", help="text file with one URL per line")
    ap.add_argument("--dry-run", action="store_true", help="show findings, don't write")
    args = ap.parse_args()

    urls = list(args.urls)
    if args.file:
        with open(args.file) as f:
            urls += [line.strip() for line in f if line.strip() and not line.startswith("#")]

    if not urls:
        print("No URLs given. Pass them as arguments or with --file links.txt", file=sys.stderr)
        return 1

    with open(COMPANIES_FILE) as f:
        data = yaml.safe_load(f)
    companies = data["companies"]

    # index existing entries by (ats, slug) so we never add a duplicate
    existing = {}
    for c in companies:
        if c.get("ats") and c.get("slug"):
            existing[(c["ats"], c["slug"].lower())] = c["name"]
    existing_names = {c["name"].lower() for c in companies}

    added = []
    skipped_dupe = []
    unparseable = []

    for url in urls:
        ats, slug = parse_url(url)
        if not ats:
            unparseable.append(url)
            continue
        key = (ats, slug.lower())
        if key in existing:
            skipped_dupe.append((url, existing[key]))
            continue

        name = guess_name(slug)
        # avoid name clash with an existing differently-sourced entry
        display_name = name
        n = 2
        while display_name.lower() in existing_names:
            display_name = f"{name} ({ats})"
            break

        entry = {
            "name": display_name,
            "city": "",
            "country": "",
            "tier": "Other",
            "ats": ats,
            "slug": slug,
        }
        companies.append(entry)
        existing[key] = display_name
        existing_names.add(display_name.lower())
        added.append((url, display_name, ats, slug))

    # ---- report
    if added:
        print(f"Added {len(added)} new " + ("company" if len(added) == 1 else "companies") + ":")
        for url, name, ats, slug in added:
            print(f"  {name:28} {ats:14} slug={slug}")
        print("  (names are guesses from the URL — edit companies.yaml if any look off)")
    if skipped_dupe:
        print(f"\nAlready in the list ({len(skipped_dupe)}), skipped:")
        for url, name in skipped_dupe:
            print(f"  {name}")
    if unparseable:
        print(f"\nCouldn't read these {len(unparseable)} — unknown or custom ATS:")
        for url in unparseable:
            print(f"  {url}")
        print("  These use a job system the scanner can't read (often Workday or a")
        print("  custom careers site). Add them by hand only if you can find a")
        print("  greenhouse/lever/ashby/personio link for the same company.")

    if args.dry_run:
        print("\n(dry run — companies.yaml not modified)")
        return 0

    if added:
        with open(COMPANIES_FILE, "w") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, default_flow_style=False)
        print(f"\nWrote {COMPANIES_FILE}. Run report.py to include them next time.")
    else:
        print("\nNothing new to add.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

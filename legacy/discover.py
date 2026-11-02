#!/usr/bin/env python3
"""
discover.py — work out which ATS platform each target company uses.

Run once. Probes each known job-board API with slug guesses derived from the
company name, and writes any hits back into companies.yaml.

IMPORTANT: slug guessing can land on a DIFFERENT company with a similar name.
This script prints the company/board name returned by each API next to your
target name. Check those by eye before trusting the config — a wrong slug means
silently scanning the wrong company's jobs forever.

Usage:
    python discover.py                  # probe every company with ats: null
    python discover.py --all            # re-probe everything, including known ones
    python discover.py --company Mollie # probe one company
    python discover.py --dry-run        # print findings, don't write the file
"""

import argparse
import re
import sys
import time
import xml.etree.ElementTree as ET

import requests
import yaml

TIMEOUT = 12
DELAY = 0.4
UA = {"User-Agent": "personal-job-search/1.0"}

COMPANIES_FILE = "companies.yaml"


# --------------------------------------------------------------- slug guessing
def slug_candidates(name: str) -> list[str]:
    """Generate plausible board slugs from a company name, most likely first."""
    base = name.lower().strip()
    base = base.replace("&", "and")
    # strip common suffixes and parentheticals
    base = re.sub(r"\(.*?\)", "", base)
    base = re.sub(r"\b(gmbh|bv|b\.v\.|inc|ltd|se|ag|nv|n\.v\.)\b", "", base)
    base = base.strip()

    no_punct = re.sub(r"[^a-z0-9\s-]", "", base)
    squashed = re.sub(r"[\s-]+", "", no_punct)
    hyphenated = re.sub(r"\s+", "-", no_punct).strip("-")
    first_word = no_punct.split()[0] if no_punct.split() else squashed

    out = []
    for c in (squashed, hyphenated, first_word):
        if c and c not in out:
            out.append(c)
    return out


# --------------------------------------------------------------- probes
# Each probe returns (n_jobs, board_name) on success, or None.
# board_name is what the API thinks it is — used to catch wrong-company hits.

def probe_greenhouse(slug):
    r = requests.get(
        f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs",
        timeout=TIMEOUT, headers=UA,
    )
    if r.status_code != 200:
        return None
    jobs = r.json().get("jobs", [])
    if not jobs:
        return None
    return len(jobs), slug


def probe_lever(slug):
    r = requests.get(
        f"https://api.lever.co/v0/postings/{slug}?mode=json",
        timeout=TIMEOUT, headers=UA,
    )
    if r.status_code != 200:
        return None
    jobs = r.json()
    if not isinstance(jobs, list) or not jobs:
        return None
    return len(jobs), slug


def probe_ashby(slug):
    r = requests.get(
        f"https://api.ashbyhq.com/posting-api/job-board/{slug}",
        timeout=TIMEOUT, headers=UA,
    )
    if r.status_code != 200:
        return None
    data = r.json()
    jobs = data.get("jobs", [])
    if not jobs:
        return None
    return len(jobs), data.get("name", slug)


def probe_smartrecruiters(slug):
    r = requests.get(
        f"https://api.smartrecruiters.com/v1/companies/{slug}/postings",
        timeout=TIMEOUT, headers=UA,
    )
    if r.status_code != 200:
        return None
    data = r.json()
    jobs = data.get("content", [])
    if not jobs:
        return None
    return data.get("totalFound", len(jobs)), slug


def probe_recruitee(slug):
    r = requests.get(
        f"https://{slug}.recruitee.com/api/offers/",
        timeout=TIMEOUT, headers=UA,
    )
    if r.status_code != 200:
        return None
    jobs = r.json().get("offers", [])
    if not jobs:
        return None
    return len(jobs), slug


def probe_workable(slug):
    r = requests.get(
        f"https://apply.workable.com/api/v1/widget/accounts/{slug}?details=true",
        timeout=TIMEOUT, headers=UA,
    )
    if r.status_code != 200:
        return None
    data = r.json()
    jobs = data.get("jobs", [])
    if not jobs:
        return None
    return len(jobs), data.get("name", slug)


def probe_personio(slug):
    r = requests.get(
        f"https://{slug}.jobs.personio.de/xml",
        timeout=TIMEOUT, headers=UA,
    )
    if r.status_code != 200 or not r.content.strip().startswith(b"<"):
        return None
    try:
        root = ET.fromstring(r.content)
    except ET.ParseError:
        return None
    positions = root.findall(".//position")
    if not positions:
        return None
    return len(positions), slug


PROBES = {
    "greenhouse": probe_greenhouse,
    "lever": probe_lever,
    "ashby": probe_ashby,
    "smartrecruiters": probe_smartrecruiters,
    "recruitee": probe_recruitee,
    "workable": probe_workable,
    "personio": probe_personio,
}


# --------------------------------------------------------------- main
def discover_one(name: str) -> list[dict]:
    """Probe every slug/ATS combination and return ALL hits, best first.

    Each hit: {ats, slug, n_jobs, board_name}. Returns [] if nothing found.
    Unlike a first-match approach, this collects everything so a 1-job name
    collision can't hide the real 300-job board that would be probed later.
    """
    hits = []
    for slug in slug_candidates(name):
        for ats, probe in PROBES.items():
            try:
                result = probe(slug)
            except requests.RequestException:
                continue
            except Exception:
                continue
            finally:
                time.sleep(DELAY)
            if result:
                n_jobs, board_name = result
                hits.append({
                    "ats": ats, "slug": slug,
                    "n_jobs": n_jobs, "board_name": board_name,
                })
    # Rank hits: prefer ones whose board name matches the company (not a
    # collision), then by job count. This stops a larger same-name company
    # from outranking the real (smaller) board.
    hits.sort(
        key=lambda h: (name_matches_board(name, h["board_name"]), h["n_jobs"]),
        reverse=True,
    )
    return hits


def name_matches_board(target: str, board: str) -> bool:
    """Does the API's board name closely resemble the target company name?

    Deliberately strict: a board called 'SalesForce Consulting GmbH' should NOT
    count as a clean match for 'Salesforce', because prefix collisions are a
    common failure mode. We require near-equality of the cleaned names, or the
    board to be a short extension of the target (to tolerate 'Adyen N.V.').
    """
    if not board:
        return True  # nothing to compare; don't warn on this signal alone
    t = re.sub(r"[^a-z0-9]", "", target.lower())
    b = re.sub(r"[^a-z0-9]", "", board.lower())
    if not t or not b:
        return True
    if t == b:
        return True
    # tolerate a small legal-suffix extension: 'adyen' vs 'adyennv'
    longer, shorter = (b, t) if len(b) >= len(t) else (t, b)
    if longer.startswith(shorter) and (len(longer) - len(shorter)) <= 3:
        return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="re-probe companies that already have an ats set")
    ap.add_argument("--company", help="probe a single company by name")
    ap.add_argument("--dry-run", action="store_true", help="print findings without writing companies.yaml")
    args = ap.parse_args()

    with open(COMPANIES_FILE) as f:
        data = yaml.safe_load(f)
    companies = data["companies"]

    targets = companies
    if args.company:
        targets = [c for c in companies if c["name"].lower() == args.company.lower()]
        if not targets:
            print(f"No company named {args.company!r} in {COMPANIES_FILE}", file=sys.stderr)
            return 1
    elif not args.all:
        targets = [c for c in companies if not c.get("ats")]

    print(f"Probing {len(targets)} companies...\n")
    found = 0
    check_manually = []
    low_confidence = []   # names where the best hit looks doubtful

    LOW_JOB_THRESHOLD = 5   # a real target company rarely has <5 openings;
                            # a handful of jobs usually means a name collision

    for c in targets:
        name = c["name"]
        hits = discover_one(name)

        if not hits:
            check_manually.append(name)
            print(f"  {name:32} -- no public board found")
            continue

        best = hits[0]
        ats, slug, n_jobs, board_name = best["ats"], best["slug"], best["n_jobs"], best["board_name"]
        c["ats"] = ats
        c["slug"] = slug
        found += 1

        # confidence signals
        flags = []
        if not name_matches_board(name, board_name):
            flags.append(f"API name={board_name!r}")
        if n_jobs < LOW_JOB_THRESHOLD:
            flags.append(f"only {n_jobs} job(s)")

        warn = ""
        if flags:
            warn = "   <-- CHECK: " + ", ".join(flags)
            low_confidence.append(name)

        print(f"  {name:32} {ats:16} slug={slug:20} {n_jobs:4} jobs{warn}")

        # if there were multiple distinct hits, show the runners-up — the real
        # board may be a lower-job alternative on a different slug/ATS
        others = [h for h in hits[1:] if (h["ats"], h["slug"]) != (ats, slug)]
        if others and flags:
            for h in others[:3]:
                print(f"       alt: {h['ats']} slug={h['slug']} ({h['n_jobs']} jobs, {h['board_name']!r})")

    print(f"\nFound: {found}/{len(targets)}")

    if low_confidence:
        print(f"\nLOW CONFIDENCE — verify these {len(low_confidence)} by hand before trusting:")
        for n in low_confidence:
            print(f"  - {n}")
        print("  A major target company showing only a few jobs, or a board name that")
        print("  doesn't match, is almost always a same-name slug collision.")
        print("  Open the company's real careers page, read the URL, and correct the")
        print("  ats/slug in companies.yaml. If none of the alternatives above is right,")
        print("  set both back to null so scan.py skips it instead of scanning the wrong jobs.")

    if check_manually:
        print(f"\nNo board found for {len(check_manually)} (likely Workday or a custom site):")
        for n in check_manually:
            print(f"  - {n}")
        print("\n  Open any posting on their careers page and read the URL.")
        print("  boards.greenhouse.io/X -> ats: greenhouse, slug: X")
        print("  jobs.lever.co/X        -> ats: lever, slug: X")
        print("  X.jobs.personio.de     -> ats: personio, slug: X")
        print("  Then fill in companies.yaml manually. Leave the rest as null.")

    if args.dry_run:
        print("\n(dry run — companies.yaml not modified)")
        return 0

    with open(COMPANIES_FILE, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, default_flow_style=False)
    print(f"\nWrote {COMPANIES_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

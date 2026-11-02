#!/usr/bin/env python3
"""
scan.py — check target companies' job boards for postings matching my search terms.

No scoring, no ranking. Just: does something matching exist, and where is it.

Usage:
    python scan.py                    # scan all configured companies
    python scan.py --company Mollie   # one company
    python scan.py --new-only         # only postings not seen on a previous run
    python scan.py --no-filter        # show every posting (useful for tuning terms)
"""

import argparse
import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from html import unescape

import requests
import yaml

TIMEOUT = 15
DELAY = 0.5
UA = {"User-Agent": "personal-job-search/1.0"}

COMPANIES_FILE = "companies.yaml"
TERMS_FILE = "search_terms.yaml"
SEEN_FILE = "state/seen.json"


# --------------------------------------------------------------- fetchers
# Each returns a list of {title, location, url}. Raises on transport errors.

def strip_html(text: str) -> str:
    if not text:
        return ""
    out = []
    depth = 0
    for ch in text:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth = max(0, depth - 1)
        elif depth == 0:
            out.append(ch)
    return unescape("".join(out)).strip()


def fetch_greenhouse(slug):
    r = requests.get(
        f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs",
        timeout=TIMEOUT, headers=UA,
    )
    r.raise_for_status()
    return [
        {
            "title": j.get("title", ""),
            "location": (j.get("location") or {}).get("name", ""),
            "url": j.get("absolute_url", ""),
        }
        for j in r.json().get("jobs", [])
    ]


def fetch_lever(slug):
    r = requests.get(
        f"https://api.lever.co/v0/postings/{slug}?mode=json",
        timeout=TIMEOUT, headers=UA,
    )
    r.raise_for_status()
    return [
        {
            "title": j.get("text", ""),
            "location": (j.get("categories") or {}).get("location", "") or "",
            "url": j.get("hostedUrl", ""),
        }
        for j in r.json()
    ]


def fetch_ashby(slug):
    r = requests.get(
        f"https://api.ashbyhq.com/posting-api/job-board/{slug}",
        timeout=TIMEOUT, headers=UA,
    )
    r.raise_for_status()
    return [
        {
            "title": j.get("title", ""),
            "location": j.get("location", "") or "",
            "url": j.get("jobUrl", ""),
        }
        for j in r.json().get("jobs", [])
    ]


def fetch_smartrecruiters(slug):
    out = []
    offset = 0
    while True:
        r = requests.get(
            f"https://api.smartrecruiters.com/v1/companies/{slug}/postings",
            params={"limit": 100, "offset": offset},
            timeout=TIMEOUT, headers=UA,
        )
        r.raise_for_status()
        data = r.json()
        content = data.get("content", [])
        for j in content:
            loc = j.get("location") or {}
            city = loc.get("city", "")
            country = loc.get("country", "")
            out.append({
                "title": j.get("name", ""),
                "location": ", ".join(x for x in (city, country.upper()) if x),
                "url": f"https://jobs.smartrecruiters.com/{slug}/{j.get('id','')}",
            })
        offset += len(content)
        if not content or offset >= data.get("totalFound", 0):
            break
        time.sleep(0.2)
    return out


def fetch_recruitee(slug):
    r = requests.get(
        f"https://{slug}.recruitee.com/api/offers/",
        timeout=TIMEOUT, headers=UA,
    )
    r.raise_for_status()
    return [
        {
            "title": j.get("title", ""),
            "location": ", ".join(x for x in (j.get("city"), j.get("country")) if x),
            "url": j.get("careers_url") or j.get("careers_apply_url", ""),
        }
        for j in r.json().get("offers", [])
    ]


def fetch_workable(slug):
    r = requests.get(
        f"https://apply.workable.com/api/v1/widget/accounts/{slug}?details=true",
        timeout=TIMEOUT, headers=UA,
    )
    r.raise_for_status()
    return [
        {
            "title": j.get("title", ""),
            "location": j.get("location", "") or "",
            "url": j.get("url") or j.get("application_url", ""),
        }
        for j in r.json().get("jobs", [])
    ]


def fetch_personio(slug):
    r = requests.get(
        f"https://{slug}.jobs.personio.de/xml",
        timeout=TIMEOUT, headers=UA,
    )
    r.raise_for_status()
    root = ET.fromstring(r.content)
    out = []
    for pos in root.findall(".//position"):
        def text(tag):
            el = pos.find(tag)
            return (el.text or "").strip() if el is not None and el.text else ""
        pid = text("id")
        out.append({
            "title": text("name"),
            "location": text("office"),
            "url": f"https://{slug}.jobs.personio.de/job/{pid}" if pid else f"https://{slug}.jobs.personio.de/",
        })
    return out


FETCHERS = {
    "greenhouse": fetch_greenhouse,
    "lever": fetch_lever,
    "ashby": fetch_ashby,
    "smartrecruiters": fetch_smartrecruiters,
    "recruitee": fetch_recruitee,
    "workable": fetch_workable,
    "personio": fetch_personio,
}


# --------------------------------------------------------------- filtering
def matches(posting: dict, terms: dict) -> bool:
    title = (posting.get("title") or "").lower()
    location = (posting.get("location") or "").lower()

    if not any(t.lower() in title for t in terms.get("include_titles", [])):
        return False
    if any(t.lower() in title for t in terms.get("exclude_titles", [])):
        return False
    locs = terms.get("locations", [])
    if locs and not any(l.lower() in location for l in locs):
        return False
    return True


# --------------------------------------------------------------- seen state
def load_seen() -> set:
    if not os.path.exists(SEEN_FILE):
        return set()
    try:
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    except (json.JSONDecodeError, OSError):
        return set()


def save_seen(urls: set):
    os.makedirs(os.path.dirname(SEEN_FILE), exist_ok=True)
    with open(SEEN_FILE, "w") as f:
        json.dump(sorted(urls), f, indent=1)


# --------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--company", help="scan a single company by name")
    ap.add_argument("--new-only", action="store_true", help="only show postings not seen before")
    ap.add_argument("--no-filter", action="store_true", help="show all postings (for tuning search terms)")
    args = ap.parse_args()

    with open(COMPANIES_FILE) as f:
        companies = yaml.safe_load(f)["companies"]
    with open(TERMS_FILE) as f:
        terms = yaml.safe_load(f)

    if args.company:
        companies = [c for c in companies if c["name"].lower() == args.company.lower()]
        if not companies:
            print(f"No company named {args.company!r}", file=sys.stderr)
            return 1

    configured = [c for c in companies if c.get("ats") and c.get("slug")]
    skipped = [c["name"] for c in companies if not (c.get("ats") and c.get("slug"))]

    seen = load_seen()
    results = {}
    errors = []
    total_fetched = 0

    for c in configured:
        name, ats, slug = c["name"], c["ats"], c["slug"]
        fetcher = FETCHERS.get(ats)
        if not fetcher:
            errors.append((name, f"unknown ats {ats!r}"))
            continue
        try:
            postings = fetcher(slug)
        except requests.HTTPError as e:
            errors.append((name, f"HTTP {e.response.status_code} — slug may have changed"))
            continue
        except requests.RequestException as e:
            errors.append((name, f"network error: {type(e).__name__}"))
            continue
        except (ET.ParseError, ValueError, KeyError) as e:
            errors.append((name, f"parse error: {type(e).__name__}"))
            continue
        finally:
            time.sleep(DELAY)

        total_fetched += len(postings)
        hits = postings if args.no_filter else [p for p in postings if matches(p, terms)]
        if args.new_only:
            hits = [p for p in hits if p["url"] not in seen]
        if hits:
            results[name] = hits

    # ------------------------------------------------------------- output
    n_matches = sum(len(v) for v in results.values())
    print(f"Scanned {len(configured)} companies — {total_fetched} postings — {n_matches} matches\n")

    for name in sorted(results):
        print(name.upper())
        for p in results[name]:
            flag = " [NEW]" if p["url"] not in seen else ""
            loc = p["location"] or "location not stated"
            print(f"  {p['title']} — {loc}{flag}")
            print(f"  {p['url']}")
        print()

    if not results:
        print("No matches.\n")
        print("If that seems wrong, run --no-filter to see everything being fetched,")
        print("then loosen the terms in search_terms.yaml.\n")

    if skipped:
        print(f"Skipped — no public job board API ({len(skipped)}). Check these manually:")
        print("  " + ", ".join(skipped) + "\n")

    if errors:
        print("Errors:")
        for name, msg in errors:
            print(f"  {name}: {msg}")
        print()

    # record everything seen this run, matched or not, so --new-only is meaningful
    all_urls = seen | {p["url"] for v in results.values() for p in v}
    save_seen(all_urls)

    return 0


if __name__ == "__main__":
    sys.exit(main())

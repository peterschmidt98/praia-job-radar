# Fixtures

One saved raw response per source, captured once from a real call and committed, so tests and `run.py --fixtures` never touch the network.

Expected files (the Replit Agent creates them while building each collector):

| File | Source |
|---|---|
| `greenhouse_<slug>.json`, `ashby_<slug>.json`, `recruitee_<slug>.json`, `smartrecruiters_<slug>.json` | company ATS boards |
| `indeed_<query>.json` | python-jobspy output, serialised |
| `adzuna_<query>.json` | Adzuna API response |
| `linkedin_apify_<search>.json` | Apify dataset items |
| `judge_<job_id>.json` | recorded Claude responses for the Judge tests |
| `pages/<domain>_open.html`, `pages/<domain>_closed.html` | live/closed pages for Verifier tests |

Strip anything personal (her name, email) before committing. Keep each file small: trim to ~20 postings.

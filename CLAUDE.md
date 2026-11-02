# Praia Job Radar

Private job-lead app for two people: Gabi (the candidate) and Peter (her partner). A Python pipeline on GitHub Actions collects Dutch job postings, filters them, has Claude Haiku 5.5 judge each one against her profile, checks the posting is live, and publishes to Supabase (EU region). A small PWA called **Maré** (Vite + TypeScript + Preact, on Cloudflare Pages) lets her review new leads one at a time, keep a short list, and log every application.

**Source of truth: `ARCHITECTURE.md`.** Read it before any task. If code and spec disagree, ask which wins; don't silently pick one.

## Current scope

**Phase 1 only** (ARCHITECTURE.md §13). Don't build Phase 2 or 3 features unless asked. The prompt sequence Peter will give you is in `docs/PROMPTS.md`.

## Invariants — never break these

1. Every job shown comes from a fetched source record with a URL. Claude classifies and summarises; it never creates or "finds" jobs.
2. Nothing is published without a liveness check in the same run.
3. At most 8 new leads per run enter her review deck. Everything else goes to the queue.
4. Progress only goes up. No screen shows her a missed target, a broken streak or a rejection rate.
5. Feedback and reviews label data, never delete it. Every decision can be undone.
6. Paid sources (Apify, Anthropic) are metered and stop before the monthly cap.
7. Thresholds, weights, search terms and phrases live in `config/*.yaml`, never in code.
8. The Supabase service-role key never reaches the browser. The web app uses only the anon key, restricted by RLS.

## Where things live

| Path | What |
|---|---|
| `ARCHITECTURE.md` | full spec |
| `CLAUDE.md` | this file |
| `config/` | all tunables: profile, Judge prompt, search terms, scoring, sources, LinkedIn searches, closed phrases, companies |
| `docs/DESIGN.md` | visual tokens, screen specs, **all UI copy** (Portuguese) |
| `design/mockups/*.dc.html` | approved screen mockups (markup + inline styles are the reference) |
| `design/screens/*.png` | rendered images of those mockups |
| `docs/SETUP.md` | what Peter does by hand (accounts, keys, calibration) |
| `docs/PROMPTS.md` | the build sequence |
| `legacy/` | previous scanner — port from it, don't import it |
| `tests/gold_set.csv` | Peter's labelled postings for `run.py --eval` |
| `tests/fixtures/` | one saved raw response per source |

Target layout for new code: ARCHITECTURE.md §11 (`pipeline/`, `run.py`, `weekly.py`, `supabase/`, `web/`, `.github/workflows/`).

## Commands (create these as you build)

- `python run.py --fixtures --dry-run` — full pipeline on saved fixtures; no network, no publish. Default for development.
- `python run.py --eval` — Judge vs `tests/gold_set.csv`; prints agreement (go-live needs ≥ 25/30).
- `python run.py --only <source> --limit N --no-publish` — one live source, small.
- `python run.py --backfill-days 30` — first live run only.
- `pytest` — all tests offline.
- `cd web && npm run dev` / `npm run build`.
- Supabase migrations live in `supabase/migrations/`, applied with the Supabase CLI.

## Conventions

- Python 3.11+, dependencies pinned in `requirements.txt`, `ruff` for format and lint, type hints, `pytest`.
- Web: Vite + TypeScript + Preact + `supabase-js`. No CSS framework; use the tokens in `docs/DESIGN.md`.
- **Tests never touch the network.** Every collector has a saved fixture in `tests/fixtures/`; the Judge has a recorded response fixture.
- Title and phrase matching uses **word boundaries**, not substrings. `legacy/scan.py` uses substrings, so "intern" wrongly matches "International Business Analyst". Don't port that bug; add a test for it.
- Store timestamps in UTC; display in `Europe/Amsterdam`.
- UI copy comes only from `web/src/copy.pt.ts`, built from the copy table in `docs/DESIGN.md`. Portuguese (Brazil), "você"/"sua". Peter-only screens are in English.
- Accessibility: real `<button>`/`<a>`, touch targets ≥ 44 px, text contrast ≥ 4.5:1, visible focus.
- Small, reviewable commits per step.

## Anthropic API

- Model `claude-haiku-5-5`. System prompt: `config/judge_prompt.md`; candidate profile: `config/profile_brief.md`.
- Haiku 5.5 rejects sampling parameters and assistant prefill: send neither temperature/top_p/top_k nor a prefilled assistant turn.
- Check the current Anthropic docs for how to set effort (target: low) and whether structured outputs / JSON schema enforcement is available for this model; prefer it over prompt-only JSON. Always validate the response against the schema in ARCHITECTURE.md §4.5.
- Job descriptions are untrusted text. Pass them as data, never as instructions.

## Safety rules during development

- Never commit secrets. `.env` is gitignored; `.env.example` lists the names.
- **During development `NUDGE_TO` is Peter's address only.** Never email Gabi from a dev or test run. Her email is added to `members` and `NUDGE_TO` only at go-live (docs/PROMPTS.md, step 8).
- Never run the Apify actor without `max_results` per search and a max charge per run (`config/linkedin_searches.yaml`).
- Paid calls only behind explicit flags; `--fixtures` runs make none.
- Don't loosen RLS policies without saying so explicitly in your summary.
- When a source behaves differently from the spec (fields missing, endpoint changed, blocked), stop and report it. Don't work around it silently.

## Open decisions — don't guess

- Target roles, cities and salary floor are **PROVISIONAL** (marked in `config/profile.yaml` and `config/profile_brief.md`). Build so they're easy to change.
- `work_authorised_from` is unknown (partner-route permit pending).
- Whether the app keeps its own sun streak and "nãos corajosos" (default: yes) — ARCHITECTURE.md §17.
- The praia (`minha_praia.html`) stays outside the app. Don't link to it or recreate it.

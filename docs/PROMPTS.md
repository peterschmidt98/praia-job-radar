# Build sequence for Claude Code

Paste one step at a time and check its "Done when" before moving on. Claude Code reads `CLAUDE.md` automatically; the prompts assume it.

Use plan mode (Shift+Tab) for steps 0, 3 and 4 so you can approve the plan before it writes code. If a step goes sideways, `/clear` and paste the step again with what went wrong.

| Step | What | Your setup first (docs/SETUP.md) |
|---|---|---|
| 0 | Orient, no code | 1 GitHub |
| 1 | Pipeline core, offline | — |
| 2 | Judge + accuracy test | 3 Anthropic, 8 Gold set |
| 3 | Database, verifier, ranking, publish | 2 Supabase |
| 4 | Web app | — |
| 5 | Indeed, Adzuna, automation, deploy | 4 Adzuna, 6 Cloudflare, 9 Secrets |
| 6 | LinkedIn | 7 Apify |
| 7 | Test week (you only) | — |
| 8 | Go live with Gabi | 10 Go live |
| — | Phase 2, Phase 3 | 5 Gmail |

---

## Step 0 — Orient

```
Read CLAUDE.md, ARCHITECTURE.md, docs/DESIGN.md, docs/PROMPTS.md and every file in config/. Don't write code yet.

Give me:
1. The Phase 1 build plan as a numbered checklist that follows docs/PROMPTS.md steps 1–8.
2. Every ambiguity or contradiction you find between these files, with your suggested resolution.
3. The Python and npm dependencies you intend to use, with versions.

Then git init, commit the current files, and push to <YOUR GITHUB REPO URL>.
```

**Done when:** you've read the list of ambiguities and answered the ones that matter.

---

## Step 1 — Pipeline core, offline

```
Build the first part of the pipeline (ARCHITECTURE.md §4.1–4.3, company ATS boards only):

- requirements.txt (pinned) and config loading with validation that fails loudly on missing or invalid keys.
- ATS collector ported from legacy/scan.py for every ATS type used in config/companies.yaml, returning RawJob.
- Normalise and dedupe (§4.2), including the URL parser ported from legacy/add_from_links.py.
- Gatekeeper (§4.3) with word-boundary matching from config/search_terms.yaml.
- Capture one real response per ATS type into tests/fixtures/ (trim to ~20 postings each).
- run.py with --fixtures --dry-run --no-publish: prints counts per stage and the surviving jobs.

Tests (all offline): every fixture parses; a known duplicate pair merges; "International Business Analyst" survives the "intern" exclusion; non-NL locations are dropped; Dutch-language postings are kept.
```

**Done when:** `pytest` passes and `python run.py --fixtures --dry-run` prints a list that looks plausible to you.

---

## Step 2 — Judge and accuracy test

```
Build the Judge (ARCHITECTURE.md §4.5) and run.py --eval.

- First check the current Anthropic API docs for claude-haiku-5-5: how to set effort to low, and whether structured outputs / JSON-schema enforcement is supported. Use it if it is. Send no temperature/top_p/top_k and no assistant prefill.
- System prompt from config/judge_prompt.md; profile from config/profile_brief.md plus languages from config/profile.yaml. Pass the job description as data.
- Validate the response with a schema model; retry once; otherwise mark the job "held" for the next run.
- Respect judge.max_calls_per_run; log tokens and cost per run.
- --eval: read tests/gold_set.csv; on the first run fetch and cache each description into tests/fixtures/gold/ (report dead links and skip them); judge each; compare should_show with "would be placed in the deck or queue"; print a confusion table and every disagreement with the Judge's reasons and gaps.
- Record three Judge responses as fixtures so tests never call the API.
```

**Done when:** `--eval` shows **≥ 25/30** agreement. If it doesn't, ask Claude Code to propose changes to `profile_brief.md` or `judge_prompt.md` based on the disagreements; approve them yourself, then re-run.

---

## Step 3 — Database, verifier, ranking, publish

```
Build storage and the rest of the Phase 1 pipeline:

- supabase/migrations for ARCHITECTURE.md §7: tables, the views my_week, deck_today and queue_open, and RLS exactly as specified, with a comment explaining each policy. Seed progress_settings from config/profile.yaml and a members row for Peter (email from env, role peter).
- Phase 1 review rule: deck and queue exclude jobs the current user has already decided on, and jobs anyone marked dead or fake.
- Verifier tier 1 (§4.6) with config/closed_phrases.yaml.
- Ranker and placement (§4.7) from config/scoring.yaml: deck ≤ 8, ≤ 2 per company, dutch == required goes to the queue.
- Publish in one transaction with the service-role key; write runs, source_stats and costs.
- Apply the migrations to my EU Supabase project (ask me for the project ref and database password when you need them).
- Then one live run: --only ats --limit 30.

Tests: placement rules; an RLS check showing that without a session nothing is readable, with Peter's session only published jobs are visible, and jobs can't be written from the client.
```

**Done when:** the live run fills the tables in the Supabase dashboard and the RLS check passes.

---

## Step 4 — Web app

```
Build web/ (ARCHITECTURE.md §6.1–6.3 Phase 1 scope, docs/DESIGN.md). Use design/screens/*.png as the visual reference and design/mockups/*.dc.html for exact spacing and styles.

- Vite + TypeScript + Preact + supabase-js, anon key only.
- Login with a 6-digit email code (signInWithOtp, then verifyOtp with type "email"); the session persists.
- Screens: Início (tide from my_week, review button, Sua lista, Fila row), Revisar (deck mode and queue mode, two big buttons plus Depois / Link morto / Parece fake, undo toast), Pronto, Fila (list, filter chips, opens the same card), Candidaturas (counters, list, status sheet, register an external application with an optional link).
- Tab bar on main screens. All copy from web/src/copy.pt.ts, generated from the table in docs/DESIGN.md §4.
- PWA manifest: name "Maré", standalone, theme and background #FFF8F4, icons.
- Phase 1 leaves out: sun streak, reason sheet, Peter-only controls and Health page.
- Mobile-first at 390 px; check it also works at 360 px. Accessibility rules from CLAUDE.md.
```

**Done when:** on your phone (local dev URL or a preview deploy) you can log in with a code, review a deck end to end, mark a lead "Candidatei", register an external application, and see the tide move.

---

## Step 5 — More sources, automation, deploy

```
- Indeed collector (python-jobspy) and Adzuna collector (§4.1, config/sources.yaml), each with a saved fixture. Check Adzuna's current API docs for parameter names (title_only etc.) and resolve its redirect URLs to the real posting.
- Manual-links collector reading the manual_links table (in Phase 1 I add rows in the Supabase dashboard).
- Budget tracking against budget_eur_per_month: paid collectors switch off at 100%.
- .github/workflows/radar.yml: cron "37 6 * * 1,3,5", plus workflow_dispatch with inputs backfill_days, only, limit. Secrets from GitHub Actions; nothing secret in logs.
- Cloudflare Pages settings for web/ — tell me exactly what to enter.
- Then trigger one run with backfill_days=30.
```

**Done when:** the workflow run is green, the app on `*.pages.dev` shows leads from at least three sources, and the run's cost is in the `costs` table.

---

## Step 6 — LinkedIn

```
Build the LinkedIn collector via Apify (ARCHITECTURE.md §8, config/linkedin_searches.yaml):

- Call the actor in actor.id through the Apify API with the enabled searches' URLs and per-search max_results; set the run's maximum charge from actor.max_charge_usd_per_run (backfill_max_charge_usd when backfilling).
- Map results to RawJob; capture a fixture from one real run.
- If Apify returns a usage-limit error (Free plan used up), skip LinkedIn, record "paused" in source_stats, and continue.
- Record the run's cost in costs; record LinkedIn yield (share reaching fit ≥ 6) in source_stats.
- Run --only linkedin --no-publish once and show me: results returned, how many passed the Gatekeeper, how many reached fit ≥ 6, and the cost.
```

**Done when:** the cost per run is under the cap and the yield looks reasonable. Then set `linkedin.enabled: true` in `config/sources.yaml` and commit.

---

## Step 7 — Test week (you only)

Use the app yourself for three runs (Mon, Wed, Fri). On each run check: every "Ver vaga" opens a real, open posting; the deck has at most 8 relevant leads; the login code works in the home-screen app. Mark leads the way you think Gabi would. Then:

```
Review the last three runs: for each, the deck, queue size, dead links found by the Verifier, links I marked dead that the Verifier passed, my "Não é pra mim" decisions, sources' yield, and costs. Propose config changes as a diff. Don't apply them.
```

**Done when:** you've applied the changes you agree with, and a full run produces a deck you'd be happy to hand her.

---

## Step 8 — Go live with Gabi

Do `docs/SETUP.md` step 10 first (add her as a Supabase user).

```
Go live:
- Add Gabi as a member: email <HER EMAIL>, role candidate.
- Delete my test applications and test reviews so her Candidaturas, tide and deck start clean.
- Confirm with an RLS check that her session reads published jobs and writes only her own reviews and applications.
```

**Done when:** she has logged in on her phone from the home-screen icon and reviewed her first deck.

---

## Phase 2 (week 2)

Do `docs/SETUP.md` step 5 (Gmail) first.

```
Build Phase 2 from ARCHITECTURE.md §13: sun streak with the cloudy-week bank (§6.4); the optional reason sheet after "Não é pra mim"; Peter-only controls in English (Recommend, + Add link at the top of Fila, Health page per docs/DESIGN.md §3); review effects per ARCHITECTURE.md (Peter's "not for me" is advisory, dead/fake from either hides for both); Verifier tier 2 with Playwright; ghost score; queue re-check and 14-day expiry; nudge email after runs with new deck leads (Gmail SMTP, copy from DESIGN.md); error email to ALERT_TO with the traceback, publishing nothing on failure; PWA polish. Tests for each.
```

## Phase 3 (week 3+, only after she's applied to something the radar found)

```
Build Phase 3 from ARCHITECTURE.md §13: weekly Company radar (§4.8) with weekly.py and its workflow; Judge calibration examples from recent reviews; Health-page suggestions as proposed config diffs; per-domain verifier modes. Optional IND sponsor badge only if I ask.
```

---

## Everyday use

- **Change search terms, cities or weights:** edit the YAML in `config/`, commit, push. The next run uses it. No Claude Code needed.
- **Run now:** GitHub → Actions → radar → Run workflow.
- **Add a job you found:** Phase 1: insert a row in `manual_links` in the Supabase dashboard. Phase 2: "+ Add link" in the app.
- **Something broke:**

```
The <run on DATE / app screen X> shows <WHAT YOU SEE>. Here is the GitHub Actions log: <PASTE>. Diagnose it and propose a fix. Wait for my OK before changing config, schema or RLS.
```

# Setup — what Peter does by hand

Claude Code writes the code; these steps need you (accounts, keys, judgement). About 2–3 hours in total, spread over the build. The "Needed before" column refers to the steps in `docs/PROMPTS.md`.

| # | Task | Time | Needed before |
|---|---|---|---|
| 1 | GitHub private repo | 10 min | Prompt step 1 |
| 2 | Supabase project (EU) | 20 min | Prompt step 3 |
| 3 | Anthropic API key + small top-up | 10 min | Prompt step 2 |
| 4 | Adzuna developer key | 5 min | Prompt step 5 |
| 5 | Gmail account for nudges | 15 min | Phase 2 (create early anyway) |
| 6 | Cloudflare Pages | 15 min | Prompt step 5 |
| 7 | Apify account + LinkedIn calibration | 30–45 min | Prompt step 6 |
| 8 | Gold set: label 30 postings | 45–60 min | Prompt step 2 |
| 9 | GitHub Actions secrets | 10 min | Prompt step 5 |
| 10 | Go live with Gabi | 15 min | Prompt step 8 |
| 11 | Shutdown | 10 min | after she's hired |

Keep every key in a password manager. Never paste keys into chat with Claude Code; put them in `.env` (local) and GitHub secrets.

---

## Before you start (not blocking the build)

- **Partner route:** confirm the conditions and her `work_authorised_from` date with the IND or an immigration lawyer, then fill it in `config/profile.yaml`.
- **Her sign-off:** 15 minutes with Gabi on target roles, cities and a salary floor. Until then `config/profile_brief.md`, `profile.yaml`, `search_terms.yaml` and `linkedin_searches.yaml` stay marked PROVISIONAL. Changing them later is a YAML edit, no rebuild.
- **Local copy of `companies.yaml`:** if your scanner folder has a newer `companies.yaml` with verified `ats`/`slug` values, merge them into `config/companies.yaml`.

## 1. GitHub

1. github.com → New repository → name e.g. `praia-job-radar` → **Private**.
2. In Claude Code (step 1 of PROMPTS) ask it to `git init`, commit and push to that repo. Or do it yourself.

## 2. Supabase (EU)

1. supabase.com → New project. **Region: Central EU (Frankfurt)** (or another EU region). Free plan.
2. Save the database password.
3. Authentication → Sign In / Providers → Email: enabled. **Turn off "Allow new users to sign up".**
4. Authentication → Emails → the **Magic Link** template: replace the link with the code so the email shows a 6-digit code, e.g. `Seu código do Maré: {{ .Token }}`. (A code works inside the iPhone home-screen app; a link doesn't.)
5. Authentication → Users → **Add user** → your email only for now. Gabi is added at go-live (step 10).
6. Project Settings → API: copy the **Project URL**, the **anon/publishable** key (web app) and the **service_role/secret** key (pipeline only).
7. Optional: Supabase's built-in email has low hourly limits. If login codes stop arriving, set custom SMTP (Authentication → Emails → SMTP) with the Gmail account from step 5.

The free project pauses after 7 days without activity. The Mon/Wed/Fri runs keep it awake; if it ever pauses, restore it from the dashboard.

## 3. Anthropic

1. console.anthropic.com → Billing → add about $5 of credit (the whole 3 months uses roughly $0.50).
2. If the console offers a spend limit, set it to $5/month.
3. API keys → create one named `praia-job-radar`.

## 4. Adzuna

developer.adzuna.com → sign up → create an app → copy **App ID** and **App Key**. Free.

## 5. Gmail for nudges

1. Create a dedicated account, e.g. `mare.radar@gmail.com`.
2. Google Account → Security → turn on 2-Step Verification.
3. Security → **App passwords** → create one named `mare` → copy the 16-character password.
4. While building, `NUDGE_TO` = your address only.

## 6. Cloudflare Pages

1. dash.cloudflare.com → sign up (free).
2. Wait until prompt step 5; Claude Code will give you the exact build settings. You'll connect the GitHub repo under Workers & Pages → Create → Pages, set the root to `web`, and add `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` as environment variables.
3. You get a `*.pages.dev` address. A custom domain is optional.

## 7. Apify + LinkedIn calibration

**Account:** apify.com → sign up (Free plan, no credit card, $5 of usage per month). Settings → API & Integrations → copy the **API token**.

**Pick an actor** in the Apify Store (search "LinkedIn jobs scraper") that:
- accepts **LinkedIn search URLs** as input,
- returns the **full job description and the apply URL** in the same result,
- charges **per result** (no monthly rental), and shows its Free-plan price,
- was updated recently and has active users.

Put its ID in `config/linkedin_searches.yaml → actor.id`. Free-plan prices per result are often about twice the paid-plan price; that's fine at this volume.

**Calibrate each search** (instructions are at the top of `config/linkedin_searches.yaml`):
1. Private browser window (logged out) → linkedin.com/jobs/search.
2. Paste the `keywords`, location Netherlands, filters: Past week, Entry level + Associate + Mid-Senior, Full-time.
3. Write the result count into `count_past_week`.
4. Copy the URL into `url` and change `f_TPR=r604800` to `f_TPR=r259200` (72 hours).
5. Set `max_results` ≈ `count_past_week ÷ 2.3 × 1.5`, rounded up.

Then set `linkedin.enabled: true` in `config/sources.yaml` when Claude Code reaches prompt step 6.

## 8. Gold set — 30 labelled postings

This is how you check the AI judges like you would, before Gabi sees anything.

1. Search LinkedIn, Indeed NL and a few company career pages for her kind of roles in the Netherlands.
2. Pick about **15 she should see** and **15 near-misses** that she shouldn't: too senior, client-facing (account manager, SDR), Dutch required, wrong function (pure finance, engineering), internships.
3. Add one row each to `tests/gold_set.csv`: `url,title,company,should_show,reason` with `should_show` = `yes` or `no` and a short reason.
4. Do this soon: postings disappear. The first `--eval` run saves each description to `tests/fixtures/gold/` so later runs don't depend on the links.

## 9. GitHub Actions secrets

Repository → Settings → Secrets and variables → Actions → New repository secret, one for each name in `.env.example` except the `VITE_` ones (those go to Cloudflare):
`ANTHROPIC_API_KEY`, `APIFY_TOKEN`, `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `NUDGE_TO`, `ALERT_TO`.

## 10. Go live with Gabi

Only after prompt step 7 (a test week on your phone) looks right.
1. Supabase → Authentication → Users → Add user → her email. Claude Code adds her to `members` with role `candidate` (prompt step 8).
2. Add her address to `NUDGE_TO` (comma-separated with yours, or hers only).
3. Send her the `*.pages.dev` link with these steps, in your own words:
   - open it in **Safari** (not inside WhatsApp),
   - log in with the 6-digit code from her email,
   - Compartilhar → **Adicionar à Tela de Início**.
4. Tell her the praia stays her own thing; the app is for leads and applications.

## 11. Shutdown (once she's hired)

Disable the GitHub Actions workflows; delete the Apify token; revoke the Anthropic key and the Gmail app password; export her applications to CSV for her records (ask Claude Code); pause or delete the Supabase project.

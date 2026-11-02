# Building Maré on Replit — one-page manual

The Replit Agent does the coding. You prepare keys, paste five prompts, and check each result. The brief it follows is `replit.md` in the repo root.

## Before you start (about 1.5 hours, do once)

| What | Where | Result |
|---|---|---|
| Spending cap | Replit → account → Usage/Billing: set a monthly budget limit | no surprise overage |
| Anthropic key | console.anthropic.com → Billing: add $5 → API keys | `ANTHROPIC_API_KEY` |
| Adzuna key | developer.adzuna.com → create app (free) | `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` |
| Apify | apify.com → Free plan (no card) → Settings → API & Integrations; pick a LinkedIn jobs actor that takes search URLs and charges per result | `APIFY_TOKEN`, actor ID |
| LinkedIn searches | Private browser window, logged out → linkedin.com/jobs. Build each search in `config/linkedin_searches.yaml` (instructions at the top of that file), paste the URLs and counts | calibrated searches |
| Gold set | Find 30 real Dutch postings: ~15 she should see, ~15 she shouldn't. You can paste them into the Agent chat; it writes `tests/gold_set.csv` | accuracy test data |
| PINs | Pick a 6-digit PIN for Gabi and one for you; make up a long random `SESSION_SECRET` | login |

## Build (the Agent works; you review)

1. **Import:** Replit → Create → Import from GitHub → `peterschmidt98/praia-job-radar`.
2. **Secrets:** in the Repl, open the Secrets tool and add `ANTHROPIC_API_KEY`, `APIFY_TOKEN`, `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, `PIN_GABI`, `PIN_PETER`, `SESSION_SECRET`. Never paste keys into the chat.
3. **Prompts:** open the Agent and paste Prompts 1–5 from the end of `replit.md`, one at a time. After each one, check:
   - **1 Plan:** it read the files and asks sensible questions. Answer them.
   - **2 Pipeline:** the eval shows **25/30 or better**. If not, ask it to propose changes to `config/profile_brief.md` or `config/judge_prompt.md` from the disagreements, approve, re-run.
   - **3 LinkedIn:** cost per run under $0.30, and a reasonable share of results scoring 6+.
   - **4 App:** on your phone, log in with your PIN, review a few leads, mark one "Candidatei", register one application from outside.
   - **5 Go live:** a scheduled deployment exists and the app has a public URL.

## Test week (just you)

Use the app for three runs (Mon, Wed, Fri). Every "Ver vaga" must open a real, open posting; at most 8 relevant leads per run. Mark leads the way Gabi would. Then ask the Agent: *"Review the last three runs and propose config changes. Don't apply them."* Before inviting her, ask it to delete your test applications and reviews.

## Hand it to Gabi

Send her the app URL and her PIN. She opens it in **Safari** (not inside WhatsApp), logs in, then taps Compartilhar → **Adicionar à Tela de Início**. The praia stays her own separate thing.

## Running it

- **Tune the search:** edit the files in `config/` (roles, cities, terms, weights). The next run uses them.
- **Add a job you found:** "Add link" in the app.
- **Costs:** your Replit subscription, about €0.50 of the $5 Anthropic credit, LinkedIn within Apify's free $5/month (it pauses until next month if used up), the rest free. Check Replit usage weekly.
- **Something broke:** tell the Agent what you saw and paste the deployment log; ask it to diagnose before changing anything.
- **When she's hired:** stop the scheduled deployment, export her applications, revoke the keys.

# Maré on Replit — 30-minute manual

You do four short things. The Replit Agent builds the rest from `replit.md`.

| # | You | Time |
|---|---|---|
| 1 | **Apify:** apify.com → sign up (Free plan, no card) → Settings → API & Integrations → copy the token. | 5 min |
| 2 | **Claude access:** only if the Agent says Replit has no built-in Claude access: console.anthropic.com → add $5 → create an API key. | 0–5 min |
| 3 | **Replit:** set a monthly spending cap. Create → Import from GitHub → `peterschmidt98/praia-job-radar`. In Secrets add `APIFY_TOKEN`, `PIN_GABI`, `PIN_PETER` (two 6-digit PINs you choose). Open the Agent and paste the prompt at the end of `replit.md`. | 10 min |
| 4 | **Check the result:** open the app URL on your phone, log in, look at the first run's numbers. Every "Ver vaga" you try should open a real, open posting. | 10 min |

Then Gabi spends **10 minutes in Calibrar**, rating 20 real postings. If the system agrees with her on at least 16, it's live. If not, the Agent proposes changes to her profile and you approve them.

**While it's being built,** Gabi turns on LinkedIn job alerts for "Sales Operations" and "Revenue Operations" in the Netherlands, so she keeps applying in the meantime.

**Costs:** your Replit subscription, LinkedIn within Apify's free $5/month (it pauses until next month if used up), and Claude either through Replit or about €0.50 of a $5 Anthropic top-up.

**Tuning later:** say it in plain words to the Agent ("more pricing roles", "fewer Utrecht jobs", "too many senior roles"). It edits `config/`.

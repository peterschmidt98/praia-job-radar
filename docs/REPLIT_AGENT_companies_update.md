I've replaced config/companies.yaml (106 companies: the 26 original, re-checked, plus 80 Dutch scale-ups). Please wire it in without changing anything else:

1. Read the new optional fields described in the file header:
   - `host: eu`: for Greenhouse, try boards-api.eu.greenhouse.io/v1/boards/{slug}/jobs first, then the global host. For Lever, use api.eu.lever.co/v0/postings/{slug}.
   - `base_url`: Recruitee on the company's own domain. Fetch {base_url}/api/offers/ instead of https://{slug}.recruitee.com/api/offers/.
   - `posts_in` and `careers`: informational only.
2. Recruitee redirects:
   - A 302 to https://recruitee.com/ means the board is dead: skip it and log it.
   - A redirect to another *.recruitee.com subdomain is a rename: follow it and log the new slug.
3. Merge this file with any companies the app has learned automatically (from apply links). Don't delete learned ones.
4. Run discover.py (or an equivalent check) once over every entry that has an ats. Report per company: the number of jobs found, the number of NL jobs, and whether the jobs match the company name (to catch slug collisions). Don't remove failing entries; list them for me, with any fix you'd suggest.
5. Optional, only if it's simple and needs no login: check whether Teamtailor career sites expose a public job feed. If they do, add a Teamtailor collector for ABAX (careers.abax.com), Hadrian (careers.hadrian.io), TestGorilla, Leadinfo (jobs.leadinfo.com) and Last Mile Solutions. If it isn't simple, skip it and tell me.

Then do one run with --no-publish and give me the per-source numbers.

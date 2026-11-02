# Maré — design and copy

The approved direction is **option A's look with option B's flow**: a calm, editorial look (serif titles, warm off-white, teal accent) and a review flow that shows one lead at a time.

- Reference images: `design/screens/1-inicio.png` … `5-candidaturas.png` (390 × 844, phone).
- Reference markup: `design/mockups/*.dc.html`. These are design-canvas files: the inline styles and structure are authoritative, but `<x-dc>`, `<helmet>`, `{{accent}}` and the `text/x-dc` script are canvas machinery. Rebuild as Preact components; don't ship these files. `{{accent}}` = `#1F7A86`.
- Sample data in the mockups (Mollie, Miro, counts) is illustrative.

## 1. Tokens

```css
:root {
  --ground: #FFF8F4;        /* page background */
  --surface: #FFFFFF;       /* cards */
  --border: #F1DFD8;        /* card borders, dividers */
  --border-strong: #E2CEC6; /* secondary button borders */
  --track: #F3E6E1;         /* progress track, neutral chips */
  --ink: #3A2430;           /* main text */
  --muted: #6B5560;         /* secondary text (4.5:1 on ground) */
  --accent: #1F7A86;        /* primary actions, tide, links */
  --accent-hover: #165C66;
  --accent-tint: #E4F2F3;   /* "Verificada", Candidatei chips */
  --accent-tint-ink: #155E68;
  --warm: #A8355A;          /* Peter, nãos corajosos */
  --warm-tint: #FBEAE3;
  --warn-ink: #8A3350;      /* "Atenção" */
  --sun: #B07A12;           /* sun icon */
  --pending: #9FD0D6;       /* tide segment already covered by her list */
  --font-display: "Instrument Serif", Georgia, serif;
  --font-ui: "Nunito Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
}
```

| Element | Spec |
|---|---|
| Page padding | 22 px sides on main screens, 16–18 px on Revisar |
| Display type | Instrument Serif 400: greeting 40 px, lead title 38 px, section title 24 px, big numbers 28–30 px |
| UI type | Nunito Sans 400/600/700/800; body 15 px, meta 13 px, labels 12 px uppercase with 0.06–0.08em tracking (only for the date line and "Por que combina com você") |
| Radius | cards 16 px (lead card 24 px, CTA 18 px), buttons 12–16 px, chips full |
| Primary button | 56 px tall on Revisar/Pronto, 44–52 px elsewhere; accent background, white 800 text |
| Secondary button | white, 1 px `--border-strong`, ink text |
| Icons | inline stroke SVG, 2–2.4 stroke width, `aria-hidden`; no emoji anywhere in the UI |
| Motion | one transition only: the lead card slides out/in on a decision (200 ms); honour `prefers-reduced-motion` |

Load fonts from Google Fonts with `display=swap`; the system fallbacks must still look right. Labels like "Quero me candidatar" may wrap to two lines on narrow phones; never truncate them.

## 2. Screens

Tab bar (Início · Fila · N · Candidaturas) on every main screen. Revisar and Pronto are full-screen flows without the tab bar.

| Screen | Purpose | Reference |
|---|---|---|
| Login | email → 6-digit code | none (keep it plain: ground, serif "Maré", one field, one button) |
| Início | where am I this week, what do I do next | `1-inicio.png` |
| Revisar | decide on one lead | `2-revisar.png` |
| Pronto | close the review with a win | `3-pronto.png` |
| Fila | everything waiting, one tap away | `4-fila.png` |
| Candidaturas | every application and its status | `5-candidaturas.png` |
| Health (Peter only, English) | pipeline status, costs, suggestions | none |

Behaviour details:
- **Revisar decisions** advance to the next card immediately and show a toast with **Desfazer** for 5 seconds.
- **Não é pra mim** then shows an optional reason sheet (one tap or Pular). Never block the flow on it.
- **Revisar in queue mode** (from Fila) uses the same card; the progress label reads "Fila: 3 de 9".
- **Candidatei** (Início list or a Fila card) creates an application, moves the tide, and shows the toast `toast_applied`.
- **Status change** in Candidaturas opens a small sheet with the five statuses; choosing "Não" shows `toast_brave_no`.
- **Ver vaga / Ler a vaga completa** open the canonical URL in a new tab.
- Empty Início (no new leads, empty list): greeting, tide, `home_none_new`, and the Fila row.

## 3. Peter-only controls (English)

- On every lead card: **★ Recommend** (sends it to her next review deck with "Peter indicou") and his own review buttons. His "Not for me" is advisory: her card shows `peter_maybe_not`.
- **+ Add link** field (top of Fila): paste a job URL; it's judged and verified in the next run.
- **Health** tab: last runs, per-source fetched/kept/published, LinkedIn yield and cost per published lead, dead-report rate, verifier misses, spend vs budget, top "not for me" reasons, Judge eval score, proposed config changes.

## 4. Copy (pt-BR) — authoritative

Use "você"/"sua" throughout. `{n}` etc. are variables. Where singular and plural differ, both are given.

| Key | Text |
|---|---|
| app_name | Maré |
| login_title | Maré |
| login_email_label | Seu e-mail |
| login_send_code | Enviar código |
| login_code_sent | Enviamos um código de 6 dígitos para {email}. |
| login_code_label | Código |
| login_submit | Entrar |
| login_code_wrong | Código errado ou expirado. Peça um novo. |
| login_resend | Reenviar código |
| login_not_member | Este e-mail não tem acesso. |
| greeting_morning / afternoon / evening | Bom dia, {nome} / Boa tarde, {nome} / Boa noite, {nome} |
| home_new_since | Chegaram {n} leads novos desde {dia}. · (1) Chegou 1 lead novo desde {dia}. |
| home_none_new | Nenhum lead novo desde {dia}. A próxima busca é {proximo_dia}. |
| tide_title | Maré da semana |
| tide_count | {x} de {meta} candidaturas |
| tide_met | Meta da semana batida. |
| streak | {n} semanas de sol · (1) 1 semana de sol |
| brave_count | {n} nãos corajosos · (1) 1 não corajoso |
| review_cta | Revisar {n} leads novos · (1) Revisar 1 lead novo |
| review_cta_sub | Um de cada vez · uns {min} minutos |
| list_title | Sua lista · {n} |
| list_item_meta | {empresa} · {cidade} · escolhida {dia} |
| list_empty | Os leads que você escolher aparecem aqui. |
| btn_view_job | Ver vaga |
| btn_applied | Candidatei |
| queue_row | Fila · {n} leads esperando · (1) Fila · 1 lead esperando |
| tab_home / tab_queue / tab_applications | Início / Fila · {n} / Candidaturas |
| review_exit | Sair |
| review_progress | Lead {i} de {n} |
| review_progress_queue | Fila: {i} de {n} |
| badge_verified | Verificada hoje |
| badge_peter | Peter indicou |
| badge_age | hoje / ontem / há {n} dias |
| badge_hiring | Contratando ativamente |
| badge_ghost | Pode ser vaga fantasma |
| badge_dutch | Precisa de holandês |
| why_title | Por que combina com você |
| watch_prefix | Atenção: |
| read_full | Ler a vaga completa |
| btn_not_for_me | Não é pra mim |
| btn_want_apply | Quero me candidatar |
| btn_later | Depois (fila) |
| btn_dead | Link morto |
| btn_fake | Parece fake |
| reason_title | Por quê? (opcional) |
| reason_options | Sênior demais · Não é o tipo de vaga · Precisa de holandês · Local · Empresa · Pular |
| peter_maybe_not | Peter: talvez não — {motivo} |
| toast_listed | Foi pra sua lista. |
| toast_skipped | Anotado. |
| toast_later | Guardada na fila. |
| toast_reported | Obrigado. Não vai aparecer de novo. |
| toast_undo | Desfazer |
| toast_undone | Desfeito. |
| toast_applied | Candidatura registrada. Mais um passo. |
| toast_brave_no | Mais um não corajoso. Conta como progresso. |
| done_count | {n} de {n} revisados |
| done_title | Pronto por hoje. |
| done_sub | Decidir também é avançar. |
| done_to_list | Foram pra sua lista · (1) Foi pra sua lista |
| done_not_for_you | Não eram pra você · (1) Não era pra você |
| done_later | Guardadas pra depois · (1) Guardada pra depois |
| done_tide_covered | As {k} que faltam já estão na sua lista. · (1) A que falta já está na sua lista. |
| done_tide_short | Faltam {k} pra meta. Sem pressa. |
| done_btn_list | Ver minha lista |
| done_btn_queue | Revisar a fila ({n}) |
| queue_title | Fila |
| queue_sub | {n} leads esperando. Sem pressa — depois de 14 dias, saem sozinhos. |
| queue_review_all | Revisar um de cada vez |
| queue_filter_all | Todos · {n} |
| queue_filter_peter | Peter indicou · {n} |
| queue_filter_dutch | Precisa de holandês · {n} |
| queue_empty | A fila está vazia. |
| apps_title | Candidaturas |
| apps_sub | Cada uma conta, inclusive os nãos. |
| apps_sent / apps_interviews / apps_brave | enviadas / entrevistas / nãos corajosos |
| apps_add_external | Registrar candidatura de fora do app |
| apps_form_link | Link da vaga (opcional) |
| apps_form_company | Empresa |
| apps_form_role | Vaga |
| apps_form_date | Data |
| apps_form_save | Salvar |
| apps_item_meta | {empresa} · enviada {data} |
| apps_status_title | Atualizar status |
| status_sent / interview / offer / no / withdrawn | Enviada / Entrevista / Oferta / Não (corajoso) / Retirei |
| apps_empty | Quando você se candidatar, a vaga aparece aqui. |
| error_load | Não deu pra carregar. Verifique a conexão e tente de novo. |
| error_save | Não deu pra salvar. Tente de novo. |
| install_hint | Abra no Safari e toque em Compartilhar → Adicionar à Tela de Início. |
| nudge_subject | {n} leads novos · (1) 1 lead novo |
| nudge_body | Chegaram {n} leads novos pra você revisar. Leva uns {min} minutos. |
| nudge_button | Abrir o Maré |

Dates: Portuguese day and month names ("segunda", "26 de outubro"), timezone Europe/Amsterdam.

Never shown to her: rejection rates, missed targets, broken streaks, Judge scores as numbers, ghost scores as numbers.

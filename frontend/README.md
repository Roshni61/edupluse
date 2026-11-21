# EduPulse: Round 3 Frontend Prototype

Team **tech gig** · Roshni K, Udit Goel · Prasunex Innovathon 2026

A working frontend prototype of EduPulse: early-warning for students, fair gamified engagement, and parent communication that works for families without smartphones and for busy working parents. All data is **sample data**; there is no backend yet.

## Run it

```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # type-check and production build
```

Needs Node 18+. Fonts (Fraunces, DM Sans, Noto Sans Tamil) load from Google Fonts, so use an internet connection for the intended look. The app still works offline with fallback fonts.

## The five-minute demo (suggested order)

1. **Landing page**: pick a role. The top bar switches roles at any time; `EN / தமிழ்` switches language; `Reset demo` restores sample state.
2. **Teacher > Today**: change "Your time today" between 10, 20 and 30 minutes and watch the plan re-rank. Open **Karthik**.
3. **Karthik's page**: compare him with *his own* baseline, drag the What-if sliders (level changes live), log a Playbook action, switch the parent note to தமிழ், approve it.
4. **Student view**: start **Fraction warm-up**. Get one answer wrong (hint, no penalty), finish, and unlock the **Personal Best** badge. Check the Class Garden and Badges shelf.
5. **Parent view**: tap a check-in mood (plus a voice-note demo), then **Book a call**. Pick Before school > 7:35, confirm, and download the `.ics` calendar file. Toggle தமிழ்.
6. **Parent > Reach me**: turn on "I don't use a smartphone", then try the **weekly voice call** keypad simulator (Tamil and English subtitles).
7. **Teacher > Parent Connect**: reach ladder, families needing a human touch, weekly five-minute slot grid.
8. **Teacher > Missions and Garden**: assign missions, send kudos, **Print cards** for students without devices.
9. **Admin**: engagement equity chart, reach by channel, support heatmap, guardrails.

## What is implemented

| Area | Feature |
|---|---|
| Teacher | Time-budget planner, Change-from-Self chart, reasons, what-if simulator, Support Playbook logging, parent-note approval (EN/TA), bright spots and kudos |
| Fair gamification | XP for effort (not marks), starter-level missions, 12 badges in 5 categories, comeback and personal-best badges, cooperative Class Garden, no leaderboards, anonymous "I'm stuck", printable paper mission cards |
| Parents without smartphones | 5-step reach ladder, SMS with reply codes, automated voice-call simulator, family helper, Saturday school desk, teacher callback queue |
| Busy parents | 5-minute slots inside teacher working hours, voice-note alternative, reminder options, downloadable `.ics` calendar event |
| Admin | Equity of badge-earning across performance bands, reach channels, class heatmap, locked guardrails |
| Responsible design | No sensitive attributes, teacher-only support levels, student view shows growth only, school-level switches |

## Design decisions (why it works in real life)

- **Rewards effort, not marks.** XP is the same for the same effort, so a low performer can earn as much as a top student. Badges are tied to growth against the student's own past.
- **Cooperative, not competitive.** The Class Garden counts everyone's drops equally and never names anyone.
- **Not dependent on devices.** Paper mission cards and teacher tick-offs; the voice call and SMS ladder for families.
- **Teachers are people.** Call windows stay inside school hours; evening slots only Tue and Thu; shift workers get voice notes instead.
- **Equity is measured.** The admin equity chart exists so we can detect if rewards favour the top.

## Technical overview

- **Stack:** React 18, TypeScript, Vite, Tailwind CSS 3, React Router (HashRouter), Recharts, Framer Motion, lucide-react.
- **State:** a single `useReducer` store in `src/store.tsx`, persisted to `localStorage` (`Reset demo` clears it).
- **Data:** `src/data/mock.ts` holds students, badges, missions, slots and admin figures. Replace with API calls when the backend exists.
- **Support-level logic:** `supportLevel()` in `mock.ts` is a transparent rule combining attendance, homework and drop from the student's own baseline. It stands in for the Change-from-Self engine and model.
- **Structure:** `src/pages/{teacher,student,parent,admin}`, shared UI in `src/components`, copy in `src/i18n.ts`.

## Limitations (honest list)

- No backend, login or real data. Support levels use a simple rule, not a trained model.
- The voice call, SMS, WhatsApp and calendar reminders are **simulated** (the `.ics` file is real). Real delivery needs a telephony/SMS provider.
- Tamil strings cover the parent portal's key screens and should be reviewed by a native speaker before any real use.
- Consent flows, data retention and audit logs are designed but not built.
- Chart data and the Karthik story are illustrative.

## Future development

1. FastAPI backend, PostgreSQL with row-level security, role-based login.
2. Real scoring: Change-from-Self engine plus gradient-boosting model with explanations; backtests on public datasets and a fairness report.
3. Integrations: ERP adapter (Prasunex first), SMS/voice provider, WhatsApp, calendar invites.
4. Intervention-effect tracking with similar-student comparison.
5. Pilot in one school; review gamification equity metrics monthly.

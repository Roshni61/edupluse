# EduPulse 🌿
> **Fair gamification, early warning intervention, and respectful parent communication.**  
> Prasunex Innovathon 2026 · Team **tech gig** (Roshni K, Udit Goel)

---

## 🔑 Demo Login Accounts

All demo accounts are pre-seeded in the database with the default password: **`Demo@1234`**.  
You can use the **Quick-Login** buttons on the landing page/top bar or sign in manually:

| Role | Username / Email | Password | Persona & Scope |
| :--- | :--- | :--- | :--- |
| 👩‍🏫 **Teacher** | `teacher@edupulse.demo` | `Demo@1234` | **Ms. Priya** · Class 9A Maths · 10/20/30m Time Planner, Change-from-Self Diagnostics & Playbook |
| 🧑‍🎓 **Student** | `student@edupulse.demo` | `Demo@1234` | **Karthik R** · Growth & Missions · Effort-based XP, Hint without penalty, Cooperative Class Garden |
| 👨‍👩‍👦 **Parent** | `parent@edupulse.demo` | `Demo@1234` | **Karthik's Mother** · Weekly 3-Tap Mood Check-in, 5-Minute Call Booking (.ics) & Reach Ladder |
| 🏛️ **Admin** | `admin@edupulse.demo` | `Demo@1234` | **HM Ramanathan** · Engagement Equity, Locked Guardrails & Immutable Audit Logs (Product Rule 7) |

---

## 🚀 Quick Start (Local Run)

### Prerequisites
- **Node.js** (v18+)
- **Python** (3.11+)

### 1. Backend (FastAPI + SQLAlchemy + SQLite/Postgres)
```bash
# In project root
python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000
```
- API Base URL: [http://localhost:8000](http://localhost:8000)
- Interactive Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

### 2. Frontend (React 18 + Vite + TypeScript)
```bash
# In frontend directory
npm --prefix frontend install
npm --prefix frontend run dev
```
- Web Application: [http://localhost:5173](http://localhost:5173)

---

## 🌐 Cloud Deployment (Vercel & Render)

This repository is pre-configured for instant zero-config cloud deployment:

- **Frontend & Serverless API (Vercel)**:
  1. Go to [vercel.com/new](https://vercel.com/new) and import `Roshni61/edupluse`.
  2. Leave Root Directory as `./` (controlled by [`vercel.json`](./vercel.json)).
  3. Click **Deploy**. Both the Vite frontend and Python API (`api/index.py`) will build automatically!
- **Dedicated Persistent Backend (Render)**:
  1. In [dashboard.render.com](https://dashboard.render.com), create a new **Web Service** from [`render.yaml`](./render.yaml).
  2. Start command runs Uvicorn ASGI with auto-seeding enabled.

---

## 🎬 5-Minute Demo Flow Walkthrough

1. **Teacher > Today ([http://localhost:5173/#/teacher](http://localhost:5173/#/teacher))**:
   - Log in as `teacher@edupulse.demo`.
   - Toggle time budget between **10 min**, **20 min**, and **30 min** to see the plan re-rank students by benefit-per-minute.
   - Open **Karthik** (ranked at Level 3 support).
2. **Karthik Diagnostic Detail**:
   - View Karthik's score drop compared to *his own* baseline (Change-from-Self engine).
   - Test the What-If simulation slider (e.g. increase attendance to 95%).
   - Log an action in the Support Playbook.
   - Switch parent note language between English and தமிழ், then click **Approve and send**.
3. **Student View ([http://localhost:5173/#/student](http://localhost:5173/#/student))**:
   - Switch to Karthik via the top bar role switcher.
   - Start **Fraction warm-up** mission. Select a wrong answer first to verify hint feedback with **zero penalty** (Product Rule 1).
   - Answer correctly, complete the mission, and unlock badges.
   - View cooperative **Class Garden** (no student rankings or leaderboards, Product Rule 2).
4. **Parent View ([http://localhost:5173/#/parent](http://localhost:5173/#/parent))**:
   - Switch to parent role.
   - Complete 3-tap weekly mood check-in.
   - Navigate to **Book a call**, select a 5-minute slot within teacher working hours (Tue/Thu evening window rules enforced, Product Rule 5), confirm, and download the `.ics` calendar invitation.
   - Try the **Reach me** ladder for low-tech phone access / shift workers.
5. **Admin Portal ([http://localhost:5173/#/admin](http://localhost:5173/#/admin))**:
   - Inspect **Engagement Equity** across performance bands (fairness alert triggered if gap exceeds 10 points).
   - Verify **Locked Guardrails** (no sensitive attributes like caste/religion/income, Product Rule 4).
   - Check **Audit Logs** ([http://localhost:5173/#/admin/audit-logs](http://localhost:5173/#/admin/audit-logs)) to verify Product Rule 7 compliance.

---

## 🧪 Testing & Verification

```bash
# Run backend pytest suite (67 passed)
python -m pytest backend/tests -v

# Run Playwright End-to-End full demo suite
npx playwright test

# Build frontend production bundle
npm --prefix frontend run build
```

---

## 📜 Core Architecture Rules ([AGENTS.md](./AGENTS.md))

1. **Effort over Marks**: XP is awarded for effort, never for marks. Same effort = same XP.
2. **No Leaderboards**: Class Garden is cooperative and never names individual students.
3. **Growth Only for Students**: Students and parents see growth only, never support levels (teacher-only).
4. **No Sensitive Attributes**: No sensitive attributes stored (caste, religion, income, etc.).
5. **Respectful Call Windows**: Parent call windows stay inside school hours; evening slots only Tue and Thu.
6. **Student Anonymity for Doubts**: Anonymous "I'm stuck" doubts are never linkable to student IDs in teacher APIs.
7. **Audit Logging**: Every sensitive read/write by teacher or admin is immutably logged.

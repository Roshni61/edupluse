# EduPulse Permanent System & Architecture Rules

## PRODUCT RULES (never violate):
1. **Effort over Marks**: XP is awarded for effort, never for marks. Same effort = same XP for every student.
2. **No Leaderboards**: No leaderboards. The Class Garden is cooperative and never names anyone.
3. **Growth Only for Students**: Students see growth only, never their support level. Support levels are teacher-only.
4. **No Sensitive Attributes**: No sensitive attributes are stored (caste, religion, income, etc.).
5. **Respectful Call Windows**: Parent call windows stay inside school hours; evening slots only Tue and Thu.
6. **Student Anonymity for Doubts**: Anonymous "I'm stuck"/doubt questions must not be linkable to a student in teacher APIs.
7. **Audit Logging**: Every sensitive read/write by teacher/admin is written to an audit log.

## ENGINEERING RULES:
- **Server Truth**: Server is the source of truth. Frontend never computes XP, badges, or support level.
- **Role & School Scoping**: All endpoints are role-checked and school-scoped. Parents see only their own child(ren).
- **Type Safety & Migrations**: Pydantic schemas for every request/response. Alembic for every schema change.
- **Mandatory Testing**: Every new endpoint gets at least one pytest test, including a permission-denied test.
- **Localization**: Keep Tamil (ta) and English (en) strings in the frontend i18n; backend stores language preference only.

# EduPulse Localization Review & Translation To-Do (Tamil - தமிழ்)

This document catalogs existing translations and lists all keys and UI strings requiring review or translation by a native Tamil speaker for production readiness.

---

## 1. Verified & Implemented Translations (`frontend/src/i18n.ts`)

The following keys have baseline Tamil translations in `frontend/src/i18n.ts` used across the Parent Portal and Authentication views:

| Key | English (en) | Current Tamil Translation (ta) | Context / Notes |
| :--- | :--- | :--- | :--- |
| `hello` | Hello, Karthik's family | வணக்கம், கார்த்திக்கின் குடும்பத்தினரே | Respectful greeting |
| `glance` | This week at a glance | இந்த வார சுருக்கம் | Summary card header |
| `well` | What went well | நன்றாக நடந்தவை | Positive reinforcement |
| `tryHome` | One thing to try at home | வீட்டில் முயற்சிக்க ஒரு விஷயம் | Parent tip |
| `checkin` | Weekly check-in | வாராந்திர கருத்து | Mood checkin prompt |
| `checkinQ` | How was this week at home? | இந்த வாரம் வீட்டில் எப்படி இருந்தது? | Warm question |
| `great` | Great | சிறப்பு | Positive mood |
| `okay` | Okay | பரவாயில்லை | Neutral mood |
| `hard` | Hard | கடினம் | Needing support mood |
| `voice` | Voice note | குரல் செய்தி | Audio recording option |
| `send` | Send | அனுப்பு | Action button |
| `book` | Book a 5-minute call | 5 நிமிட அழைப்பை முன்பதிவு செய்யுங்கள் | Call booking CTA |
| `teacherCalls` | Teacher calls my phone | ஆசிரியர் எனக்கு அழைப்பார் | Inbound call channel |
| `voiceNotes` | Voice notes, reply when I'm free | குரல் செய்தி, நேரம் கிடைக்கும்போது பதில் சொல்கிறேன் | Asynchronous voice note channel |
| `visit` | Visit school on Saturday | சனிக்கிழமை பள்ளிக்கு வருகிறேன் | Saturday school desk |
| `video` | Video link | வீடியோ இணைப்பு | Online video slot |
| `reminders` | Reminders | நினைவூட்டல்கள் | Notification toggles |
| `confirm` | Confirm | உறுதிசெய் | Booking confirmation |
| `noPhone` | I don't use a smartphone | என்னிடம் ஸ்மார்ட்போன் இல்லை | Low-tech toggle |
| `thanks` | Thank you | நன்றி | Acknowledgment |
| `nextCall` | Your next call | உங்கள் அடுத்த அழைப்பு | Scheduled booking item |
| `reach` | Reach me | என்னைத் தொடர்பு கொள்ள | Alternative reach ladder header |
| `signIn` | Sign in to EduPulse | எடுபல்ஸ் உள்நுழைவு | Login header |
| `signInDesc` | Access your role-specific dashboard with secure role and school scoping. | பாதுகாப்பான அனுமதியுடன் உங்கள் பொறுப்பிற்குரிய திரையை அணுகுங்கள். | Login subtitle |
| `emailLabel` | Email address | மின்னஞ்சல் முகவரி | Auth form |
| `passwordLabel` | Password | கடவுச்சொல் | Auth form |
| `signInBtn` | Sign In | உள்நுழைக | Auth submit |
| `signingIn` | Signing in... | உள்நுழைகிறது... | Auth pending |
| `logoutBtn` | Log out | வெளியேறு | Topbar action |

---

## 2. To-Do: Teacher Portal Keys (Pending Native Translation)

The following UI strings in `Teacher` pages are currently in English and should be localized in Phase 8:

| Suggested Key | English Source | Proposed Tamil Translation | Context |
| :--- | :--- | :--- | :--- |
| `teacher.today` | Today | இன்று | Main teacher dashboard tab |
| `teacher.budget` | Time budget | நேர ஒதுக்கீடு | 10/20/30 min planner budget |
| `teacher.playbook` | Support Playbook | ஆதரவு செயல்திட்டம் | Action logging |
| `teacher.followup` | Follow-up due | மறுபரிசீலனை நாள் | 4-6 week review reminder |
| `teacher.brightSpots` | Bright spots | பாராட்டுக்குரியவை | Positive growth highlights |
| `teacher.kudos` | Send Kudos | பாராட்டு அனுப்பு | Peer / teacher recognition |
| `teacher.draftNote` | Draft Parent Note | பெற்றோர் குறிப்பு வரைவு | EN/TA parent message |
| `teacher.approve` | Approve & Send | ஒப்புதல் அளித்து அனுப்பு | Outbox dispatch |
| `teacher.unreached` | Needs a human touch | கூடுதல் கவனம் தேவைப்படும் குடும்பங்கள் | Reach ladder list |
| `teacher.reserveCallback` | Reserve callback | திரும்ப அழைப்பை முன்பதிவு செய் | Teacher callback CTA |
| `teacher.autoFit` | Auto-fit requests | தானாக பொருத்து | Slot optimizer |

---

## 3. To-Do: Student Gamification Keys (Pending Native Translation)

| Suggested Key | English Source | Proposed Tamil Translation | Context |
| :--- | :--- | :--- | :--- |
| `student.garden` | Class Garden | வகுப்புத் தோட்டம் | Cooperative anonymous garden |
| `student.drops` | Drops of water | நீர் துளிகள் | Effort contribution units |
| `student.growthLevels` | Sprout / Sapling / Bloom / Grove | தளிர் / நாற்று / பூ / சோலை | Personal growth progression |
| `student.missions` | Missions | பயிற்சிகள் / பணிகள் | Bite-sized practice activities |
| `student.starter` | Starter | தொடக்க நிலை | Tier 1 mission |
| `student.steady` | Steady | சீரான நிலை | Tier 2 mission |
| `student.stretch` | Stretch | சவால் நிலை | Tier 3 mission |
| `student.imStuck` | I'm stuck (Ask a doubt) | எனக்கு சந்தேகம் உள்ளது | Anonymous question submit |
| `student.badges` | Badges | பதக்கங்கள் | Milestone badges |
| `student.effortOverMarks` | Effort counts, never marks | முயற்சி மட்டுமே கணக்கிடப்படும் | Core product rule reassurance |

---

## 4. To-Do: Admin & Equity Keys (Pending Native Translation)

| Suggested Key | English Source | Proposed Tamil Translation | Context |
| :--- | :--- | :--- | :--- |
| `admin.overview` | School Overview | பள்ளி பொதுப் பார்வை | High-level aggregated dashboard |
| `admin.equity` | Engagement equity | சமத்துவ ஈடுபாடு | Band-level badge earnings |
| `admin.needsSupport` | Needs support | கூடுதல் ஆதரவு தேவை | Support level 3 band |
| `admin.onTrack` | On track | சரியான பாதையில் | Support level 2 band |
| `admin.strong` | Strong | சிறப்பான நிலையில் | Support level 1 band |
| `admin.equityAlert` | Equity Alert | சமத்துவ எச்சரிக்கை | Fairness gap $> 10$ points |
| `admin.guardrails` | Guardrails | பாதுகாப்பு விதிகள் | Responsible design settings |
| `admin.auditLogs` | Audit logs | தணிக்கைப் பதிவுகள் | Immutable action logging |

---

## 5. Dialect & Cultural Guidelines for Native Reviewer

1. **Honorifics and Respectful Address**:
   - When addressing parents, always use respectful plural forms (`அழைக்கவும்`, `உங்களின்`, `அவர்கள்`) rather than singular forms.
2. **Growth vs. Deficit Framing**:
   - Avoid stigmatizing words like `மட்டம்` (low) or `தோல்வி` (failure). Use `கூடுதல் பயிற்சி` (extra practice) and `ஆதரவு தேவை` (needs support).
3. **No Sensitive Language**:
   - As per **Rule 4**, never introduce terminology that implies caste, community, income class, or gender bias.

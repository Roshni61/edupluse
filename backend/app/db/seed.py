import logging
from datetime import datetime, date, timedelta, timezone
from sqlalchemy.orm import Session
from app.core.security import get_password_hash
from app.db.session import SessionLocal, engine, Base
from app.models.models import (
    School,
    User,
    Class,
    ClassTeacher,
    Student,
    ParentLink,
    Assessment,
    Score,
    Attendance,
    HomeworkRecord,
    SupportSnapshot,
    PlaybookAction,
    Mission,
    MissionAssignment,
    Badge,
    StudentBadge,
    XpLedger,
    GardenDrop,
    Doubt,
    CallWindow,
    Booking,
    CallbackQueue,
    ParentNote,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")

DEFAULT_PASSWORD = "Demo@1234"


def now_utc():
    return datetime.now(timezone.utc)


def seed_database(db: Session = None):
    own_session = False
    if db is None:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        own_session = True

    try:
        hashed_password = get_password_hash(DEFAULT_PASSWORD)

        # -------------------------------------------------------------
        # 1. School
        # -------------------------------------------------------------
        school = db.query(School).filter(School.name == "Chennai Model Secondary School").first()
        if not school:
            school = School(
                name="Chennai Model Secondary School",
                call_window_config={
                    "windows": ["am", "lunch", "pm", "eve"],
                    "evening_allowed_days": ["Tue", "Thu"],
                    "slot_duration_minutes": 5,
                },
                feature_flags={
                    "public_leaderboards": False,
                    "push_notifications_children": False,
                    "daily_mission_cap": 3,
                    "fairness_alert_threshold": 15,
                },
            )
            db.add(school)
            db.flush()
        logger.info(f"School: {school.name} ({school.id})")

        # -------------------------------------------------------------
        # 2. Call Windows (from WINDOWS in mock.ts)
        # -------------------------------------------------------------
        windows_data = [
            ("am", "Before school", "07:30", "08:15", ["Mon", "Tue", "Wed", "Thu", "Fri"], False),
            ("lunch", "Lunch break", "13:00", "13:40", ["Mon", "Tue", "Wed", "Thu", "Fri"], False),
            ("pm", "After school", "16:15", "17:00", ["Mon", "Tue", "Wed", "Thu", "Fri"], False),
            ("eve", "Evening (Tue and Thu)", "18:30", "19:30", ["Tue", "Thu"], True),
        ]
        call_windows_map = {}
        for wid, label, start, end, days, extended in windows_data:
            cw = db.query(CallWindow).filter(
                CallWindow.school_id == school.id,
                CallWindow.label == label
            ).first()
            if not cw:
                cw = CallWindow(
                    school_id=school.id,
                    label=label,
                    start_time=start,
                    end_time=end,
                    days=days,
                    is_extended=extended,
                )
                db.add(cw)
                db.flush()
            call_windows_map[wid] = cw

        # -------------------------------------------------------------
        # 3. Classes (9A plus other classes from HEAT_CLASSES)
        # -------------------------------------------------------------
        classes_data = [
            ("9A", "9"),
            ("8A", "8"),
            ("8B", "8"),
            ("9B", "9"),
            ("10A", "10"),
            ("10B", "10"),
        ]
        classes_map = {}
        for cname, grade in classes_data:
            cls_obj = db.query(Class).filter(
                Class.school_id == school.id,
                Class.name == cname
            ).first()
            if not cls_obj:
                cls_obj = Class(
                    school_id=school.id,
                    name=cname,
                    grade=grade,
                )
                db.add(cls_obj)
                db.flush()
            classes_map[cname] = cls_obj

        class_9a = classes_map["9A"]

        # -------------------------------------------------------------
        # 4. Demo Users & Class Teacher
        # -------------------------------------------------------------
        # Teacher: Ms. Priya
        teacher_user = db.query(User).filter(User.email == "teacher@edupulse.demo").first()
        if not teacher_user:
            teacher_user = User(
                school_id=school.id,
                role="teacher",
                name="Ms. Priya",
                email="teacher@edupulse.demo",
                password_hash=hashed_password,
                language="en",
                is_active=True,
            )
            db.add(teacher_user)
            db.flush()

        # Admin: Principal Sundaram
        admin_user = db.query(User).filter(User.email == "admin@edupulse.demo").first()
        if not admin_user:
            admin_user = User(
                school_id=school.id,
                role="admin",
                name="Principal Sundaram",
                email="admin@edupulse.demo",
                password_hash=hashed_password,
                language="en",
                is_active=True,
            )
            db.add(admin_user)
            db.flush()

        # Associate teacher with Class 9A for Maths
        ct = db.query(ClassTeacher).filter(
            ClassTeacher.class_id == class_9a.id,
            ClassTeacher.teacher_id == teacher_user.id,
            ClassTeacher.subject == "Maths",
        ).first()
        if not ct:
            ct = ClassTeacher(
                class_id=class_9a.id,
                teacher_id=teacher_user.id,
                subject="Maths",
            )
            db.add(ct)
            db.flush()

        # -------------------------------------------------------------
        # 5. 12 Badges (from BADGES in mock.ts)
        # -------------------------------------------------------------
        badges_data = [
            ("first-step", "First Step", "Effort", "Finish your very first mission.", "Footprints"),
            ("showed-up", "Showed Up", "Effort", "Complete 3 missions in one week.", "Sun"),
            ("try-again", "Tried Again", "Effort", "Retry a question after a hint.", "RotateCcw"),
            ("personal-best", "Personal Best", "Growth", "Beat your own previous best score.", "TrendingUp"),
            ("comeback", "Comeback", "Growth", "Return to missions after a break.", "Rocket"),
            ("topic-turnaround", "Topic Turnaround", "Growth", "Lift a weak topic by 15 points.", "Target"),
            ("steady-week", "Steady Week", "Consistency", "Do something every school day for a week. Rest days never break it.", "CalendarCheck"),
            ("early-bird", "Early Bird", "Consistency", "Submit homework before the deadline 3 times.", "Sunrise"),
            ("helping-hand", "Helping Hand", "Community", "Explain an idea to a classmate.", "HeartHandshake"),
            ("class-gardener", "Class Gardener", "Community", "Water the Class Garden 5 times.", "Sprout"),
            ("question-asker", "Question Asker", "Curiosity", "Ask a doubt. Good questions count.", "MessageCircleQuestion"),
            ("explorer", "Explorer", "Curiosity", "Try a Stretch mission.", "Compass"),
        ]
        badges_map = {}
        for code, name, category, how, icon in badges_data:
            badge = db.query(Badge).filter(Badge.code == code).first()
            if not badge:
                badge = Badge(
                    code=code,
                    name=name,
                    category=category,
                    how_to_earn=how,
                    icon=icon,
                )
                db.add(badge)
                db.flush()
            badges_map[code] = badge

        # -------------------------------------------------------------
        # 6. 3 Starter Missions (from MISSIONS in mock.ts)
        # -------------------------------------------------------------
        missions_data = [
            ("m1", "Fraction warm-up", 5, 30, "Starter", "quiz", "personal-best", "Three friendly questions. No marks lost for wrong answers."),
            ("m2", "Explain it to a friend", 3, 20, "Starter", "help", "helping-hand", "Pick one idea from today and explain it to a classmate."),
            ("m3", "Ask one doubt", 2, 15, "Starter", "ask", "question-asker", "Anything you're unsure about. Your teacher sees it without your name on it."),
        ]
        missions_map = {}
        for mid_code, title, mins, xp, tier, kind, bcode, blurb in missions_data:
            m = db.query(Mission).filter(Mission.title == title).first()
            badge_ref = badges_map.get(bcode)
            if not m:
                m = Mission(
                    title=title,
                    minutes=mins,
                    xp=xp,
                    tier=tier,
                    kind=kind,
                    badge_id=badge_ref.id if badge_ref else None,
                    blurb=blurb,
                    is_active=True,
                )
                db.add(m)
                db.flush()
            missions_map[mid_code] = m

            # Assign mission to Class 9A
            assign = db.query(MissionAssignment).filter(
                MissionAssignment.mission_id == m.id,
                MissionAssignment.class_id == class_9a.id,
            ).first()
            if not assign:
                assign = MissionAssignment(
                    mission_id=m.id,
                    class_id=class_9a.id,
                    assigned_by=teacher_user.id,
                )
                db.add(assign)
                db.flush()

        # -------------------------------------------------------------
        # 7. 8 Assessments (T1 to T8) for Class 9A
        # -------------------------------------------------------------
        assessments_map = {}
        today = date.today()
        for idx in range(8):
            label = f"T{idx + 1}"
            held_date = today - timedelta(weeks=8 - idx)
            ass = db.query(Assessment).filter(
                Assessment.class_id == class_9a.id,
                Assessment.label == label,
            ).first()
            if not ass:
                ass = Assessment(
                    class_id=class_9a.id,
                    subject="Maths",
                    label=label,
                    held_on=held_date,
                )
                db.add(ass)
                db.flush()
            assessments_map[label] = ass

        # -------------------------------------------------------------
        # 8. The 8 Students from mock.ts
        # -------------------------------------------------------------
        mock_students = [
            {
                "key": "karthik",
                "name": "Karthik",
                "email": "student@edupulse.demo",
                "roll_no": "9A-01",
                "subject": "Maths",
                "level": 3,
                "minutes": 8,
                "benefit": 95,
                "att": 76,
                "hw": 60,
                "reasons": [
                    "Maths is down 9 marks from his usual level of 73",
                    "4 Monday absences in the last 5 weeks",
                    "Homework late 3 times this month",
                ],
                "actions": [
                    "10-minute fractions practice mission",
                    "5-minute parent call",
                    "Pair with a peer helper for ratios",
                ],
                "parent_name": "Karthik's Mother",
                "parent_email": "parent@edupulse.demo",
                "parent_who": "Mother",
                "channel": "whatsapp",
                "pref_lang": "ta",
                "no_smartphone": False,
                "shift_worker": False,
                "scores": [74, 73, 75, 72, 68, 64, 61, 60],
                "badges": ["first-step", "showed-up"],
                "xp": 340,
            },
            {
                "key": "divya",
                "name": "Divya",
                "email": "divya@edupulse.demo",
                "roll_no": "9A-02",
                "subject": "Maths",
                "level": 2,
                "minutes": 10,
                "benefit": 88,
                "att": 71,
                "hw": 38,
                "reasons": [
                    "Attendance fell to 71% over four weeks",
                    "Homework missing 5 of the last 8",
                    "Good sign: finished 4 Garden missions in 2 weeks",
                ],
                "actions": [
                    "Short chat about what is getting in the way",
                    "Voice-note check-in with parent",
                    "Start with Starter-level missions",
                ],
                "parent_name": "Divya's Father",
                "parent_email": "divya.parent@edupulse.demo",
                "parent_who": "Father",
                "channel": "voice",
                "pref_lang": "en",
                "no_smartphone": False,
                "shift_worker": True,  # Night shift worker
                "scores": [44, 41, 43, 40, 42, 41, 43, 45],
                "badges": ["first-step", "class-gardener"],
                "xp": 180,
            },
            {
                "key": "arun",
                "name": "Arun",
                "email": "arun@edupulse.demo",
                "roll_no": "9A-03",
                "subject": "Science",
                "level": 2,
                "minutes": 6,
                "benefit": 70,
                "att": 88,
                "hw": 70,
                "reasons": [
                    "Science down 9 marks from his usual level of 66",
                    "Last two submissions were late",
                ],
                "actions": [
                    "Review the last lab report together",
                    "Try one Stretch mission",
                ],
                "parent_name": "Arun's Grandmother",
                "parent_email": "arun.parent@edupulse.demo",
                "parent_who": "Grandmother",
                "channel": "voice",
                "pref_lang": "ta",
                "no_smartphone": True,  # Feature phone
                "shift_worker": False,
                "scores": [66, 68, 65, 67, 63, 60, 58, 57],
                "badges": ["first-step"],
                "xp": 110,
            },
            {
                "key": "vikram",
                "name": "Vikram",
                "email": "vikram@edupulse.demo",
                "roll_no": "9A-04",
                "subject": "Maths",
                "level": 2,
                "minutes": 5,
                "benefit": 60,
                "att": 90,
                "hw": 80,
                "reasons": [
                    "Ratios and proportions are the weak topic",
                    "Quiz scores flat for three weeks",
                ],
                "actions": [
                    "Topic mini-lesson on ratios",
                    "Peer helper: Meena",
                ],
                "parent_name": "Vikram's Mother",
                "parent_email": "vikram.parent@edupulse.demo",
                "parent_who": "Mother",
                "channel": "sms",
                "pref_lang": "en",
                "no_smartphone": False,
                "shift_worker": False,
                "scores": [62, 60, 61, 59, 55, 54, 50, 52],
                "badges": ["first-step", "topic-turnaround"],
                "xp": 160,
            },
            {
                "key": "rahul",
                "name": "Rahul",
                "email": "rahul@edupulse.demo",
                "roll_no": "9A-05",
                "subject": "English",
                "level": 1,
                "minutes": 3,
                "benefit": 30,
                "att": 85,
                "hw": 85,
                "reasons": ["Small attendance dip on Fridays"],
                "actions": ["Friendly check-in"],
                "parent_name": "Rahul's Father",
                "parent_email": "rahul.parent@edupulse.demo",
                "parent_who": "Father",
                "channel": "whatsapp",
                "pref_lang": "en",
                "no_smartphone": False,
                "shift_worker": False,
                "scores": [68, 66, 67, 66, 65, 64, 66, 63],
                "badges": ["first-step", "steady-week"],
                "xp": 190,
            },
            {
                "key": "lakshmi",
                "name": "Lakshmi",
                "email": "lakshmi@edupulse.demo",
                "roll_no": "9A-06",
                "subject": "Maths",
                "level": 1,
                "minutes": 2,
                "benefit": 20,
                "att": 92,
                "hw": 90,
                "reasons": ["Marks drifting slightly lower, still within her normal range"],
                "actions": ["Keep an eye for two more weeks"],
                "parent_name": "Lakshmi's Mother",
                "parent_email": "lakshmi.parent@edupulse.demo",
                "parent_who": "Mother",
                "channel": "whatsapp",
                "pref_lang": "en",
                "no_smartphone": False,
                "shift_worker": False,
                "scores": [59, 60, 58, 61, 60, 59, 58, 57],
                "badges": ["first-step"],
                "xp": 120,
            },
            {
                "key": "meena",
                "name": "Meena",
                "email": "meena@edupulse.demo",
                "roll_no": "9A-07",
                "subject": "Maths",
                "level": 1,
                "minutes": 0,
                "benefit": 0,
                "att": 96,
                "hw": 95,
                "reasons": [],
                "actions": [],
                "parent_name": "Meena's Mother",
                "parent_email": "meena.parent@edupulse.demo",
                "parent_who": "Mother",
                "channel": "whatsapp",
                "pref_lang": "en",
                "no_smartphone": False,
                "shift_worker": False,
                "scores": [55, 57, 60, 62, 66, 69, 72, 74],
                "badges": ["first-step", "personal-best", "helping-hand"],
                "xp": 310,
            },
            {
                "key": "sana",
                "name": "Sana",
                "email": "sana@edupulse.demo",
                "roll_no": "9A-08",
                "subject": "Science",
                "level": 1,
                "minutes": 0,
                "benefit": 0,
                "att": 98,
                "hw": 100,
                "reasons": [],
                "actions": [],
                "parent_name": "Sana's Father",
                "parent_email": "sana.parent@edupulse.demo",
                "parent_who": "Father",
                "channel": "whatsapp",
                "pref_lang": "en",
                "no_smartphone": False,
                "shift_worker": False,
                "scores": [70, 72, 71, 74, 75, 77, 78, 80],
                "badges": ["first-step", "early-bird", "steady-week"],
                "xp": 350,
            },
        ]

        students_map = {}
        for sdata in mock_students:
            # Student User
            s_user = db.query(User).filter(User.email == sdata["email"]).first()
            if not s_user:
                s_user = User(
                    school_id=school.id,
                    role="student",
                    name=sdata["name"],
                    email=sdata["email"],
                    password_hash=hashed_password,
                    language=sdata.get("pref_lang", "en"),
                    is_active=True,
                )
                db.add(s_user)
                db.flush()

            # Parent User
            p_user = db.query(User).filter(User.email == sdata["parent_email"]).first()
            if not p_user:
                p_user = User(
                    school_id=school.id,
                    role="parent",
                    name=sdata["parent_name"],
                    email=sdata["parent_email"],
                    password_hash=hashed_password,
                    language=sdata.get("pref_lang", "en"),
                    is_active=True,
                )
                db.add(p_user)
                db.flush()

            # Student record
            stu = db.query(Student).filter(Student.user_id == s_user.id).first()
            if not stu:
                stu = Student(
                    user_id=s_user.id,
                    class_id=class_9a.id,
                    roll_no=sdata["roll_no"],
                )
                db.add(stu)
                db.flush()
            students_map[sdata["key"]] = stu

            # ParentLink
            pl = db.query(ParentLink).filter(
                ParentLink.parent_user_id == p_user.id,
                ParentLink.student_id == stu.id,
            ).first()
            if not pl:
                pl = ParentLink(
                    parent_user_id=p_user.id,
                    student_id=stu.id,
                    relation=sdata["parent_who"],
                    preferred_channel=sdata["channel"],
                    preferred_language=sdata.get("pref_lang", "en"),
                    no_smartphone=sdata.get("no_smartphone", False),
                    shift_worker=sdata.get("shift_worker", False),
                )
                db.add(pl)
                db.flush()

            # 8 Test Scores
            for idx, marks in enumerate(sdata["scores"]):
                label = f"T{idx + 1}"
                ass = assessments_map[label]
                sc = db.query(Score).filter(
                    Score.student_id == stu.id,
                    Score.assessment_id == ass.id,
                ).first()
                if not sc:
                    sc = Score(
                        student_id=stu.id,
                        assessment_id=ass.id,
                        marks=marks,
                    )
                    db.add(sc)
                    db.flush()

            # Attendance records
            target_att = sdata["att"]
            total_days = 25 if sdata["key"] == "karthik" else 20
            present_target = round((target_att / 100.0) * total_days)
            existing_att = db.query(Attendance).filter(Attendance.student_id == stu.id).count()
            if existing_att == 0:
                absences_needed = total_days - present_target
                absent_indices = set()
                if sdata["key"] == "karthik":
                    mon_indices = [i for i in range(total_days) if (today - timedelta(days=total_days - i)).weekday() == 0]
                    absent_indices.update(mon_indices[:4])
                for idx in range(total_days):
                    if len(absent_indices) >= absences_needed:
                        break
                    absent_indices.add(idx)

                for day_idx in range(total_days):
                    att_date = today - timedelta(days=total_days - day_idx)
                    is_present = (day_idx not in absent_indices)
                    att_rec = Attendance(
                        student_id=stu.id,
                        date=att_date,
                        present=is_present,
                    )
                    db.add(att_rec)

            # Homework records (10 assignments)
            target_hw = sdata["hw"]
            existing_hw = db.query(HomeworkRecord).filter(HomeworkRecord.student_id == stu.id).count()
            if existing_hw == 0:
                for hw_idx in range(10):
                    hw_date = today - timedelta(days=20 - (hw_idx * 2))
                    if sdata["key"] == "divya" and hw_idx >= 2:
                        hw_status = "missing" if (hw_idx % 2 == 0) else "late"
                    elif sdata["key"] == "karthik" and hw_idx in (7, 8, 9):
                        hw_status = "late"
                    elif (hw_idx / 10.0) * 100 < target_hw:
                        hw_status = "on_time"
                    else:
                        hw_status = "late" if hw_idx % 2 == 0 else "missing"

                    hw_rec = HomeworkRecord(
                        student_id=stu.id,
                        subject="Maths",
                        due_date=hw_date,
                        status=hw_status,
                    )
                    db.add(hw_rec)

            # SupportSnapshot (Change-from-Self analysis)
            base_score = round(sum(sdata["scores"][:4]) / 4)
            drop_score = max(0, base_score - sdata["scores"][-1])
            snap = db.query(SupportSnapshot).filter(SupportSnapshot.student_id == stu.id).first()
            if not snap:
                snap = SupportSnapshot(
                    student_id=stu.id,
                    level=sdata["level"],
                    reasons=sdata["reasons"],
                    minutes=sdata["minutes"],
                    benefit=sdata["benefit"],
                    baseline=base_score,
                    drop=drop_score,
                )
                db.add(snap)
                db.flush()

            # Playbook Actions
            for action in sdata["actions"]:
                pa = db.query(PlaybookAction).filter(
                    PlaybookAction.student_id == stu.id,
                    PlaybookAction.action == action,
                ).first()
                if not pa:
                    pa = PlaybookAction(
                        student_id=stu.id,
                        teacher_id=teacher_user.id,
                        action=action,
                        note="Initial support playbook action from teacher diagnosis.",
                        logged_at=now_utc(),
                        followup_due=today + timedelta(days=14),
                    )
                    db.add(pa)

            # Badges earned
            for bcode in sdata.get("badges", []):
                badge_obj = badges_map.get(bcode)
                if badge_obj:
                    sb = db.query(StudentBadge).filter(
                        StudentBadge.student_id == stu.id,
                        StudentBadge.badge_id == badge_obj.id,
                    ).first()
                    if not sb:
                        sb = StudentBadge(
                            student_id=stu.id,
                            badge_id=badge_obj.id,
                            earned_at=now_utc() - timedelta(days=3),
                        )
                        db.add(sb)

            # XP Ledger
            xp_total = db.query(XpLedger).filter(XpLedger.student_id == stu.id).count()
            if xp_total == 0 and sdata.get("xp", 0) > 0:
                # Add effort-based XP entry
                xp_entry = XpLedger(
                    student_id=stu.id,
                    delta=sdata["xp"],
                    reason="Completed learning missions and showed consistent effort",
                    ref_id="seed_initial_xp",
                )
                db.add(xp_entry)

        # -------------------------------------------------------------
        # 9. Class Garden Drops (31 drops from store.tsx / mock.ts)
        # -------------------------------------------------------------
        current_drops = db.query(GardenDrop).filter(GardenDrop.class_id == class_9a.id).count()
        if current_drops < 31:
            for d in range(31 - current_drops):
                drop_rec = GardenDrop(
                    class_id=class_9a.id,
                    student_id=None,  # Anonymous drops (Rule 2)
                    created_at=now_utc() - timedelta(hours=31 - d),
                )
                db.add(drop_rec)

        # -------------------------------------------------------------
        # 10. Bookings from BOOKED in mock.ts
        # -------------------------------------------------------------
        booked_entries = [
            ("meena", "Meena's Mother", "Mon", "07:35", "am", "call"),
            ("arun", "Arun's Grandmother", "Tue", "13:05", "lunch", "voice"),
            ("vikram", "Vikram's Mother", "Wed", "16:20", "pm", "call"),
            ("rahul", "Rahul's Father", "Thu", "18:30", "eve", "call"),
        ]
        # Next week dates for Mon, Tue, Wed, Thu
        for skey, p_label, day_name, start_t, win_id, meth in booked_entries:
            stu_obj = students_map.get(skey)
            if not stu_obj:
                continue
            parent_link = stu_obj.parents[0] if stu_obj.parents else None
            if not parent_link:
                continue

            day_offset = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4}[day_name]
            booking_date = today + timedelta(days=(7 - today.weekday() + day_offset))

            bkg = db.query(Booking).filter(
                Booking.teacher_id == teacher_user.id,
                Booking.date == booking_date,
                Booking.start_time == start_t,
            ).first()
            if not bkg:
                bkg = Booking(
                    parent_user_id=parent_link.parent_user_id,
                    student_id=stu_obj.id,
                    teacher_id=teacher_user.id,
                    date=booking_date,
                    start_time=start_t,
                    duration_min=5,
                    method=meth,
                    reminders=["whatsapp", "hour"],
                    status="confirmed",
                )
                db.add(bkg)

        # -------------------------------------------------------------
        # 11. Callback Queue from UNREACHED in mock.ts
        # -------------------------------------------------------------
        unreached_data = [
            ("divya", "Night-shift worker. Two missed calls.", "pending"),
            ("arun", "Feature phone. Tamil voice call not answered twice.", "pending"),
            ("vikram", "No reply to the weekly summary for 2 weeks.", "pending"),
        ]
        for skey, reason, status in unreached_data:
            stu_obj = students_map.get(skey)
            if stu_obj and stu_obj.parents:
                parent_link = stu_obj.parents[0]
                cb = db.query(CallbackQueue).filter(
                    CallbackQueue.student_id == stu_obj.id,
                    CallbackQueue.reason == reason,
                ).first()
                if not cb:
                    cb = CallbackQueue(
                        student_id=stu_obj.id,
                        parent_user_id=parent_link.parent_user_id,
                        reason=reason,
                        status=status,
                    )
                    db.add(cb)

        # -------------------------------------------------------------
        # 12. Anonymous Doubts for Class 9A (Rule 6: NO student_id)
        # -------------------------------------------------------------
        initial_doubts = [
            ("Fractions practice", "I get confused when subtracting fractions with unlike denominators."),
            ("Ratios", "How do we simplify ratios with decimals?"),
        ]
        for topic, msg in initial_doubts:
            dbt = db.query(Doubt).filter(
                Doubt.class_id == class_9a.id,
                Doubt.text.contains(topic),
            ).first()
            if not dbt:
                dbt = Doubt(
                    class_id=class_9a.id,
                    text=f"[{topic}] {msg}",
                    resolved=False,
                    created_at=now_utc() - timedelta(days=1),
                )
                db.add(dbt)

        # -------------------------------------------------------------
        # 13. Karthik's Parent Note (approved/sent demo state)
        # -------------------------------------------------------------
        karthik_stu = students_map["karthik"]
        p_note = db.query(ParentNote).filter(ParentNote.student_id == karthik_stu.id).first()
        if not p_note:
            p_note = ParentNote(
                student_id=karthik_stu.id,
                teacher_id=teacher_user.id,
                body_en="Karthik has been working hard on practice missions. Maths is down 9 marks from his usual level of 73. A short 10-minute practice at home could help, and the class teacher will check in this week.",
                body_ta="அறிவியலில் கார்த்திக் சிறப்பாகச் செய்து வருகிறார்; பயிற்சிப் பணிகளையும் முடித்து வருகிறார். கணிதத்தில் கடந்த மூன்று தேர்வுகளில் மதிப்பெண் சற்றுக் குறைந்துள்ளது. வீட்டில் தினமும் 10 நிமிடம் பின்னங்கள் பயிற்சி செய்தால் உதவும். வகுப்பாசிரியர் இந்த வாரம் உங்களைத் தொடர்பு கொள்வார்.",
                status="approved",
                channel="WhatsApp",
            )
            db.add(p_note)

        db.commit()
        logger.info("Successfully seeded all EduPulse prototype data idempotently!")
    except Exception as e:
        db.rollback()
        logger.error(f"Error during seeding: {e}")
        raise
    finally:
        if own_session:
            db.close()


if __name__ == "__main__":
    seed_database()

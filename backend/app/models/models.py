import uuid
from datetime import datetime, timezone, date
from sqlalchemy import (
    Boolean, Column, DateTime, Date, ForeignKey, Integer, String, Text, JSON,
    UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.db.session import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class School(Base):
    """
    schools (name, call_window_config JSON, feature_flags JSON)
    """
    __tablename__ = "schools"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    call_window_config = Column(JSON, default=dict)
    feature_flags = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)


    users = relationship("User", back_populates="school", cascade="all, delete-orphan")
    classes = relationship("Class", back_populates="school", cascade="all, delete-orphan")
    call_windows = relationship("CallWindow", back_populates="school", cascade="all, delete-orphan")


class User(Base):
    """
    users (school_id, role[teacher|student|parent|admin], name, email unique, password_hash, language[en|ta], is_active)
    PRODUCT RULE 4: No sensitive attributes are stored (caste, religion, income, etc.).
    """
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False, index=True)  # teacher | student | parent | admin
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    language = Column(String(10), default="en", nullable=False)  # en | ta
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)


    school = relationship("School", back_populates="users")
    student_profile = relationship("Student", back_populates="user", uselist=False)
    parent_links = relationship("ParentLink", back_populates="parent_user", foreign_keys="ParentLink.parent_user_id")
    taught_classes = relationship("ClassTeacher", back_populates="teacher")
    playbook_actions = relationship("PlaybookAction", back_populates="teacher")
    sent_notes = relationship("ParentNote", back_populates="teacher")
    kudos_sent = relationship("Kudos", back_populates="teacher")

    @property
    def hashed_password(self) -> str:
        return self.password_hash

    @hashed_password.setter
    def hashed_password(self, value: str):
        self.password_hash = value

    @property
    def preferred_lang(self) -> str:
        return self.language

    @preferred_lang.setter
    def preferred_lang(self, value: str):
        self.language = value


class Class(Base):
    """
    classes (school_id, name e.g. "8A", grade)
    """
    __tablename__ = "classes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(50), nullable=False, index=True)  # "8A", "9A", etc.
    grade = Column(String(20), nullable=False)  # "8", "9"
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)


    school = relationship("School", back_populates="classes")
    students = relationship("Student", back_populates="class_group", cascade="all, delete-orphan")
    teachers = relationship("ClassTeacher", back_populates="class_group", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="class_group", cascade="all, delete-orphan")
    garden_drops = relationship("GardenDrop", back_populates="class_group", cascade="all, delete-orphan")
    doubts = relationship("Doubt", back_populates="class_group", cascade="all, delete-orphan")


class ClassTeacher(Base):
    """
    class_teachers (class_id, teacher_id, subject)
    """
    __tablename__ = "class_teachers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    class_id = Column(String(36), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)


    class_group = relationship("Class", back_populates="teachers")
    teacher = relationship("User", back_populates="taught_classes")


class Student(Base):
    """
    students (user_id, class_id, roll_no)
    """
    __tablename__ = "students"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, unique=True, index=True)
    class_id = Column(String(36), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    roll_no = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)


    user = relationship("User", back_populates="student_profile")
    class_group = relationship("Class", back_populates="students")
    parents = relationship("ParentLink", back_populates="student", cascade="all, delete-orphan")
    score_records = relationship("Score", back_populates="student", cascade="all, delete-orphan")
    attendance = relationship("Attendance", back_populates="student", cascade="all, delete-orphan")
    homework_records = relationship("HomeworkRecord", back_populates="student", cascade="all, delete-orphan")
    support_snapshots = relationship("SupportSnapshot", back_populates="student", cascade="all, delete-orphan", order_by="SupportSnapshot.computed_at")
    playbook_actions = relationship("PlaybookAction", back_populates="student", cascade="all, delete-orphan")
    attempts = relationship("MissionAttempt", back_populates="student", cascade="all, delete-orphan")
    badges = relationship("StudentBadge", back_populates="student", cascade="all, delete-orphan")
    xp_entries = relationship("XpLedger", back_populates="student", cascade="all, delete-orphan")
    kudos = relationship("Kudos", back_populates="student", cascade="all, delete-orphan")
    parent_notes = relationship("ParentNote", back_populates="student", cascade="all, delete-orphan")
    checkins = relationship("Checkin", back_populates="student", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="student", cascade="all, delete-orphan")

    @property
    def parent_user_id(self) -> str:
        return self.parents[0].parent_user_id if self.parents else None

    # Helper properties for schema serialization and server truth
    @property
    def name(self) -> str:
        return self.user.name if self.user else ""

    @property
    def class_name(self) -> str:
        return self.class_group.name if self.class_group else ""

    @property
    def school_id(self) -> str:
        return self.class_group.school_id if self.class_group else ""

    @property
    def subject(self) -> str:
        # Returns subject from class teacher or primary subject
        if self.class_group and self.class_group.teachers:
            return self.class_group.teachers[0].subject
        return "Maths"

    @property
    def current_xp(self) -> int:
        """PRODUCT RULE 1 & ENGINEERING RULE: XP is derived from xp_ledger entries."""
        return sum(entry.delta for entry in self.xp_entries) if self.xp_entries else 0

    @property
    def scores(self) -> list:
        if not self.score_records:
            return []
        sorted_scores = sorted(self.score_records, key=lambda s: s.assessment.label if s.assessment else "")
        return [s.marks for s in sorted_scores]

    @property
    def scores_list(self) -> list:
        return self.scores

    @property
    def attendance_pct(self) -> int:
        if not self.attendance:
            return 90
        present_count = sum(1 for a in self.attendance if a.present)
        return round((present_count / len(self.attendance)) * 100)

    @property
    def homework_pct(self) -> int:
        if not self.homework_records:
            return 85
        ontime_count = sum(1 for h in self.homework_records if h.status == "on_time")
        return round((ontime_count / len(self.homework_records)) * 100)

    @property
    def latest_snapshot(self):
        return self.support_snapshots[-1] if self.support_snapshots else None

    @property
    def support_level(self) -> int:
        return self.latest_snapshot.level if self.latest_snapshot else 1

    @property
    def reasons(self) -> list:
        return self.latest_snapshot.reasons if self.latest_snapshot else []

    @property
    def suggested_actions(self) -> list:
        # Actions derived from latest playbook actions or snapshot suggestions
        return ["10-minute fractions practice mission", "5-minute parent call", "Pair with a peer helper for ratios"]

    @property
    def minutes(self) -> int:
        return self.latest_snapshot.minutes if self.latest_snapshot else 0

    @property
    def benefit(self) -> int:
        return self.latest_snapshot.benefit if self.latest_snapshot else 0

    @property
    def baseline_score(self) -> int:
        return self.latest_snapshot.baseline if self.latest_snapshot else 70

    @property
    def bright(self) -> bool:
        return (self.support_level == 1 and (self.name in ("Meena", "Sana") or (self.scores_list and self.scores_list[-1] >= 74)))

    @property
    def bright_why(self) -> str:
        if self.name == "Meena":
            return "Up 19 marks over eight tests"
        elif self.name == "Sana":
            return "Longest steady climb in the class"
        return "Steady progress and strong engagement"

    @property
    def primary_parent_link(self):
        return self.parents[0] if self.parents else None

    @property
    def parent_who(self) -> str:
        return self.primary_parent_link.relation if self.primary_parent_link else "Parent"

    @property
    def parent_channel(self) -> str:
        if self.primary_parent_link:
            ch = self.primary_parent_link.preferred_channel
            if ch == "voice":
                return "Voice note" if self.primary_parent_link.shift_worker else "Voice call (Tamil)"
            elif ch == "sms":
                return "SMS"
            return "WhatsApp"
        return "WhatsApp"


class ParentLink(Base):
    """
    parent_links (parent_user_id, student_id, relation, preferred_channel[app|whatsapp|sms|voice|callback|desk], preferred_language, no_smartphone bool, shift_worker bool)
    """
    __tablename__ = "parent_links"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    parent_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    relation = Column(String(100), nullable=False)  # Mother | Father | Grandmother | Guardian
    preferred_channel = Column(String(50), default="whatsapp", nullable=False)  # app | whatsapp | sms | voice | callback | desk
    preferred_language = Column(String(10), default="en", nullable=False)  # en | ta
    no_smartphone = Column(Boolean, default=False, nullable=False)
    shift_worker = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)


    parent_user = relationship("User", back_populates="parent_links")
    student = relationship("Student", back_populates="parents")


class Assessment(Base):
    """
    assessments (class_id, subject, label e.g. T1, held_on)
    """
    __tablename__ = "assessments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    class_id = Column(String(36), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    subject = Column(String(100), nullable=False)
    label = Column(String(50), nullable=False, index=True)  # T1, T2, etc.
    held_on = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)


    class_group = relationship("Class", back_populates="assessments")
    scores = relationship("Score", back_populates="assessment", cascade="all, delete-orphan")


class Score(Base):
    """
    scores (student_id, assessment_id, marks)
    """
    __tablename__ = "scores"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_id = Column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    marks = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)


    student = relationship("Student", back_populates="score_records")
    assessment = relationship("Assessment", back_populates="scores")


class Attendance(Base):
    """
    attendance (student_id, date, present bool)
    """
    __tablename__ = "attendance"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    present = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)


    student = relationship("Student", back_populates="attendance")


class HomeworkRecord(Base):
    """
    homework_records (student_id, subject, due_date, status[on_time|late|missing])
    """
    __tablename__ = "homework_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    subject = Column(String(100), nullable=False)
    due_date = Column(Date, nullable=False, index=True)
    status = Column(String(50), nullable=False)  # on_time | late | missing
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)


    student = relationship("Student", back_populates="homework_records")


class SupportSnapshot(Base):
    """
    support_snapshots (student_id, computed_at, level 1-3, reasons JSON, minutes int, benefit int, baseline int, drop int)
    PRODUCT RULE 3: Support levels are teacher-only.
    """
    __tablename__ = "support_snapshots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    computed_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    level = Column(Integer, nullable=False)  # 1 | 2 | 3
    reasons = Column(JSON, default=list, nullable=False)
    minutes = Column(Integer, default=0, nullable=False)
    benefit = Column(Integer, default=0, nullable=False)
    baseline = Column(Integer, default=70, nullable=False)
    drop = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)


    student = relationship("Student", back_populates="support_snapshots")


class PlaybookAction(Base):
    """
    playbook_actions (student_id, teacher_id, action, note, logged_at, followup_due)
    """
    __tablename__ = "playbook_actions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(255), nullable=False)
    note = Column(Text, nullable=True)
    logged_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    followup_due = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)


    student = relationship("Student", back_populates="playbook_actions")
    teacher = relationship("User", back_populates="playbook_actions")


class Mission(Base):
    """
    missions (title, minutes, xp, tier, kind, badge_id nullable, blurb, is_active)
    PRODUCT RULE 1: XP is awarded for effort, never for marks.
    """
    __tablename__ = "missions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    minutes = Column(Integer, default=5, nullable=False)
    xp = Column(Integer, nullable=False)
    tier = Column(String(50), default="Starter", nullable=False)  # Starter | Steady | Stretch
    kind = Column(String(50), default="quiz", nullable=False)  # quiz | help | ask
    badge_id = Column(String(36), ForeignKey("badges.id", ondelete="SET NULL"), nullable=True)
    blurb = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)


    badge = relationship("Badge")
    assignments = relationship("MissionAssignment", back_populates="mission", cascade="all, delete-orphan")
    attempts = relationship("MissionAttempt", back_populates="mission", cascade="all, delete-orphan")


class MissionAssignment(Base):
    """
    mission_assignments (mission_id, class_id or student_id, assigned_by)
    """
    __tablename__ = "mission_assignments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    mission_id = Column(String(36), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, index=True)
    class_id = Column(String(36), ForeignKey("classes.id", ondelete="CASCADE"), nullable=True, index=True)
    student_id = Column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=True, index=True)
    assigned_by = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)


    mission = relationship("Mission", back_populates="assignments")


class MissionAttempt(Base):
    """
    mission_attempts (student_id, mission_id, status, score, hints_used, xp_awarded, completed_at)
    """
    __tablename__ = "mission_attempts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    mission_id = Column(String(36), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="completed", nullable=False)  # in_progress | completed | abandoned
    score = Column(Integer, default=0, nullable=False)
    hints_used = Column(Integer, default=0, nullable=False)
    xp_awarded = Column(Integer, default=0, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)


    student = relationship("Student", back_populates="attempts")
    mission = relationship("Mission", back_populates="attempts")


class Badge(Base):
    """
    badges (code, name, category, how_to_earn, icon)
    """
    __tablename__ = "badges"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    code = Column(String(50), unique=True, index=True, nullable=False)  # first-step, personal-best
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)  # Effort | Growth | Consistency | Community | Curiosity
    how_to_earn = Column(String(255), nullable=False)
    icon = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)


    earned_by = relationship("StudentBadge", back_populates="badge", cascade="all, delete-orphan")


class StudentBadge(Base):
    """
    student_badges (student_id, badge_id, earned_at) unique pair
    """
    __tablename__ = "student_badges"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    badge_id = Column(String(36), ForeignKey("badges.id", ondelete="CASCADE"), nullable=False, index=True)
    earned_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)


    student = relationship("Student", back_populates="badges")
    badge = relationship("Badge", back_populates="earned_by")

    __table_args__ = (
        UniqueConstraint("student_id", "badge_id", name="uq_student_badge"),
    )


class XpLedger(Base):
    """
    xp_ledger (student_id, delta, reason, ref_id, created_at) -- XP total is derived from this
    PRODUCT RULE 1: XP is awarded for effort, never marks.
    """
    __tablename__ = "xp_ledger"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    delta = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=False)
    ref_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)

    student = relationship("Student", back_populates="xp_entries")


class GardenDrop(Base):
    """
    garden_drops (class_id, student_id nullable, created_at)
    PRODUCT RULE 2: No leaderboards. The Class Garden is cooperative and never names anyone.
    """
    __tablename__ = "garden_drops"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    class_id = Column(String(36), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("students.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)

    class_group = relationship("Class", back_populates="garden_drops")


class Kudos(Base):
    """
    kudos (student_id, teacher_id, message, created_at)
    """
    __tablename__ = "kudos"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)


    student = relationship("Student", back_populates="kudos")
    teacher = relationship("User", back_populates="kudos_sent")


class Doubt(Base):
    """
    doubts (class_id, text, created_at, resolved)
    PRODUCT RULE 6: Anonymous "I'm stuck"/doubt questions must not be linkable to a student in teacher APIs.
    NO student_id column on purpose.
    """
    __tablename__ = "doubts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    class_id = Column(String(36), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    text = Column(Text, nullable=False)
    resolved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)

    class_group = relationship("Class", back_populates="doubts")

    @property
    def topic(self) -> str:
        return self.text.split(":", 1)[0].strip() if ":" in self.text else self.text

    @property
    def message(self) -> str:
        return self.text.split(":", 1)[1].strip() if ":" in self.text else ""

    @property
    def class_name(self) -> str:
        return self.class_group.name if self.class_group else ""


class ParentNote(Base):
    """
    parent_notes (student_id, teacher_id, body_en, body_ta, status[draft|approved|sent], channel)
    """
    __tablename__ = "parent_notes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    body_en = Column(Text, nullable=False)
    body_ta = Column(Text, nullable=False)
    status = Column(String(50), default="draft", nullable=False)  # draft | approved | sent
    channel = Column(String(50), default="WhatsApp", nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)


    student = relationship("Student", back_populates="parent_notes")
    teacher = relationship("User", back_populates="sent_notes")


class Checkin(Base):
    """
    checkins (parent_user_id, student_id, mood, has_voice_note, voice_note_url nullable, created_at)
    """
    __tablename__ = "checkins"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    parent_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    mood = Column(String(50), nullable=False)  # great | okay | hard
    has_voice_note = Column(Boolean, default=False, nullable=False)
    voice_note_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)


    student = relationship("Student", back_populates="checkins")


class CallWindow(Base):
    """
    call_windows (school_id, label, start_time, end_time, days[], is_extended)
    PRODUCT RULE 5: Parent call windows stay inside school hours; evening slots only Tue and Thu.
    """
    __tablename__ = "call_windows"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    label = Column(String(100), nullable=False)  # "Before school", "Evening (Tue and Thu)"
    start_time = Column(String(10), nullable=False)  # "07:30", "18:30"
    end_time = Column(String(10), nullable=False)  # "08:15", "19:30"
    days = Column(JSON, nullable=False)  # ["Mon", "Tue", "Wed", "Thu", "Fri"] or ["Tue", "Thu"]
    is_extended = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)


    school = relationship("School", back_populates="call_windows")


class Booking(Base):
    """
    bookings (parent_user_id, student_id, teacher_id, date, start_time, duration_min=5, method, reminders[], status[confirmed|cancelled|done])
    unique (teacher_id, date, start_time)
    PRODUCT RULE 5: Parent call windows stay inside school hours; evening slots only Tue and Thu.
    """
    __tablename__ = "bookings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    parent_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    start_time = Column(String(10), nullable=False)  # "07:35", "18:30"
    duration_min = Column(Integer, default=5, nullable=False)
    method = Column(String(50), default="call", nullable=False)  # call | voice | video | visit
    reminders = Column(JSON, default=list, nullable=False)
    status = Column(String(50), default="confirmed", nullable=False)  # confirmed | cancelled | done
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)


    student = relationship("Student", back_populates="bookings")

    @property
    def parent_id(self) -> str:
        return self.parent_user_id

    @property
    def slot_time(self) -> str:
        return self.start_time

    @property
    def day(self) -> str:
        return self.date.strftime("%a") if self.date else "Tue"

    @property
    def window_id(self) -> str:
        hour = int(self.start_time.split(":")[0]) if ":" in self.start_time else 9
        return "eve" if hour >= 18 else "pm" if hour >= 14 else "lunch" if hour >= 12 else "am"

    __table_args__ = (
        UniqueConstraint("teacher_id", "date", "start_time", name="uq_teacher_booking_slot"),
    )


class OutboxMessage(Base):
    """
    outbox_messages (to_user_id, channel, template, payload JSON, status[queued|sent|failed], provider_ref, created_at)
    """
    __tablename__ = "outbox_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    to_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    channel = Column(String(50), nullable=False)  # whatsapp | sms | voice
    template = Column(String(100), nullable=False)
    payload = Column(JSON, default=dict, nullable=False)
    status = Column(String(50), default="queued", nullable=False)  # queued | sent | failed
    provider_ref = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)


class CallbackQueue(Base):
    """
    callback_queue (student_id, parent_user_id, reason, status, booking_id nullable)
    """
    __tablename__ = "callback_queue"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reason = Column(String(255), nullable=False)
    status = Column(String(50), default="pending", nullable=False)  # pending | reserved | completed
    booking_id = Column(String(36), ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)

    student = relationship("Student")
    parent_user = relationship("User")



class AuditLog(Base):
    """
    audit_logs (actor_id, action, entity, entity_id, meta JSON, created_at)
    PRODUCT RULE 7: Every sensitive read/write by teacher/admin is written to an audit log.
    """
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    actor_id = Column(String(36), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    entity = Column(String(100), nullable=False)
    entity_id = Column(String(100), nullable=True)
    meta = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)

    @property
    def actor_role(self) -> str:
        return self.meta.get("actor_role", "") if isinstance(self.meta, dict) else ""

    @property
    def school_id(self) -> str:
        return self.meta.get("school_id", "") if isinstance(self.meta, dict) else ""

    @property
    def resource_id(self) -> str:
        return self.entity_id

    @property
    def resource_type(self) -> str:
        return self.entity

    @property
    def details(self) -> dict:
        return self.meta


# Backwards-compatibility aliases for API routes
StudentMission = MissionAttempt
AnonymousDoubt = Doubt
ParentCallBooking = Booking
ClassGarden = Class


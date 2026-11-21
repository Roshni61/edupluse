from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, field_validator, ConfigDict


# Health Check Schemas
class HealthResponse(BaseModel):
    status: str = "ok"
    app: str = "EduPulse"
    environment: str
    version: str = "0.1.0"
    database_status: str = "connected"


# User & Auth Schemas
class UserBase(BaseModel):
    email: str
    name: str
    role: str  # "teacher" | "student" | "parent" | "admin"
    preferred_lang: str = "en"  # "en" | "ta"

    @field_validator("preferred_lang")
    def validate_lang(cls, v: str) -> str:
        if v not in ("en", "ta"):
            raise ValueError("Supported languages are 'en' and 'ta'")
        return v


class UserCreate(UserBase):
    password: str
    school_id: str


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    language: str = "en"
    is_active: bool = True
    created_at: datetime


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 min
    user: UserResponse


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


class LogoutResponse(BaseModel):
    message: str = "Logged out successfully"


# Student Schemas
# PRODUCT RULE 3: Students see growth only, never their support level.
class StudentGrowthView(BaseModel):
    """Student view: shows growth against self only."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    class_name: str
    subject: str
    current_xp: int
    baseline_score: int
    scores: List[int]
    attendance_pct: int
    homework_pct: int


class StudentTeacherView(BaseModel):
    """Teacher/Admin view: includes early warning support level and action recommendations."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    class_name: str
    subject: str
    current_xp: int
    baseline_score: int
    scores: List[int]
    attendance_pct: int
    homework_pct: int
    support_level: int
    reasons: List[str]
    suggested_actions: List[str]
    benefit: int
    minutes: int
    bright: bool
    bright_why: Optional[str] = None
    parent_who: str
    parent_channel: str


class StudentParentView(BaseModel):
    """Parent view: child progress and attendance."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    class_name: str
    subject: str
    attendance_pct: int
    homework_pct: int
    parent_who: str
    parent_channel: str


# Badge Schemas
class BadgeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    category: str
    how_to_earn: str
    icon: str


# Mission Schemas
# PRODUCT RULE 1: XP awarded for effort, never for marks.
class MissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    minutes: int
    xp: int
    tier: str
    kind: str
    badge_id: Optional[str] = None
    blurb: str
    active: bool


class MissionCompleteRequest(BaseModel):
    mission_id: str
    tries: int = Field(default=1, ge=1)


class MissionCompleteResponse(BaseModel):
    xp_awarded: int
    new_total_xp: int
    badge_unlocked: Optional[str] = None
    message: str


# Class Garden Schemas
# PRODUCT RULE 2: No leaderboards. The Class Garden is cooperative and never names anyone.
class ClassGardenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    class_name: str
    total_drops: int
    target_drops: int = 48
    stage: str


# Anonymous Doubt Schemas
# PRODUCT RULE 6: Anonymous "I'm stuck"/doubt questions must not be linkable to a student in teacher APIs.
class AnonymousDoubtCreate(BaseModel):
    class_name: str
    topic: str
    message: Optional[str] = None


class AnonymousDoubtResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    class_name: str
    topic: str
    message: Optional[str] = None
    created_at: datetime


# Parent Call Booking Schemas
# PRODUCT RULE 5: Parent call windows stay inside school hours; evening slots only Tue and Thu.
class CallBookingCreate(BaseModel):
    day: str  # Mon, Tue, Wed, Thu, Fri
    slot_time: str
    window_id: str  # am, lunch, pm, eve
    method: str
    reminders: List[str] = []

    @field_validator("day")
    def validate_day(cls, v: str) -> str:
        valid_days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
        if v not in valid_days:
            raise ValueError(f"Booking day must be one of {valid_days}")
        return v


class CallBookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    parent_id: str
    day: str
    slot_time: str
    window_id: str
    method: str
    reminders: List[str]
    created_at: datetime


# Audit Log Schemas
# PRODUCT RULE 7: Every sensitive read/write by teacher/admin is written to an audit log.
class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor_id: str
    actor_role: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    created_at: datetime


# Teacher Portal Schemas
class BrightSpotView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    bright_why: Optional[str] = None
    kudos_sent: bool = False


class TodaySummary(BaseModel):
    class_name: str = "9A"
    total_students: int = 24
    watered_yesterday: int = 18
    parents_reached: int = 21
    garden_drops: int = 31
    target_garden_drops: int = 48


class TeacherTodayPlanResponse(BaseModel):
    budget: int
    used: int
    in_plan: List[StudentTeacherView]
    later: List[StudentTeacherView]
    bright: List[BrightSpotView]
    summary: TodaySummary


class ChartPoint(BaseModel):
    t: str
    score: int
    avg: int


class TeacherStudentDetailResponse(BaseModel):
    student: StudentTeacherView
    tests: List[str]
    class_avg: List[int]
    chart_data: List[ChartPoint]
    baseline: int
    drop: int
    reasons: List[str]
    suggested_actions: List[str]
    logged_actions: List[str]
    parent_note_status: Optional[str] = None


class WhatIfRequest(BaseModel):
    attendance: int = Field(ge=0, le=100)
    homework: int = Field(ge=0, le=100)


class WhatIfResponse(BaseModel):
    attendance: int
    homework: int
    drop: int
    score: float
    level: int


class PlaybookActionCreate(BaseModel):
    action: str
    note: Optional[str] = None


class PlaybookActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_id: str
    teacher_id: str
    action: str
    note: Optional[str] = None
    logged_at: datetime
    followup_due: Optional[Any] = None


class ParentNoteDraftResponse(BaseModel):
    student_id: str
    student_name: str
    parent_who: str
    channel: str
    preferred_language: str
    body_en: str
    body_ta: str
    status: str
    sent: bool


class ParentNoteApproveRequest(BaseModel):
    body_en: str
    body_ta: Optional[str] = None
    approved: bool = True
    channel: Optional[str] = None


class ParentNoteApproveResponse(BaseModel):
    status: str
    message: str
    note_id: str
    outbox_id: Optional[str] = None


class KudosCreate(BaseModel):
    student_id: str
    message: Optional[str] = "Great effort and steady growth!"


class KudosResponse(BaseModel):
    success: bool
    message: str
    kudos_id: str


# Student Gamification Schemas
# PRODUCT RULE 1: XP is awarded for effort, never marks.
# PRODUCT RULE 2: No leaderboards. Class Garden is cooperative.
# PRODUCT RULE 3: Students see growth only, never their support level.
class ProgressPoint(BaseModel):
    w: str
    v: int


class StudentMissionItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    minutes: int
    xp: int
    tier: str
    kind: str
    blurb: str
    is_done: bool = False
    badge_id: Optional[str] = None


class StudentKudosItem(BaseModel):
    id: str
    teacher_name: str
    message: str
    created_at: datetime


class ClassGardenInfo(BaseModel):
    total_drops: int
    target_drops: int = 48
    stage: str
    pct: float
    watered_today_count: int = 18
    total_classmates: int = 24


class StudentBadgeItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    name: str
    category: str
    how_to_earn: str
    icon: str
    earned: bool = False
    earned_at: Optional[datetime] = None


class StudentHomeResponse(BaseModel):
    xp_total: int
    level_name: str
    next_level: str
    to_next: int
    pct: float
    class_name: str
    student_name: str
    assigned_missions: List[StudentMissionItem]
    earned_badges: List[StudentBadgeItem]
    total_badges_count: int
    class_garden: ClassGardenInfo
    recent_kudos: List[StudentKudosItem]
    own_progress: List[ProgressPoint]


class MissionSubmitRequest(BaseModel):
    hints_used: int = 0
    tries: int = 1
    score: Optional[int] = 0


class MissionSubmitResponse(BaseModel):
    xp_awarded: int
    new_total_xp: int
    badge_unlocked: Optional[str] = None
    newly_unlocked_badges: List[StudentBadgeItem] = []
    garden_drops: int
    already_completed: bool = False
    message: str


class StudentDoubtCreate(BaseModel):
    text: str
    topic: Optional[str] = None


class StudentDoubtResponse(BaseModel):
    id: str
    class_name: str
    text: str
    topic: str
    message: Optional[str] = None
    created_at: datetime
    resolved: bool = False


# Teacher Mission Management Schemas
class TeacherMissionItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    minutes: int
    xp: int
    tier: str
    kind: str
    blurb: str
    is_assigned: bool = False


class TeacherMissionAssignRequest(BaseModel):
    mission_id: str
    assign: bool = True


class TeacherMissionTickRequest(BaseModel):
    student_id: str
    note: Optional[str] = "Paper mission completed"


class PrintCardItem(BaseModel):
    id: str
    title: str
    minutes: int
    xp: int
    tier: str
    blurb: str


# =========================================================================
# Parent Connect and Parent Portal Schemas
# =========================================================================

class ParentHomeChildSummary(BaseModel):
    id: str
    name: str
    class_name: str
    roll_no: str
    subject: str
    attendance_pct: int
    homework_pct: int
    current_xp: int
    growth_highlight: str


class ParentHomeNote(BaseModel):
    id: str
    body: str
    language: str
    channel: str
    created_at: datetime


class ParentBookingItem(BaseModel):
    id: str
    day: str
    date: str
    time: str
    method: str
    teacher_name: str
    reminders: List[str] = []
    status: str


class ParentPreferencesResponse(BaseModel):
    preferred_channel: str
    preferred_language: str
    no_smartphone: bool
    shift_worker: bool
    offer_voice_note: bool = False


class ParentPreferencesUpdate(BaseModel):
    channel: Optional[str] = None
    language: Optional[str] = None
    no_smartphone: Optional[bool] = None
    shift_worker: Optional[bool] = None


class ParentCheckinCreate(BaseModel):
    mood: str
    has_voice_note: bool = False
    voice_note_url: Optional[str] = None


class ParentHomeResponse(BaseModel):
    child: ParentHomeChildSummary
    latest_note: Optional[ParentHomeNote] = None
    next_booking: Optional[ParentBookingItem] = None
    recent_checkin: Optional[Dict[str, Any]] = None
    preferences: ParentPreferencesResponse


class WindowSlots(BaseModel):
    id: str
    label: str
    time: str
    extended: bool
    slots: List[str]


class ParentSlotsResponse(BaseModel):
    days: List[str]
    windows: List[WindowSlots]
    booked: Dict[str, str] = {}


class ParentBookingCreate(BaseModel):
    day: str
    date: Optional[str] = None
    window_id: Optional[str] = "am"
    time: str
    method: str = "call"
    reminders: List[str] = []


class InboundSMSRequest(BaseModel):
    from_phone: Optional[str] = ""
    body: str
    student_id: Optional[str] = None
    parent_user_id: Optional[str] = None


class VoiceSimulateRequest(BaseModel):
    keypad_input: str
    student_id: Optional[str] = None
    parent_user_id: Optional[str] = None


class TeacherConnectResponse(BaseModel):
    ladder: List[Dict[str, Any]]
    unreached: List[Dict[str, Any]]
    booked_count: int
    budget_calls: int = 8
    booked: Dict[str, str]


class TeacherCallbackReserveRequest(BaseModel):
    callback_id: str
    day: str = "Tue"
    date: Optional[str] = None
    time: str = "1:00 PM"
    method: str = "call"


# =========================================================================
# Admin Schemas
# =========================================================================

class EquityBand(BaseModel):
    band: str
    earned: int
    total_students: int
    earned_students: int


class ReachChannelStat(BaseModel):
    name: str
    value: int
    count: int


class AdminKPIs(BaseModel):
    support_plan_count: int
    families_reached_pct: int
    badge_earning_pct: int


class EquityAlert(BaseModel):
    flagged: bool
    gap: int
    message: str


class AdminOverviewResponse(BaseModel):
    kpis: AdminKPIs
    equity: List[EquityBand]
    equity_alert: EquityAlert
    reach: List[ReachChannelStat]
    heat_classes: List[str]
    heat: List[List[int]]


class GuardrailItem(BaseModel):
    key: str
    label: str
    value: Any
    locked: bool
    description: str


class AdminGuardrailsResponse(BaseModel):
    guardrails: List[GuardrailItem]
    feature_flags: Dict[str, Any]


class AdminSettingsUpdate(BaseModel):
    feature_flags: Dict[str, Any]


class AuditLogItem(BaseModel):
    id: str
    actor_id: str
    actor_role: str
    action: str
    entity: str
    entity_id: Optional[str] = None
    meta: Dict[str, Any] = {}
    created_at: datetime


class AuditLogsResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[AuditLogItem]





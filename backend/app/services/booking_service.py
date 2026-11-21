from typing import List, Dict, Any
from app.core.exceptions import InvalidCallWindowException

WINDOWS_CONFIG = [
    {
        "id": "am",
        "label": "Before school",
        "time": "7:30 to 8:15 AM",
        "slots": ["7:30", "7:35", "7:40", "7:45", "7:50", "7:55"],
        "extended": False,
    },
    {
        "id": "lunch",
        "label": "Lunch break",
        "time": "1:00 to 1:40 PM",
        "slots": ["1:00", "1:05", "1:10", "1:15", "1:20", "1:25"],
        "extended": False,
    },
    {
        "id": "pm",
        "label": "After school",
        "time": "4:15 to 5:00 PM",
        "slots": ["4:15", "4:20", "4:25", "4:30", "4:35", "4:40"],
        "extended": False,
    },
    {
        "id": "eve",
        "label": "Evening (Tue and Thu only)",
        "time": "6:30 to 7:30 PM",
        "slots": ["6:30", "6:35", "6:40", "6:45", "6:50", "6:55"],
        "extended": True,
    },
]


def validate_booking_window(day: str, window_id: str, slot_time: str) -> None:
    """
    PRODUCT RULE 5: Parent call windows stay inside school hours; evening slots only Tue and Thu.
    """
    window = next((w for w in WINDOWS_CONFIG if w["id"] == window_id), None)
    if not window:
        raise InvalidCallWindowException(f"Invalid call window: {window_id}")

    # Weekends (Sat, Sun) cannot be booked for normal calls
    if day in ("Sat", "Sun"):
        raise InvalidCallWindowException("Parent call windows are only available on weekdays (Mon-Fri).")

    # Evening slots are strictly limited to Tue and Thu
    if window["extended"] and day not in ("Tue", "Thu"):
        raise InvalidCallWindowException(
            f"Evening call slots are only offered on Tuesday and Thursday. Selected day: {day}"
        )

    # Slot must be valid for the window
    if slot_time not in window["slots"]:
        raise InvalidCallWindowException(
            f"Slot {slot_time} is not a valid 5-minute slot for window {window['label']}."
        )

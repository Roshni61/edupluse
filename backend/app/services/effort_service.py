from typing import List, Dict, Any, Tuple


def calculate_baseline(scores: List[int]) -> int:
    """Calculates student's own historical baseline from the first 4 recorded scores."""
    if not scores:
        return 70
    initial = scores[:4]
    return round(sum(initial) / len(initial))


def calculate_drop_from_self(scores: List[int], baseline: int) -> int:
    """Calculates how much the student has dropped from their own baseline, not class average."""
    if not scores:
        return 0
    latest = scores[-1]
    return max(0, baseline - latest)


def calculate_support_level(att: int, hw: int, drop: int) -> int:
    """
    ENGINEERING RULE: Server is the source of truth.
    Formula: (100 - att) * 0.5 + (100 - hw) * 0.3 + drop * 1.2
    Returns:
      3: 'Needs support now' (score >= 34)
      2: 'Needs support' (score >= 20)
      1: 'Keep an eye'
    """
    score = (100 - att) * 0.5 + (100 - hw) * 0.3 + drop * 1.2
    if score >= 34:
        return 3
    elif score >= 20:
        return 2
    return 1


def calculate_xp_award(mission_xp: int) -> int:
    """
    PRODUCT RULE 1: XP is awarded for effort, never for marks. Same effort = same XP for every student.
    Every completed mission yields its configured XP regardless of mistakes or accuracy.
    """
    return mission_xp


def level_from_xp(xp: int) -> Dict[str, Any]:
    tiers = [
        {"name": "Sprout", "min": 0},
        {"name": "Sapling", "min": 200},
        {"name": "Bloom", "min": 450},
        {"name": "Grove", "min": 800},
    ]
    cur_idx = 0
    for idx, tier in enumerate(tiers):
        if xp >= tier["min"]:
            cur_idx = idx

    cur = tiers[cur_idx]
    next_tier = tiers[cur_idx + 1] if cur_idx + 1 < len(tiers) else None

    if next_tier:
        pct = (xp - cur["min"]) / (next_tier["min"] - cur["min"])
        to_next = next_tier["min"] - xp
        next_name = next_tier["name"]
    else:
        pct = 1.0
        to_next = 0
        next_name = "Top"

    return {
        "name": cur["name"],
        "next": next_name,
        "pct": round(pct, 2),
        "to_next": to_next,
        "index": cur_idx,
    }

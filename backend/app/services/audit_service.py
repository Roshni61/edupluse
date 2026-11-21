import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.models import AuditLog

logger = logging.getLogger("audit")


def log_sensitive_access(
    db: Session,
    school_id: str,
    actor_id: str,
    actor_role: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """
    PRODUCT RULE 7: Every sensitive read/write by teacher/admin is written to an audit log.
    """
    meta = dict(details or {})
    meta["school_id"] = school_id
    meta["actor_role"] = actor_role

    audit_entry = AuditLog(
        actor_id=actor_id,
        action=action,
        entity=resource_type,
        entity_id=resource_id,
        meta=meta,
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(audit_entry)

    logger.info(
        f"[AUDIT] School: {school_id} | Actor: {actor_id} ({actor_role}) | Action: {action} "
        f"| Resource: {resource_type}:{resource_id}"
    )
    return audit_entry

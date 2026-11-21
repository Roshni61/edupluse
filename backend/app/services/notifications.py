import logging
import uuid
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.models import OutboxMessage

logger = logging.getLogger("notifications")


class NotificationProvider(ABC):
    """
    Abstract interface for dispatching parent and student communications.
    """

    @abstractmethod
    def send(
        self,
        db: Session,
        to_user_id: str,
        channel: str,
        template: str,
        payload: Dict[str, Any],
    ) -> OutboxMessage:
        """Dispatches or queues an outbound message and persists an OutboxMessage record."""
        pass


class ConsoleProvider(NotificationProvider):
    """
    Default provider for prototype and testing:
    Logs notification to console/logger and stores OutboxMessage with status='sent'.
    """

    def send(
        self,
        db: Session,
        to_user_id: str,
        channel: str,
        template: str,
        payload: Dict[str, Any],
    ) -> OutboxMessage:
        ref = f"console-{uuid.uuid4().hex[:8]}"
        logger.info(
            f"[NOTIFICATION - {channel.upper()}] To User: {to_user_id} | Template: {template} | Ref: {ref}\n"
            f"Payload: {payload}"
        )

        outbox = OutboxMessage(
            to_user_id=to_user_id,
            channel=channel.lower(),
            template=template,
            payload=payload,
            status="sent",
            provider_ref=ref,
        )
        db.add(outbox)
        db.commit()
        db.refresh(outbox)
        return outbox


class SMSProvider(NotificationProvider):
    """Stub for SMS gateway provider (e.g. Twilio / Gupshup / Fast2SMS)."""

    def send(
        self,
        db: Session,
        to_user_id: str,
        channel: str,
        template: str,
        payload: Dict[str, Any],
    ) -> OutboxMessage:
        ref = f"sms-stub-{uuid.uuid4().hex[:8]}"
        logger.info(f"[SMS STUB] Queueing SMS to {to_user_id}: {payload}")
        outbox = OutboxMessage(
            to_user_id=to_user_id,
            channel="sms",
            template=template,
            payload=payload,
            status="queued",
            provider_ref=ref,
        )
        db.add(outbox)
        db.commit()
        db.refresh(outbox)
        return outbox


class VoiceProvider(NotificationProvider):
    """Stub for automated voice telephony provider (e.g. Twilio / Exotel / Ozonetel)."""

    def send(
        self,
        db: Session,
        to_user_id: str,
        channel: str,
        template: str,
        payload: Dict[str, Any],
    ) -> OutboxMessage:
        ref = f"voice-stub-{uuid.uuid4().hex[:8]}"
        logger.info(f"[VOICE STUB] Triggering outbound call to {to_user_id}: {payload}")
        outbox = OutboxMessage(
            to_user_id=to_user_id,
            channel="voice",
            template=template,
            payload=payload,
            status="queued",
            provider_ref=ref,
        )
        db.add(outbox)
        db.commit()
        db.refresh(outbox)
        return outbox


class WhatsAppProvider(NotificationProvider):
    """Stub for WhatsApp Business API provider (e.g. Meta Cloud API / Karix)."""

    def send(
        self,
        db: Session,
        to_user_id: str,
        channel: str,
        template: str,
        payload: Dict[str, Any],
    ) -> OutboxMessage:
        ref = f"wa-stub-{uuid.uuid4().hex[:8]}"
        logger.info(f"[WHATSAPP STUB] Queueing WhatsApp message to {to_user_id}: {payload}")
        outbox = OutboxMessage(
            to_user_id=to_user_id,
            channel="whatsapp",
            template=template,
            payload=payload,
            status="queued",
            provider_ref=ref,
        )
        db.add(outbox)
        db.commit()
        db.refresh(outbox)
        return outbox


_default_notification_provider: NotificationProvider = ConsoleProvider()


def get_notification_provider() -> NotificationProvider:
    return _default_notification_provider

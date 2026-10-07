"""Shared contracts and enums for Oldy Buddy.

These enums are shared across modules (intelligence, voice agent, events engine, reminders).
"""

from enum import Enum


class Intent(str, Enum):
    """Classified conversational intent of the elderly user."""

    TALK = "talk"
    HELP = "help"
    REMINDER_DONE = "reminder_done"
    REMINDER_FORGOT = "reminder_forgot"
    FOOD = "food"
    SOS = "sos"
    UNKNOWN = "unknown"


class EventType(str, Enum):
    """System event types consumed by the decision engine and alert systems."""

    CHECKIN_OK = "checkin_ok"
    CHECKIN_CONCERN = "checkin_concern"
    CHECKIN_MISSED = "checkin_missed"
    REMINDER_DONE = "reminder_done"
    REMINDER_MISSED = "reminder_missed"
    HELP_REQUEST = "help_request"
    SOS = "sos"

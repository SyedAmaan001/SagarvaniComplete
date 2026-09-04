"""
Twilio Alert Service
Sends SMS and WhatsApp alerts to fishermen and coast guard.
Supports bulk alerts, templated messages, and delivery status tracking.
"""

import os
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from dotenv import load_dotenv

try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioRestException
    TWILIO_INSTALLED = True
except ImportError:
    Client = None
    TwilioRestException = Exception
    TWILIO_INSTALLED = False

load_dotenv()

# ─── Twilio Credentials ────────────────────────────────────────────────────────
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE = os.getenv("TWILIO_PHONE_NUMBER", "")
TARGET_PHONE = os.getenv("TWILIO_TARGET_PHONE", "")

# WhatsApp requires "whatsapp:+1..." format
TWILIO_WA_FROM = f"whatsapp:{TWILIO_PHONE}"


def _get_client() -> Client:
    """Initialize and return a Twilio client."""
    if not TWILIO_INSTALLED:
        raise EnvironmentError("Twilio package not installed. Run 'pip install twilio'")
    if not ACCOUNT_SID or not AUTH_TOKEN:
        raise EnvironmentError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set in .env")
    return Client(ACCOUNT_SID, AUTH_TOKEN)


def send_sms_alert(
    to_number: str,
    message: str,
    risk_level: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send an SMS alert via Twilio.

    Args:
        to_number: Recipient phone number (e.g., '+919035195941')
        message: Alert message text
        risk_level: Optional risk level tag (SAFE/CAUTION/WARNING/DANGER)

    Returns:
        Dict with SID, status, and timestamp
    """
    # Prepend ORCA header
    prefix = f"[ORCA ALERT]"
    if risk_level:
        emoji_map = {"SAFE": "🟢", "CAUTION": "🟡", "WARNING": "🟠", "DANGER": "🔴"}
        prefix = f"[ORCA {emoji_map.get(risk_level, '')} {risk_level}]"

    full_message = f"{prefix}\n{message}\n\n— ORCA Maritime Safety System"
    full_message = full_message[:1600]  # SMS character limit

    try:
        client = _get_client()
        msg = client.messages.create(
            body=full_message,
            from_=TWILIO_PHONE,
            to=to_number,
        )
        return {
            "success": True,
            "sid": msg.sid,
            "status": msg.status,
            "to": to_number,
            "type": "sms",
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "message_preview": full_message[:100] + "...",
        }
    except TwilioRestException as e:
        return {
            "success": False,
            "error": str(e),
            "to": to_number,
            "type": "sms",
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }
    except EnvironmentError as e:
        return {
            "success": False,
            "error": str(e),
            "to": to_number,
            "type": "sms",
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }


def send_whatsapp_alert(
    to_number: str,
    message: str,
    risk_level: Optional[str] = None,
    location: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Send a WhatsApp alert via Twilio.

    Args:
        to_number: Recipient phone number (e.g., '+919035195941')
        message: Alert message text
        risk_level: Optional risk level (SAFE/CAUTION/WARNING/DANGER)
        location: Optional {'lat': float, 'lon': float} for maps link

    Returns:
        Dict with SID, status, and timestamp
    """
    emoji_map = {"SAFE": "🟢", "CAUTION": "🟡", "WARNING": "🟠", "DANGER": "🔴"}
    emoji = emoji_map.get(risk_level, "🌊") if risk_level else "🌊"

    location_str = ""
    if location:
        lat, lon = location.get("lat"), location.get("lon")
        if lat and lon:
            location_str = f"\n📍 Location: https://maps.google.com/?q={lat},{lon}"

    full_message = (
        f"🌊 *ORCA MARITIME SAFETY ALERT*\n"
        f"{emoji} *{risk_level or 'INFO'}*\n\n"
        f"{message}"
        f"{location_str}\n\n"
        f"⏰ {datetime.now(timezone.utc).strftime('%d %b %Y, %H:%M UTC')}\n"
        f"_ORCA — SIH26176 Maritime Safety System_"
    )
    full_message = full_message[:1600]

    wa_to = f"whatsapp:{to_number}" if not to_number.startswith("whatsapp:") else to_number

    try:
        client = _get_client()
        msg = client.messages.create(
            body=full_message,
            from_=TWILIO_WA_FROM,
            to=wa_to,
        )
        return {
            "success": True,
            "sid": msg.sid,
            "status": msg.status,
            "to": to_number,
            "type": "whatsapp",
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "message_preview": full_message[:100] + "...",
        }
    except TwilioRestException as e:
        return {
            "success": False,
            "error": str(e),
            "to": to_number,
            "type": "whatsapp",
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }
    except EnvironmentError as e:
        return {
            "success": False,
            "error": str(e),
            "to": to_number,
            "type": "whatsapp",
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }


def send_bulk_alert(
    phone_numbers: List[str],
    message: str,
    risk_level: str,
    channel: str = "sms",
    location: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Send alerts to multiple recipients.

    Args:
        phone_numbers: List of phone numbers
        message: Alert message
        risk_level: Risk level string
        channel: 'sms' or 'whatsapp'
        location: Optional location dict

    Returns:
        Summary of all send attempts
    """
    results = []
    success_count = 0
    fail_count = 0

    for number in phone_numbers:
        if channel == "whatsapp":
            result = send_whatsapp_alert(number, message, risk_level, location)
        else:
            result = send_sms_alert(number, message, risk_level)

        results.append(result)
        if result.get("success"):
            success_count += 1
        else:
            fail_count += 1

    return {
        "total_sent": len(phone_numbers),
        "success_count": success_count,
        "fail_count": fail_count,
        "channel": channel,
        "results": results,
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }


def send_danger_alert(
    risk_score: float,
    risk_level_str: str,
    advisory_text: str,
    lat: float,
    lon: float,
    additional_numbers: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Auto-trigger danger alert when risk score > 75.
    Sends to the default target number and any additional numbers.
    """
    if risk_score <= 75:
        return {
            "triggered": False,
            "reason": f"Risk score {risk_score} <= 75, no auto-alert sent.",
        }

    all_numbers = [TARGET_PHONE] if TARGET_PHONE else []
    if additional_numbers:
        all_numbers.extend(additional_numbers)

    if not all_numbers:
        return {
            "triggered": False,
            "reason": "No target phone numbers configured in .env",
        }

    message = (
        f"DANGER ALERT — Risk Score: {risk_score}/100\n\n"
        f"{advisory_text[:400]}\n\n"
        f"Avoid going to sea. Contact coast guard: 1554"
    )

    location = {"lat": lat, "lon": lon}
    result = send_bulk_alert(
        all_numbers, message, risk_level_str, channel="whatsapp", location=location
    )
    result["triggered"] = True
    result["risk_score"] = risk_score
    return result


def get_message_status(message_sid: str) -> Dict[str, Any]:
    """Check the delivery status of a previously sent message."""
    try:
        client = _get_client()
        msg = client.messages(message_sid).fetch()
        return {
            "sid": msg.sid,
            "status": msg.status,
            "to": msg.to,
            "from_": msg.from_,
            "error_code": msg.error_code,
            "error_message": msg.error_message,
            "date_sent": str(msg.date_sent),
        }
    except Exception as e:
        return {"error": str(e), "sid": message_sid}

"""
Reusable notification message templates for Oldy Buddy Notifications.
"""

def get_notification_template(severity: str, elder_name: str, message: str) -> dict:
    sev = severity.upper()
    if sev in ["EMERGENCY", "HIGH"]:
        return {
            "title": f"🚨 EMERGENCY ALERT: {elder_name}",
            "body": f"Urgent: {message}. Immediate assistance required!",
            "sms": f"🚨 URGENT: Emergency alert for {elder_name}: {message}. Please check immediately!",
            "priority": "high",
        }
    elif sev in ["WARNING", "MEDIUM"]:
        return {
            "title": f"⚠️ Warning Alert: {elder_name}",
            "body": f"Attention needed: {message}",
            "sms": f"⚠️ OldyBuddy Warning for {elder_name}: {message}. Please check on them.",
            "priority": "normal",
        }
    else:  # INFO / LOW
        return {
            "title": f"ℹ️ Info: {elder_name}",
            "body": f"Update: {message}",
            "sms": f"OldyBuddy Info for {elder_name}: {message}",
            "priority": "normal",
        }

"""
notification_manager.py
NotificationManager: tracks status-change events for complaints.
Kept simple (in-memory + optional print) since a real SMS/email gateway
is outside hackathon scope - the class boundary is what matters for OOP.
"""

from datetime import datetime


class NotificationManager:
    def __init__(self):
        self._log = []

    def notify_new_complaint(self, complaint):
        self._log.append({
            "type": "NEW_COMPLAINT",
            "complaint_id": complaint.complaint_id,
            "message": f"New {complaint.priority} priority complaint filed in {complaint.category}.",
            "timestamp": datetime.utcnow().isoformat(),
        })

    def notify_status_change(self, complaint_id, new_status):
        self._log.append({
            "type": "STATUS_CHANGE",
            "complaint_id": complaint_id,
            "message": f"Complaint {complaint_id} status changed to {new_status}.",
            "timestamp": datetime.utcnow().isoformat(),
        })

    def recent(self, limit=10):
        return list(reversed(self._log[-limit:]))

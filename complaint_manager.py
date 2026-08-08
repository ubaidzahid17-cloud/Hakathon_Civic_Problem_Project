"""
complaint_manager.py
ComplaintManager: the orchestration class that ties together
Complaint (entity), AIAnalyzer (AI service), DatabaseManager (storage) and
NotificationManager (events). This is the core OOP workflow class -
nothing in the API layer talks to AI or the DB directly.
"""

from models import Complaint, DatabaseManager, VALID_STATUSES
from ai_service import AIAnalyzer
from notification_manager import NotificationManager


class ComplaintManager:
    def __init__(self, db: DatabaseManager = None, ai: AIAnalyzer = None,
                 notifier: NotificationManager = None):
        self.db = db or DatabaseManager()
        self.ai = ai or AIAnalyzer()
        self.notifier = notifier or NotificationManager()

    def submit_complaint(self, description, location, citizen_name="", citizen_phone="", image_flag=False):
        if not description or not description.strip():
            raise ValueError("Complaint description cannot be empty.")
        if not location or not location.strip():
            raise ValueError("Location cannot be empty.")
        if not citizen_name or not citizen_name.strip():
            raise ValueError("Name cannot be empty.")
        if not citizen_phone or not citizen_phone.strip():
            raise ValueError("Phone number cannot be empty.")

        complaint = Complaint(description=description, location=location,
                               citizen_name=citizen_name, citizen_phone=citizen_phone,
                               image_flag=image_flag)

        try:
            ai_result = self.ai.analyze(description)
        except Exception as e:
            # AI failure fallback: don't crash the whole submission
            ai_result = {
                "category": "Other", "priority": "Medium", "confidence": 0.0,
                "keywords": [], "summary": description[:100],
                "explanation": f"AI analysis failed ({e}); defaulted to Other/Medium.",
            }

        complaint.apply_ai_result(ai_result)
        self.db.save(complaint)
        self.notifier.notify_new_complaint(complaint)
        return complaint

    def list_complaints(self, **filters):
        return self.db.get_all(**filters)

    def get_complaint(self, complaint_id):
        return self.db.get_by_id(complaint_id)

    def update_status(self, complaint_id, status):
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Must be one of {VALID_STATUSES}")
        existing = self.db.get_by_id(complaint_id)
        if not existing:
            raise LookupError(f"Complaint {complaint_id} not found.")
        self.db.update_status(complaint_id, status)
        self.notifier.notify_status_change(complaint_id, status)
        return self.db.get_by_id(complaint_id)

    def reassign_department(self, complaint_id, department):
        existing = self.db.get_by_id(complaint_id)
        if not existing:
            raise LookupError(f"Complaint {complaint_id} not found.")
        self.db.update_department(complaint_id, department)
        return self.db.get_by_id(complaint_id)

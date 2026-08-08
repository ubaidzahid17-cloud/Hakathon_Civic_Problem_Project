"""
models.py
OOP data layer for AI Smart Civic Services.

Classes:
    Complaint        -> represents a single citizen complaint (entity)
    DatabaseManager   -> handles all SQLite persistence (data access layer)
"""

import sqlite3
import uuid
from datetime import datetime
from contextlib import contextmanager

DB_PATH = "data/civic_services.db"

VALID_STATUSES = ["Open", "Assigned", "In Progress", "Resolved"]
VALID_PRIORITIES = ["Low", "Medium", "High", "Critical"]
VALID_CATEGORIES = [
    "Road", "Water/Drainage", "Waste", "Electricity",
    "Safety", "Other"
]

DEPARTMENT_MAP = {
    "Road": "Roads & Infrastructure Dept.",
    "Water/Drainage": "Water & Sanitation Dept.",
    "Waste": "Solid Waste Management Dept.",
    "Electricity": "Electricity Board",
    "Safety": "Public Safety Dept.",
    "Other": "General Municipal Office",
}


class Complaint:
    """Represents a single civic complaint (entity / domain object)."""

    def __init__(self, description, location, citizen_name="", citizen_phone="",
                 image_flag=False, complaint_id=None, category=None, priority=None,
                 status="Open", assigned_department=None, ai_output=None,
                 date=None, resolved_date=None):
        self.complaint_id = complaint_id or f"CMP-{uuid.uuid4().hex[:8].upper()}"
        self.description = description.strip()
        self.location = location.strip()
        self.citizen_name = (citizen_name or "").strip()
        self.citizen_phone = (citizen_phone or "").strip()
        self.image_flag = image_flag
        self.category = category
        self.priority = priority
        self.status = status
        self.assigned_department = assigned_department
        self.ai_output = ai_output  # dict: {category, priority, summary, confidence, keywords}
        self.date = date or datetime.utcnow().isoformat()
        self.resolved_date = resolved_date

    def apply_ai_result(self, ai_result: dict):
        """Attach AIAnalyzer output to this complaint and derive fields from it."""
        self.ai_output = ai_result
        self.category = ai_result.get("category", "Other")
        self.priority = ai_result.get("priority", "Medium")
        self.assigned_department = DEPARTMENT_MAP.get(self.category, "General Municipal Office")

    def mark_resolved(self):
        self.status = "Resolved"
        self.resolved_date = datetime.utcnow().isoformat()

    def resolution_time_hours(self):
        """Returns resolution time in hours, or None if not yet resolved."""
        if not self.resolved_date:
            return None
        start = datetime.fromisoformat(self.date)
        end = datetime.fromisoformat(self.resolved_date)
        return round((end - start).total_seconds() / 3600, 2)

    def to_dict(self):
        return {
            "complaint_id": self.complaint_id,
            "description": self.description,
            "location": self.location,
            "citizen_name": self.citizen_name,
            "citizen_phone": self.citizen_phone,
            "category": self.category,
            "priority": self.priority,
            "status": self.status,
            "assigned_department": self.assigned_department,
            "ai_output": self.ai_output,
            "date": self.date,
            "resolved_date": self.resolved_date,
            "resolution_time_hours": self.resolution_time_hours(),
        }


class DatabaseManager:
    """Handles all persistence for complaints (single responsibility: storage)."""

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS complaints (
                    complaint_id TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    location TEXT,
                    citizen_name TEXT,
                    citizen_phone TEXT,
                    category TEXT,
                    priority TEXT,
                    status TEXT,
                    assigned_department TEXT,
                    ai_summary TEXT,
                    ai_confidence REAL,
                    ai_keywords TEXT,
                    date TEXT,
                    resolved_date TEXT
                )
            """)

    def save(self, complaint: Complaint):
        ai = complaint.ai_output or {}
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO complaints
                (complaint_id, description, location, citizen_name, citizen_phone,
                 category, priority, status, assigned_department, ai_summary,
                 ai_confidence, ai_keywords, date, resolved_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                complaint.complaint_id, complaint.description, complaint.location,
                complaint.citizen_name, complaint.citizen_phone,
                complaint.category, complaint.priority, complaint.status,
                complaint.assigned_department, ai.get("summary"), ai.get("confidence"),
                ",".join(ai.get("keywords", [])), complaint.date, complaint.resolved_date
            ))
        return complaint

    def update_status(self, complaint_id, status, resolved_date=None):
        with self._connect() as conn:
            if status == "Resolved" and resolved_date is None:
                resolved_date = datetime.utcnow().isoformat()
            if status == "Resolved":
                conn.execute(
                    "UPDATE complaints SET status=?, resolved_date=? WHERE complaint_id=?",
                    (status, resolved_date, complaint_id)
                )
            else:
                conn.execute(
                    "UPDATE complaints SET status=? WHERE complaint_id=?",
                    (status, complaint_id)
                )

    def update_dates(self, complaint_id, date=None, resolved_date=None):
        with self._connect() as conn:
            if date is not None:
                conn.execute("UPDATE complaints SET date=? WHERE complaint_id=?", (date, complaint_id))
            if resolved_date is not None:
                conn.execute("UPDATE complaints SET resolved_date=? WHERE complaint_id=?", (resolved_date, complaint_id))

    def update_department(self, complaint_id, department):
        with self._connect() as conn:
            conn.execute(
                "UPDATE complaints SET assigned_department=? WHERE complaint_id=?",
                (department, complaint_id)
            )

    def get_all(self, category=None, priority=None, status=None, location=None, search=None):
        query = "SELECT * FROM complaints WHERE 1=1"
        params = []
        if category:
            query += " AND category=?"
            params.append(category)
        if priority:
            query += " AND priority=?"
            params.append(priority)
        if status:
            query += " AND status=?"
            params.append(status)
        if location:
            query += " AND location LIKE ?"
            params.append(f"%{location}%")
        if search:
            query += " AND description LIKE ?"
            params.append(f"%{search}%")
        query += " ORDER BY date DESC"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._enrich(dict(r)) for r in rows]

    def get_by_id(self, complaint_id):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM complaints WHERE complaint_id=?", (complaint_id,)
            ).fetchone()
        return self._enrich(dict(row)) if row else None

    @staticmethod
    def _enrich(record):
        """Adds derived fields (resolution_time_hours, ai_output dict) to a raw DB row."""
        record["ai_output"] = {
            "summary": record.get("ai_summary"),
            "confidence": record.get("ai_confidence"),
            "keywords": (record.get("ai_keywords") or "").split(",") if record.get("ai_keywords") else [],
        }
        if record.get("date") and record.get("resolved_date"):
            start = datetime.fromisoformat(record["date"])
            end = datetime.fromisoformat(record["resolved_date"])
            record["resolution_time_hours"] = round((end - start).total_seconds() / 3600, 2)
        else:
            record["resolution_time_hours"] = None
        return record

    def count(self):
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]

"""
app.py
Flask API + view layer for AI Smart Civic Services.
Routes only orchestrate HTTP <-> ComplaintManager / StatisticsService.
No AI or DB logic lives here (see complaint_manager.py, ai_service.py, models.py).
"""

from flask import Flask, request, jsonify, render_template
from complaint_manager import ComplaintManager
from stats_service import StatisticsService
from models import VALID_STATUSES, VALID_CATEGORIES, VALID_PRIORITIES, DEPARTMENT_MAP

app = Flask(__name__)
manager = ComplaintManager()
stats_service = StatisticsService()


# ---------- Page routes ----------

@app.route("/")
def citizen_page():
    return render_template("index.html")


@app.route("/admin")
def admin_page():
    return render_template("admin.html")


# ---------- API: complaints ----------

@app.route("/api/complaints", methods=["POST"])
def create_complaint():
    data = request.get_json(silent=True) or {}
    description = data.get("description", "")
    location = data.get("location", "")
    citizen_name = data.get("citizen_name", "")
    citizen_phone = data.get("citizen_phone", "")
    image_flag = bool(data.get("image_flag", False))

    try:
        complaint = manager.submit_complaint(description, location, citizen_name, citizen_phone, image_flag)
        return jsonify({"success": True, "complaint": complaint.to_dict()}), 201
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Server error: {e}"}), 500


@app.route("/api/complaints", methods=["GET"])
def get_complaints():
    filters = {
        "category": request.args.get("category") or None,
        "priority": request.args.get("priority") or None,
        "status": request.args.get("status") or None,
        "location": request.args.get("location") or None,
        "search": request.args.get("search") or None,
    }
    filters = {k: v for k, v in filters.items() if v}
    try:
        complaints = manager.list_complaints(**filters)
        return jsonify({"success": True, "complaints": complaints, "count": len(complaints)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/complaints/<complaint_id>", methods=["GET"])
def get_complaint(complaint_id):
    complaint = manager.get_complaint(complaint_id)
    if not complaint:
        return jsonify({"success": False, "error": "Complaint not found"}), 404
    return jsonify({"success": True, "complaint": complaint})


@app.route("/api/complaints/<complaint_id>/status", methods=["PATCH"])
def update_status(complaint_id):
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    try:
        updated = manager.update_status(complaint_id, status)
        return jsonify({"success": True, "complaint": updated})
    except LookupError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/complaints/<complaint_id>/department", methods=["PATCH"])
def update_department(complaint_id):
    data = request.get_json(silent=True) or {}
    department = data.get("department")
    if not department:
        return jsonify({"success": False, "error": "department is required"}), 400
    try:
        updated = manager.reassign_department(complaint_id, department)
        return jsonify({"success": True, "complaint": updated})
    except LookupError as e:
        return jsonify({"success": False, "error": str(e)}), 404


# ---------- API: statistics / meta ----------

@app.route("/api/statistics", methods=["GET"])
def get_statistics():
    complaints = manager.list_complaints()
    return jsonify({"success": True, "report": stats_service.full_report(complaints)})


@app.route("/api/meta", methods=["GET"])
def get_meta():
    return jsonify({
        "statuses": VALID_STATUSES,
        "categories": VALID_CATEGORIES,
        "priorities": VALID_PRIORITIES,
        "departments": sorted(set(DEPARTMENT_MAP.values())),
    })


# ---------- Error handlers ----------

@app.errorhandler(404)
def not_found(e):
    return jsonify({"success": False, "error": "Resource not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"success": False, "error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

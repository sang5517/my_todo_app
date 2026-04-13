from flask import Blueprint, render_template,session
from models.report import Report
from utils.auth import login_required
from models.user import User
from extensions import db

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/reports")
@login_required
def reports():
    user = User.query.get(session['user_id'])

    if not user.is_admin:
        return "권한 없음", 403

    reports = Report.query.order_by(Report.created_at.desc()).all()

    return render_template("admin/reports.html", reports=reports)

@admin_bp.route("/report/resolve/<int:report_id>", methods=["POST"])
@login_required
def resolve_report(report_id):
    user = User.query.get(session['user_id'])

    if not user.is_admin:
        return {"success": False}, 403

    report = Report.query.get(report_id)
    report.status = "resolved"

    db.session.commit()

    return {"success": True}
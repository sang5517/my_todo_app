from flask import Blueprint, render_template,session,request,jsonify
from models.report import Report
from models.post import Post
from models.comment import Comment
from utils.auth import login_required
from models.user import User
from extensions import db
from sqlalchemy import func

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/reports")
@login_required
def reports():
    user = User.query.get(session['user_id'])

    if not user.is_admin:
        return "권한 없음", 403

    status = request.args.get("status") # 추가
    page = request.args.get("page", 1, type=int) #추가

    query = Report.query.order_by(Report.created_at.desc())

    # 🔥 기본은 pending만
    if status != "all":
        query = query.filter_by(status="pending")

    reports = query.paginate(page=page, per_page=10)

    # 추가 시작
    post_counts = db.session.query(
        Report.post_id,
        func.count(Report.id).label("count")

    ).filter(Report.post_id != None)\
     .group_by(Report.post_id).all()
    
    comment_counts = db.session.query(
        Report.comment_id,
        func.count(Report.id).label("count")
    ).filter(Report.comment_id != None)\
     .group_by(Report.comment_id).all()
    
    post_count_dict = {p.post_id: p.count for p in post_counts}
    comment_count_dict = {c.comment_id: c.count for c in comment_counts}
    # 🔥 추가 끝

    return render_template(
        "admin/reports.html",
        reports=reports,
        status=status,
        post_count_dict=post_count_dict,
        comment_count_dict=comment_count_dict
    )

@admin_bp.route("/report/action/<int:report_id>", methods=["POST"])
@login_required
def resolve_action(report_id):
    user = User.query.get(session['user_id'])

    if not user.is_admin:
        return {"success": False}, 403

    action = request.form.get("action")
    report = Report.query.get(report_id)

    if not report:
        return {"success": False, "message" : "신고 없음"}
    
    # 삭제 처리

    if action == "delete":
        if report.post_id:
            post = Post.query.get(report.post_id)
            if post:
                comment_ids = [c.id for c in post.comments]
                db.session.delete(post)

            # 같은 post 신고 전부 처리
            Report.query.filter_by(post_id=report.post_id).update({
                "status": "deleted"
            })

            # 🔥 댓글 신고도 전부 처리
            if comment_ids:
                Report.query.filter(Report.comment_id.in_(comment_ids)).update({
                    "status": "deleted"
                }, synchronize_session=False)


        elif report.comment_id:
            comment = Comment.query.get(report.comment_id)
            if comment:
                db.session.delete(comment)

            # 같은 comment 신고 전부 처리
            Report.query.filter_by(comment_id=report.comment_id).update({
                "status": "deleted"
            })

        report.status = "deleted"   # ✅ 추가
        
    elif action == "ignore":
        if report.post_id:
            Report.query.filter_by(post_id=report.post_id).update({
                "status": "ignored"
            })

        elif report.comment_id:
            Report.query.filter_by(comment_id=report.comment_id).update({
                "status": "ignored"
            })
    db.session.commit()

    return {"success": True}
            
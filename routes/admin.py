from flask import Blueprint, render_template,session,request,jsonify
from models.report import Report
from models.post import Post
from models.comment import Comment
from utils.auth import login_required
from datetime import datetime
from datetime import timedelta
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

@admin_bp.route("/users")
@login_required
def users():

    user = User.query.get(session['user_id'])

    if not user.is_admin:
        return "권한 없음",403
    
    page = request.args.get("page",1,type=int)

    users = User.query.order_by(User.id.desc())\
                      .paginate(page=page, per_page=10)
    
    return render_template(
        "admin/users.html",
        users = users
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

@admin_bp.route("/user/delete/<int:user_id>", methods=['POST'])
@login_required
def admin_delete_user(user_id):

    admin = User.query.get(session['user_id'])

    if not admin.is_admin:
        return jsonify({"success": False, "message": "권한 없음"})

    user = User.query.get(user_id)

    if not user:
        return jsonify({"success": False, "message": "유저 없음"})

    if user.is_deleted:
        return jsonify({"success": False, "message": "이미 탈퇴된 계정"})

    if user.id == admin.id:
        return jsonify({"success": False, "message": "본인은 삭제 불가"})
    # 🔥 데이터 삭제
    Post.query.filter_by(author_id=user.id).delete()
    Comment.query.filter_by(user_id=user.id).delete()

    user.is_deleted = True
    user.deleted_at = datetime.utcnow()

    db.session.commit()

    return jsonify({"success": True})

@admin_bp.route("/user/ban/<int:user_id>", methods=['POST'])
@login_required
def admin_ban_user(user_id):

    admin = User.query.get(session['user_id'])

    if not admin.is_admin:
        return jsonify({"success": False, "message": "권한 없음"})
    
    user = User.query.get(user_id)

    if not user:
        return jsonify({"success": False, "message": "유저 없음"})
    
    if user.id == admin.id:
        return jsonify({"success": False, "message": "본인은 정지 불가"})

    # ✅ JSON 받기
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "message": "데이터 없음"})

    reason = data.get("reason")
    days = data.get("days")

    if not reason:
        return jsonify({"success": False, "message": "정지 사유 필요"})

    try:
        days = int(days)
    except:
        return jsonify({"success": False, "message": "정지 기간 숫자 입력"})

    # ✅ 정지 처리
    user.is_banned = True
    user.banned_at = datetime.utcnow()
    user.ban_reason = reason

    if days == 0:
        user.ban_until = None  # 영구정지
    else:
        user.ban_until = datetime.utcnow() + timedelta(days=days)

    db.session.commit()

    return jsonify({"success": True})

@admin_bp.route("/user/unban/<int:user_id>", methods=['POST'])
@login_required
def admin_unban_user(user_id):

    admin = User.query.get(session['user_id'])

    if not admin.is_admin:
        return jsonify({"success": False, "message": "권한 없음"})

    user = User.query.get(user_id)

    if not user:
        return jsonify({"success": False, "message": "유저 없음"})

    user.is_banned = False
    user.banned_at = None
    user.ban_until = None
    user.ban_reason = None

    db.session.commit()

    return jsonify({"success": True})
from flask import Blueprint,request,session,jsonify
from extensions import db
from models.report import Report
from utils.auth import login_required


report_bp = Blueprint('report', __name__, url_prefix='/report')

@report_bp.route('/post/<int:post_id>', methods=['POST'])
@login_required
def report_post(post_id):
    reason = request.form.get('reason')

    # 중복 신고 체크
    existing = Report.query.filter_by(
        reporter_id=session['user_id'],
        post_id=post_id
    ).first()

    if existing:
        return jsonify({
            "success": False,
            "message": "이미 신고한 게시글입니다."
        })
    report = Report(
        reporter_id = session['user_id'],
        post_id=post_id,
        reason=reason
    )

    db.session.add(report)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "신고 완료"
    })

@report_bp.route('/comment/<int:comment_id>', methods=['POST'])
@login_required
def report_comment(comment_id):
    reason = request.form.get('reason')
    
    # 중복 신고 체크
    existing = Report.query.filter_by(
        reporter_id=session['user_id'],
        comment_id=comment_id
    ).first()

    if existing:
        return jsonify({
            "success": False,
            "message": "이미 신고한 댓글입니다."
        })
    
    report = Report(
        reporter_id=session['user_id'],
        comment_id=comment_id,
        reason=reason
    )

    db.session.add(report)
    db.session.commit()


    return jsonify({"success": True, "message": "신고 완료"})

from flask import Blueprint, request, redirect, session
from models.comment import Comment
from extensions import db
from utils.auth import login_required
from flask import jsonify
from utils.filter import contains_bad_word
from models.user import User

comment_bp = Blueprint('comment', __name__)

@comment_bp.route('/comment/write/<int:post_id>', methods=['POST'])
@login_required
def write_comment(post_id):
    content = request.form['content']


    # 1. 공백 체크
    if not content:
        return jsonify({"success": False, "message": "댓글을 입력하세요"})
    
    # 2. 최소 길이
    if len(content) > 300:
        return jsonify({"success":False, "message": "댓글은 300자 이하로 입력해주세요"})
    
    # 3.욕설필터

    # 4. 욕설 필터
    if contains_bad_word(content):
        return jsonify({"success": False, "message": "부적절한 단어가 포함되어 있습니다"})
    
    comment = Comment(
        content=content,
        user_id=session['user_id'],
        post_id=post_id
    )

    db.session.add(comment)
    db.session.commit()

    return jsonify({"success": True, "message" : "댓글 작성 완료 "})

@comment_bp.route('/comment/delete/<int:comment_id>')
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    user = User.query.get(session['user_id'])

    if comment.user_id != session['user_id'] and not user.is_admin:
        return "권환 없음"
    
    db.session.delete(comment)
    db.session.commit()

    return redirect(request.referrer)

@comment_bp.route('/comment/update/<int:comment_id>', methods=['POST'])
@login_required
def update_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    user = User.query.get(session['user_id'])

    if comment.user_id != session['user_id'] and not user.is_admin:
        return jsonify({"success": False, "messager": "권한 없음"})
    
    new_content = request.form.get('content')

    comment.content = new_content
    db.session.commit()

    return jsonify({
        "message" : "수정 완료",
        "success": True
    })

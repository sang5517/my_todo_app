from flask import Blueprint, request, redirect, session
from models.comment import Comment
from extensions import db
from models.file import File
from utils.auth import login_required
from flask import jsonify
from utils.filter import contains_bad_word
from models.user import User
from bs4 import BeautifulSoup
import uuid
import os
from werkzeug.utils import secure_filename

comment_bp = Blueprint('comment', __name__)

@comment_bp.route('/comment/write/<int:post_id>', methods=['POST'])
@login_required
def write_comment(post_id):

    data = request.get_json()

    content = data.get('content', '').strip()
    files = data.get('files', [])

    text_only = BeautifulSoup(content, "html.parser").get_text()

    # 🔥 검증
    if not content and not files:
        return jsonify({"success": False, "message": "댓글 또는 파일을 입력하세요"})

    if len(text_only) > 300:
        return jsonify({"success": False, "message": "댓글은 300자 이하"})

    if contains_bad_word(content):
        return jsonify({"success": False, "message": "부적절한 단어 포함"})

    # 🔥 댓글 저장
    comment = Comment(
        content=content,
        user_id=session['user_id'],
        post_id=post_id
    )

    db.session.add(comment)
    db.session.commit()

    # 🔥 파일 저장 (URL 기반)
    for url in files:

        filename = url.split("/")[-1]

        ext = filename.rsplit('.', 1)[-1].lower()

        if ext in ['jpg','jpeg','png','gif','webp']:
            file_type = 'image'
        elif ext in ['mp4','webm','ogg']:
            file_type = 'video'
        else:
            file_type = 'file'

        db.session.add(File(
            file_path=filename,
            file_type=file_type,
            original_filename=filename,
            comment_id=comment.id
        ))

    db.session.commit()

    return jsonify({"success": True, "message": "댓글 작성 완료"})

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

from flask import Blueprint, request, redirect, session
from models.comment import Comment
from extensions import db
from models.file import File
from utils.auth import login_required
from flask import jsonify
from utils.filter import contains_bad_word
from models.user import User
import uuid
import os
from werkzeug.utils import secure_filename

comment_bp = Blueprint('comment', __name__)

@comment_bp.route('/comment/write/<int:post_id>', methods=['POST'])
@login_required
def write_comment(post_id):

    content = request.form.get('content', '').strip()
    files = request.files.getlist('files')

    # 🔥 1. 검증
    if not content and not files:
        return jsonify({"success": False, "message": "댓글 또는 파일을 입력하세요"})

    if len(content) > 300:
        return jsonify({"success": False, "message": "댓글은 300자 이하"})

    if content and contains_bad_word(content):
        return jsonify({"success": False, "message": "부적절한 단어 포함"})

    # 🔥 2. 댓글 먼저 저장 (핵심)
    comment = Comment(
        content=content,
        user_id=session['user_id'],
        post_id=post_id
    )

    db.session.add(comment)
    db.session.commit()   # 👉 comment.id 생성됨

    # 🔥 3. 파일 처리
    for file in files:
        if file and file.filename != "":
            original_filename = file.filename
            safe_filename = secure_filename(file.filename)

            filename = str(uuid.uuid4()) + "_" + safe_filename

            upload_dir = os.path.join('static', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)

            upload_path = os.path.join(upload_dir, filename)
            file.save(upload_path)

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
                original_filename=original_filename,
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

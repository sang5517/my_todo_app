from flask import Blueprint, request, redirect, session
from models.comment import Comment
from extensions import db
from utils.auth import login_required

comment_bp = Blueprint('comment', __name__)

@comment_bp.route('/comment/write/<int:post_id>', methods=['POST'])
@login_required
def write_comment(post_id):
    content = request.form['content']

    comment = Comment(
        content=content,
        user_id=session['user_id'],
        post_id=post_id
    )

    db.session.add(comment)
    db.session.commit()

    return redirect(request.referrer)

@comment_bp.route('/comment/delete/<int:comment_id>')
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    if comment.user_id != session['user_id']:
        return "권환 없음"
    
    db.session.delete(comment)
    db.session.commit()

    return redirect(request.referrer)


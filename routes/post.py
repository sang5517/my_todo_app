from flask import Blueprint, render_template,request,redirect,session
from models.post import Post
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from models.user import User
from models.like import Like
from models.comment import Comment
from flask import jsonify
from utils.auth import login_required
from datetime import timedelta

post_bp = Blueprint('post', __name__)
like_bp = Blueprint('like', __name__)

@post_bp.route('/')
def index():
    posts = Post.query.filter_by(category='general').order_by(Post.created_at.desc()).all()
    return render_template(
        'index.html',
        posts=posts,
        title='최근 글',
        category='general'
    )

@post_bp.route('/write', methods=['GET', 'POST'])
@login_required
def write():
    # GET 요청 시 query parameter로 category 받기
    default_category = request.args.get('category', 'general')

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        # POST에서는 숨겨진 input이나 select에서 category 가져오기
        category = request.form.get('category', default_category)
        
        new_post = Post(
            title=title,
            content=content,
            author_id=session['user_id'],
            category=category, 
        )
        db.session.add(new_post)
        db.session.commit()

        # 작성 후 카테고리 페이지로 이동
        if category == 'qna':
            return redirect('/qna')
        elif category == 'faq':
            return redirect('/faq')
        elif category == 'tips':
            return redirect('/tips')
        else:
            return redirect('/')  # general

    return render_template('write.html', default_category=default_category)

@post_bp.route('/delete/<int:post_id>')
@login_required
def delete(post_id):
    post_to_delete = Post.query.get_or_404(post_id)
    if post_to_delete.author_id != session['user_id']:
        return "권한이 없습니다."

    category = post_to_delete.category  # 삭제 전 카테고리 저장
    db.session.delete(post_to_delete)
    db.session.commit()

    # 삭제 후 카테고리별 페이지로 리다이렉트
    if category == 'qna':
        return redirect('/qna')
    elif category == 'faq':
        return redirect('/faq')
    elif category == 'tips':
        return redirect('/tips')
    else:
        return redirect('/')

@post_bp.route('/update/<int:post_id>', methods=['GET', 'POST'])
@login_required
def update(post_id):
    post = Post.query.get_or_404(post_id)

    # 작성자 확인
    if post.author_id != session['user_id']:
        return "권한이 없습니다."

    if request.method == 'POST':
        # 폼에서 입력 받은 값으로 업데이트
        post.title = request.form['title']
        post.content = request.form['content']
        # post.category = request.form.get('category', post.category)  # 선택 없으면 기존 카테고리 유지

        db.session.commit()

        # 수정 후 카테고리별 페이지로 리다이렉트
        if post.category == 'qna':
            return redirect('/qna')
        elif post.category == 'faq':
            return redirect('/faq')
        elif post.category == 'tips':
            return redirect('/tips')
        else:
            return redirect('/')

    # GET 요청 시 기존 글 내용 폼에 전달
    return render_template('update.html', post=post)

@login_required
@like_bp.route('/like/<int:post_id>', methods=['POST'])
def like_post(post_id):
    post = Post.query.get_or_404(post_id)

    user_id = session['user_id']

    existing_like = Like.query.filter_by(user_id=user_id, post_id=post.id).first()

    if existing_like:
        db.session.delete(existing_like)
    else:
        new_like = Like(user_id=user_id, post_id=post.id)
        db.session.add(new_like)

    db.session.commit()

    # 🔥 핵심: JSON으로 응답
    like_count = Like.query.filter_by(post_id=post.id).count()

    return jsonify({
        "count": like_count
    })

@login_required
@like_bp.route('/comment_like/<int:comment_id>', methods=['POST'])
def like_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    user_id = session['user_id']

    existing_like = Like.query.filter_by(
        user_id=user_id,
        comment_id=comment.id
    ).first()

    if existing_like:
        db.session.delete(existing_like)
    else:
        new_like = Like(user_id=user_id, comment_id=comment.id)
        db.session.add(new_like)

    db.session.commit()

    like_count = Like.query.filter_by(comment_id=comment.id).count()

    return jsonify({
        "count": like_count
    })

@post_bp.route('/qna')
def qna():
    posts = Post.query.filter_by(category='qna').order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts, title='Q&A', category='qna')

@post_bp.route('/faq')
def faq():
    posts = Post.query.filter_by(category='faq').order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts, title='FAQ', category='faq')

@post_bp.route('/tips')
def tips():
    posts = Post.query.filter_by(category='tips').order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts, title='꿀팁', category='tips')

@post_bp.route('/post/<int:post_id>')
def detail(post_id):
    post = Post.query.get_or_404(post_id)
    if session.get('user_id'):
        post.views += 1 # 조회수 증가
        db.session.commit()
        
    return render_template('detail.html' , post=post)


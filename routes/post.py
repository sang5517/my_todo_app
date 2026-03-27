from flask import Blueprint, render_template,request,redirect,session
from models.post import Post
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from models.user import User
from utils.auth import login_required
post_bp = Blueprint('post', __name__)


@post_bp.route('/')
def index():
    # 메인 페이지에서는 'general' 카테고리 글만 보여주기 
    posts = Post.query.filter_by(category='general').order_by(Post.created_at.desc()).all() # DB에 저장된 모든 블로그 글을 최근 순으로 가져오서 posts 리스트에 담는 것 
    return render_template('index.html', posts=posts) # render_template() flask에서 html 파일을 렌더링 할때 쓰는 함수 

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
            category=category
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

@post_bp.route('/qna')
def qna():
    # Q&A 카테고리 글만 가져오기
    posts = Post.query.filter_by(category='qna').order_by(Post.created_at.desc()).all()
    return render_template('qna.html', posts=posts)

@post_bp.route('/faq')
def faq():
    # Q&A 카테고리 글만 가져오기
    posts = Post.query.filter_by(category='faq').order_by(Post.created_at.desc()).all()
    return render_template('faq.html', posts=posts)

@post_bp.route('/tips')
def tips():
    # Q&A 카테고리 글만 가져오기
    posts = Post.query.filter_by(category='tips').order_by(Post.created_at.desc()).all()
    return render_template('tips.html', posts=posts)

@post_bp.route('/post/<int:post_id>')
def detail(post_id):
    post = Post.query.get_or_404(post_id)

    post.views += 1 # 조회수 증가
    db.session.commit()

    return render_template('detail.html' , post=post)


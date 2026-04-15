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
import html
from utils.filter import contains_bad_word
from sqlalchemy import or_
from sqlalchemy import func
post_bp = Blueprint('post', __name__)
like_bp = Blueprint('like', __name__)

@post_bp.route('/')
def index():
    posts, keyword = list_posts('general')

    return render_template(
        'index.html',
        posts=posts,
        category='general',
        title='자유게시판',
        keyword=keyword
    )

@post_bp.route('/write', methods=['GET', 'POST'])
@login_required
def write():
    default_category = request.args.get('category', 'general')
    user = User.query.get(session['user_id'])

    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        category = request.form.get('category', default_category)
        
        # 관리자 제한 (여기위치가 핵심 )
        if category == 'notice' and not user.is_admin:
            return jsonify({
                "success": False,
                "message": "관리자만 작성 가능"
            })
        
        # 1. 빈값 체크
        if not title or not content:
            return jsonify({"success": False, "message": "제목과 내용을 입력해주세요"})
        
        # 2. 글자수 제한
        if len(title) > 100:
            return jsonify({"success": False, "message": "제목은 100자 이하로 입력해주세요"})
        
        if len(content) > 2000:
            return jsonify({"success": False, "message": "내용은 2000자 이하로 입력해주세요"})
        
        # 3. 욕설 필터
        if contains_bad_word(title) or contains_bad_word(content):
            return jsonify({"success": False, "message": "부적절한 단어가 포함되어 있습니다"})
        
        new_post = Post(
            title=title,
            content=content,
            author_id=session['user_id'],
            category=category, 
        )
        db.session.add(new_post)
        db.session.commit()

        # 🔥 redirect 대신 JSON
        if category == 'qna':
            redirect_url = '/qna'
        elif category == 'notice':
            redirect_url = '/notice'
        elif category == 'info':
            redirect_url = '/info'
        else:
            redirect_url = '/'

        return jsonify({
            "success": True,
            "redirect": redirect_url
        })

    return render_template('write.html', default_category=default_category)

@post_bp.route('/delete/<int:post_id>')
@login_required
def delete(post_id):
    post_to_delete = Post.query.get_or_404(post_id)
    user = User.query.get(session['user_id'])

    if post_to_delete.author_id != session['user_id'] and not user.is_admin:
        return "권한이 없습니다."

    category = post_to_delete.category  # 삭제 전 카테고리 저장
    db.session.delete(post_to_delete)
    db.session.commit()

    # 삭제 후 카테고리별 페이지로 리다이렉트
    if category == 'qna':
        return redirect('/qna')
    elif category == 'notice':
        return redirect('/notice')
    elif category == 'info':
        return redirect('/info')
    else:
        return redirect('/')

@post_bp.route('/update/<int:post_id>', methods=['GET', 'POST'])
@login_required
def update(post_id):
    post = Post.query.get_or_404(post_id)
    user = User.query.get(session['user_id'])

    # 작성자 확인
    if post.author_id != session['user_id'] and not user.is_admin:
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
        elif post.category == 'notice':
            return redirect('/notice')
        elif post.category == 'info':
            return redirect('/info')
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
    posts, keyword = list_posts('qna')

    return render_template(
        'index.html',
        posts=posts,
        category='qna',
        title='Q&A',
        keyword=keyword
    )

@post_bp.route('/notice')
def notice():
    posts, keyword = list_posts('notice')

    return render_template(
        'index.html',
        posts=posts,
        category='notice',
        title='Notice',
        keyword=keyword
    )

@post_bp.route('/info')
def info():
    posts, keyword = list_posts('info')

    return render_template(
        'index.html',
        posts=posts,
        category='info',
        title='정보공유',
        keyword=keyword
    )

@post_bp.route('/post/<int:post_id>')
def detail(post_id):
    post = Post.query.get_or_404(post_id)

    page = request.args.get('page', 1, type=int)
    
    comments = Comment.query.filter_by(post_id=post_id)\
                            .order_by(Comment.created_at.desc())\
                            .paginate(page=page, per_page=5, error_out=False)
    
    if session.get('user_id'):
        post.views += 1 # 조회수 증가
        db.session.commit()
        
    return render_template('detail.html' , post=post , comments=comments)


@post_bp.route('/mypage/delete/<int:post_id>', methods=['POST'])
@login_required
def mypage_delete(post_id):
    post = Post.query.get_or_404(post_id)

    if post.author_id != session['user_id']:
        return jsonify({"success": False, "message": "권한 없음"})
    
    db.session.delete(post)
    db.session.commit()

    return jsonify({"success": True, "message": "삭제 완료"})

@post_bp.route('/mypage/update/<int:post_id>', methods=['POST'])
@login_required
def mypage_update(post_id):
    post = Post.query.get_or_404(post_id)

    # 작성자 검증
    if post.author_id != session['user_id']:
        return jsonify({"success": False, "message": "권한 없음"})
    
    title = request.form.get('title')
    content = request.form.get('content')

    if not title or not content:
        return jsonify({"success": False, "message": "값 입력 필요"})
    
    post.title = title
    post.content = content

    db.session.commit()

    return jsonify({"success": True, "message": "수정 완료"})


@post_bp.route('/mypage/comment/update/<int:comment_id>', methods=['POST'])
@login_required
def mypage_update_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    if comment.user_id != session['user_id']:
        return jsonify({"success": False, "message": "권한 없음"})

    content = request.form.get('content')

    if not content:
        return jsonify({"success": False, "message": "내용 입력하세요"})
    
    comment.content = content
    db.session.commit()

    return jsonify({"success": True, "message": "댓글 수정 완료"})


@post_bp.route('/mypage/comment/delete/<int:comment_id>', methods=['POST'])
@login_required
def mypage_delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    if comment.user_id != session['user_id']:
        return jsonify({"success": False, "message": "권한 없음"})
    
    db.session.delete(comment)
    db.session.commit()

    return jsonify({"success": True, "message": "댓글 삭제 완료"})




def list_posts(category):
    page = request.args.get('page', 1, type=int)
    keyword = request.args.get('q', '').strip()
    sort = request.args.get('sort', 'latest') # 추가
    query = Post.query.filter_by(category=category)

    if keyword:
        query = query.filter(Post.title.contains(keyword))

    # 정렬 분기
    if sort == "views":
        query = query.order_by(Post.views.desc())
    elif sort == "popular":
        query = query.outerjoin(
            Like, (Post.id == Like.post_id) & (Like.comment_id == None)
        )\
        .group_by(Post.id)\
        .order_by(func.count(Like.id).desc())

    else: # Latest
        query = query.order_by(Post.created_at.desc())
    
    posts = query.order_by(Post.created_at.desc())\
                 .paginate(page=page, per_page=10, error_out=False)

    return posts, keyword
from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'dev-secret_key'

db = SQLAlchemy(app)

# =====================
# DB 모델 정의
# =====================
class User(db.Model): # 유저정보 저장 
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False) # 중복불가
    password = db.Column(db.String(200), nullable=False) # 
    posts = db.relationship('Post', backref='author', lazy=True) # User.posts로 한 유저가 쓴 글들을 바로 가져올수 있음

class Post(db.Model):# 글정보 저장 , 글작성자와 연결 
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow) # 글작성시간
    author_id = db.Column(db.Integer, db.ForeignKey('user.id')) # 작성자 id

# DB 테이블 생성
with app.app_context():
    db.create_all()

# =====================
# 헬퍼 함수
# =====================
def is_logged_in(): # 로그인 여부 체크 함수
    return 'user_id' in session

def current_user(): # 로그인 되어 있으면 현재 유저 정보 반환 
    if is_logged_in():
        return User.query.get(session['user_id'])
    return None

# =====================
# 라우트
# =====================
@app.route('/')
def index():
    posts = Post.query.order_by(Post.created_at.desc()).all()  # 최신글부터 표시
    return render_template('index.html', posts=posts, logged_in=is_logged_in(), user=current_user())

@app.route('/write', methods=['GET', 'POST'])
def write():
    """글 작성 페이지"""
    if not is_logged_in(): # 로그인 여부 체크
        return redirect('/login') # 로그인 안 되어 있으면 로그인 페이지로 이동 

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        new_post = Post(title=title, content=content, author_id=session['user_id'])
        db.session.add(new_post)
        db.session.commit()
        return redirect('/')
    return render_template('write.html')

@app.route('/delete/<int:post_id>')
def delete(post_id):
    """글 삭제"""
    if not is_logged_in(): # 로그인 여부 체크
        return redirect('/login') # 로그인 안 되어 있으면 로그인 페이지로 이동 

    post_to_delete = Post.query.get_or_404(post_id)
    if post_to_delete.author_id != session['user_id']:
        return "권한이 없습니다."  # 다른 사람 글 삭제 방지

    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect('/')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """회원가입"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_pw = generate_password_hash(password)
        user = User(username=username, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """로그인"""
    error = None # 에러 메시지를 담을 변수 
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if not user:
            error = "아이디가 존재하지 않습니다"
        elif not check_password_hash(user.password,password):
            error = "비밀번호가 틀렸습니다"
        else:
            session['user_id'] = user.id
            return redirect('/')
        
    return render_template('login.html',error=error)

@app.route('/logout')
def logout():
    """로그아웃"""
    session.pop('user_id', None)
    return redirect('/')

# =====================
# 앱 실행
# =====================
if __name__ == '__main__':
    app.run(debug=True)

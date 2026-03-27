from flask import Blueprint, render_template, request, redirect, session
from models.user import User
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from utils.email import send_email,generate_code
auth_bp = Blueprint('auth', __name__)



@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['email']
        password = request.form['password']
        if not session.get('verified') or session.get('email_for_verify') != username:
            return "이메일 인증 먼저 해주세요"
        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            if existing_user.provider != "local":
                return "이미 소셜 계정으로 가입된 이메일입니다. 소셜 로그인 이용해주세요"
            else:
                return "이미 가입된 아이디입니다"

        hashed_pw = generate_password_hash(password)
        user = User(username=username, password=hashed_pw, provider="local",is_verified=True)
        db.session.add(user)
        db.session.commit()
        return redirect('/login')

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if not user:
            error = "아이디가 존재하지 않습니다"
        elif user.provider != "local":
            error = "소셜 로그인 계정입니다. 소셜 로그인을 이용해주세요"
        elif not check_password_hash(user.password, password):
            error = "비밀번호가 틀렸습니다"
        else:
            session['user_id'] = user.id
            return redirect('/')

    return render_template('login.html', error=error)

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/')

@auth_bp.route('/send-code', methods=['POST'])
def send_code():
    email = request.form['email']

    code = generate_code()

    session['email_code'] = code
    session['email_for_verify'] = email

    send_email(email,code)

    return "인증코드 발송됨"


@auth_bp.route('/verify-code', methods=['POST'])
def verify_code():
    user_code = request.form['code']

    if user_code == session.get('email_code'):
        session['verified'] = True
        return "인증 성공"
    else:
        return "인증 실패"
    


from flask import Blueprint, render_template, request, redirect, session
from models.user import User
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from utils.email import send_email,generate_code
from flask import jsonify

auth_bp = Blueprint('auth', __name__)



from flask import jsonify

@auth_bp.route('/register', methods=['GET','POST'])
def register():

    if request.method == 'GET':
        return render_template('register.html')  # ✅ 이게 맞음
    
    username = request.form.get('email')
    password = request.form.get('password')

    if not session.get('verified') or session.get('email_for_verify') != username:
        return jsonify({"message": "이메일 인증 먼저 해주세요", "success": False})

    existing_user = User.query.filter_by(username=username).first()

    if existing_user:
        if existing_user.provider != "local":
            return jsonify({"message": "소셜 계정입니다", "success": False})
        else:
            return jsonify({"message": "이미 가입된 아이디", "success": False})

    hashed_pw = generate_password_hash(password)
    user = User(username=username, password=hashed_pw, provider="local", is_verified=True)

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "회원가입 성공", "success": True})

@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')  # ✅ 이게 맞음
    
    username = request.form.get('email')
    password = request.form.get('password')

    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({"message": "아이디 없음", "success": False})

    if user.provider != "local":
        return jsonify({"message": "소셜 로그인 계정입니다", "success": False})

    if not check_password_hash(user.password, password):
        return jsonify({"message": "비밀번호 틀림", "success": False})

    session['user_id'] = user.id
    return jsonify({"message": "로그인 성공", "success": True})

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

    send_email(email,code,"register")

    return "인증코드 발송됨"


@auth_bp.route('/reset-password/send-code', methods=['POST'])
def reset_send_code():
    email = request.form.get('email')

    user = User.query.filter_by(username=email).first()
    if not user:
        return jsonify({"message": "가입된 이메일 없음", "success": False})

    code = generate_code()

    session['reset_code'] = code
    session['reset_email'] = email

    send_email(email, code,"reset")

    return jsonify({"message": "인증코드 발송됨", "success": True})

@auth_bp.route('/verify-code', methods=['POST'])
def verify_code():
    user_code = request.form['code']

    if user_code == session.get('email_code'):
        session['verified'] = True
        return "인증 성공"
    else:
        return "인증 실패"
        
@auth_bp.route('/find-id', methods=['POST'])
def find_id():
    email = request.form.get('email')
    user = User.query.filter_by(username=email).first()

    if not user:
        return jsonify({"message": "가입된 이메일 없음", "success": False})
    
    return jsonify({"message": f"아이디: {user.username}", "success": True})



@auth_bp.route('/find-id', methods=['GET'])
def find_id_page():
    return render_template('find_id.html')


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'GET':
        return render_template('reset_password.html')

    # POST
    if not session.get('reset_verified'):
        return jsonify({"message": "인증 먼저 하세요", "success": False})

    new_password = request.form.get('password')
    email = session.get('reset_email')

    user = User.query.filter_by(username=email).first()

    user.password = generate_password_hash(new_password)
    db.session.commit()

    return jsonify({"message": "비밀번호 변경 완료", "success": True})

@auth_bp.route('/reset-password/verify',methods=['POST'])
def reset_verify():
    code = request.form.get('code')

    if code == session.get('reset_code'):
        session['reset_verified'] = True
        return jsonify({"message" : "인증 성공", "success": True})
    
    return jsonify({"message" : "코드 틀림", "success":False})


    
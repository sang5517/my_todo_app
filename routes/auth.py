from flask import Blueprint, render_template, request, redirect, session
from models.user import User
from models.comment import Comment
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from utils.email import send_email,generate_code
from flask import jsonify
from models.post import Post
import re
auth_bp = Blueprint('auth', __name__)



from flask import jsonify

def clean_nickname(nickname):
    if not nickname:
        return None
    
    nickname = nickname.strip()              # 앞뒤 공백 제거
    nickname = " ".join(nickname.split())    # 공백 여러개 → 1개
    
    return nickname


@auth_bp.route('/register', methods=['GET','POST'])
def register():

    if request.method == 'GET':
        return render_template('register.html')  # ✅ 이게 맞음
    
    username = request.form.get('username')
    nickname = clean_nickname(request.form.get('nickname')) 
    email = request.form.get('email')
    password = request.form.get('password')
    password_confirm = request.form.get('password_confirm')

    if password != password_confirm:
        return jsonify({"message": "비밀번호 불일치", "success": False})
    

    if not session.get('verified') or session.get('email_for_verify') != email:
        return jsonify({"message": "이메일 인증 먼저 해주세요", "success": False})

    existing_user = User.query.filter_by(username=username).first()

    if existing_user:
        if existing_user.provider != "local":
            return jsonify({"message": "소셜 계정입니다", "success": False})
        else:
            return jsonify({"message": "이미 가입된 아이디", "success": False})

    # 🔥 이메일 중복 체크 추가
    existing_email = User.query.filter_by(email=email).first()
    if existing_email:
        return jsonify({"message": "이미 가입된 이메일입니다", "success": False})
    
    hashed_pw = generate_password_hash(password)

    if not nickname or not re.match("^[a-zA-Z0-9가-힣 ]{2,15}$", nickname):
        return jsonify({"message": "닉네임은 2~15자, 한글/영문/숫자만 가능", "success": False})
    
    existing_nickname = User.query.filter_by(nickname=nickname).first()
    if existing_nickname:
        return jsonify({"message": "이미 사용중인 닉네임", "success": False})
    
    user = User(
        username=username,
        email=email, # 🔥 여기 추가
        password=hashed_pw,
        nickname=nickname,
        provider="local",
        is_verified=True
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "회원가입 성공", "success": True})

@auth_bp.route('/check-username',methods=['POST'])
def check_username():
    username = request.form.get('username')

    user = User.query.filter_by(username=username).first()

    if user:
        return jsonify({"message": "이미 사용중인 아이디", "available" : False})
    else:
        return jsonify({"message": "사용 가능한 아이디", "available": True})
    

@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')  # ✅ 이게 맞음
    
    username = request.form.get('username')
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

    return jsonify({
        "success": True,
        "message": "인증코드 발송됨"
    })


@auth_bp.route('/reset-password/send-code', methods=['POST'])
def reset_send_code():
    email = request.form.get('email')

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "가입된 이메일 없음", "success": False})

    code = generate_code()

    session['reset_code'] = code
    session['reset_email'] = email

    send_email(email, code,"reset")

    return jsonify({"message": "인증코드 발송됨", "success": True})

@auth_bp.route('/verify-code', methods=['POST'])
def verify_code():
    user_code = request.form.get('code')
    email = request.form.get('email')  # 🔥 여기 get 사용

    if not email:
        return jsonify({"success": False, "message": "이메일 누락"})

    if user_code == session.get('email_code') and email == session.get('email_for_verify'):
        session['verified'] = True
        session['verified_email'] = email
        return jsonify({"success": True, "message": "인증 성공"})
    else:
        return jsonify({"success": False, "message": "인증 실패"})
        

@auth_bp.route('/find-id', methods=['POST'])
def find_id():
    email = request.form.get('email')

    # 인증 체크 추가
    if not session.get('verified') or session.get('verified_email') != email:
        return jsonify({
            "message": "이메일 인증 먼저 해주세요",
            "success": False
        })
    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"message": "가입된 이메일 없음", "success": False})
    
    return jsonify({
    "success": True,
    "username": user.username
    })



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

    user = User.query.filter_by(email=email).first()

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


@auth_bp.route('/mypage')
def mypage():
    if 'user_id' not in session:
        return redirect('/login')
    
    user = User.query.get(session['user_id'])

    return render_template('mypage.html', user=user)

import re
from flask import jsonify, request, session
from models.user import User
from extensions import db

@auth_bp.route('/mypage/send-code', methods = ['POST'])
def mypage_send_code():
    if 'user_id' not in session:
        return jsonify({"success":False, "message":"로그인 필요"})
    
    user = User.query.get(session['user_id'])

    code = generate_code()

    session['mypage_code'] = code
    session['mypage_verified'] = False

    send_email(user.email, code, "reset")

    return jsonify({"success": True, "message":"인증코드 발송됨"})

@auth_bp.route("/mypage/verify", methods=['POST'])
def mypage_verify():
    code = request.form.get('code')

    if code == session.get('mypage_code'):
        session['mypage_verified'] = True
        return jsonify({"success": True, "message": "인증 성공"})
    
    return jsonify({"success": False, "message": "코드 틀림"})

@auth_bp.route('/myposts')
def my_posts():
    if 'user_id' not in session:
        return redirect('/login')
    page = request.args.get('page', 1, type=int)

    posts = Post.query.filter_by(author_id = session['user_id'])\
                      .order_by(Post.created_at.desc())\
                      .paginate(page=page, per_page=10, error_out=False)

    return render_template('myposts.html',posts=posts)


@auth_bp.route('/mycomments')
def my_comments():
    if 'user_id' not in session:
        return redirect('/login')
    
    page = request.args.get('page',1, type=int)

    comments = Comment.query.filter_by(user_id=session['user_id'])\
                           .order_by(Comment.created_at.desc())\
                           .paginate(page=page, per_page=10, error_out=False)
    

    
    return render_template('mycomments.html', comments=comments)

@auth_bp.route("/mypage/change-password", methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return jsonify({"success" : False, "message": "로그인 필요"})
       
    
    user = User.query.get(session['user_id'])
    
    if user.provider != 'local':
        return jsonify({
            "success": False,
            "message": "소셜 로그인 계정은 비밀번호 변경이 불가능합니다"
        })
    

    if not session.get("mypage_verified"):
        return jsonify({"success": False, "message": "이메일 인증 필요"})
    
    new_password = request.form.get('password')

    if not new_password:
        return jsonify({"success" : False, "message": "비밀번호 입력하세요"})
    
    user.password = generate_password_hash(new_password)

    db.session.commit()

    # 인증 초기화(중요)
    session.pop('mypage_verified', None)
    session.pop('mypage_code',None)

    return jsonify({"success": True, "message": "비밀번호 변경 완료"})




@auth_bp.route('/update-nickname', methods=['POST'])
def update_nickname():
    
    if 'user_id' not in session:
        return jsonify({"message": "로그인 필요", "success": False})

    user = User.query.get(session['user_id'])
    new_nickname = clean_nickname(request.form.get('nickname'))

    # 1. 형식 검사
    if not new_nickname or not re.match("^[a-zA-Z0-9가-힣 ]{2,15}$", new_nickname):
        return jsonify({"message": "닉네임은 2~15자, 한글/영문/숫자만 가능", "success": False})

    
    # 2. 중복 체크
    existing = User.query.filter_by(nickname=new_nickname).first()
    if existing and existing.id != user.id:
        return jsonify({"message": "이미 사용중인 닉네임", "success": False})

    if user.nickname == new_nickname:
        return jsonify({"message": "현재 닉네임과 같습니다", "success": False})
    
    # 3. 업데이트
    user.nickname = new_nickname
    db.session.commit()

    return jsonify({"message": "닉네임 변경 완료", "success": True})

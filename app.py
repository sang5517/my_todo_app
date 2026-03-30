from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_dance.contrib.google import make_google_blueprint, google
import requests
from dotenv import load_dotenv
import os
from functools import wraps
from extensions import db
from config import Config
from models.user import User
from models.post import Post
from routes.post import post_bp,like_bp
from utils.auth import is_logged_in
from routes.auth import auth_bp
from routes.comment import comment_bp

# =====================
# 환경 변수 & 앱 초기화
# =====================
load_dotenv()
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # 로컬 개발용 HTTP 허용

app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(post_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(comment_bp)
app.register_blueprint(like_bp)
db.init_app(app)


# =====================
# DB 모델 정의
# =====================
with app.app_context():
    db.create_all()

# =====================
# 헬퍼 함수
# =====================
def current_user():
    if is_logged_in():
        return User.query.get(session['user_id'])
    return None

# ✅ 모든 템플릿에서 로그인 상태와 사용자 정보 자동 전달
@app.context_processor
def inject_user():
    return dict(
        logged_in=is_logged_in(),
        user=current_user()
    )

# ✅ 로그인 필요시 redirect 처리 데코레이터
# =====================
# Google OAuth 설정
# =====================
google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ],
    redirect_to="google_login_process"
)
app.register_blueprint(google_bp, url_prefix="/login")

@app.route("/login/google/process")
def google_login_process():
    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        return redirect(url_for("login"))

    user_info = resp.json()
    email = user_info['email']
    user = User.query.filter_by(email=email).first()

    if user:
        if user.provider == "local":
            session['pending_link'] = email
            return redirect(url_for("social_link_confirm"))
        else:
            session['user_id'] = user.id
            return redirect("/")
    else:
        username = email.split("@")[0]

        user = User(
            username=username,
            email=email,
            password=None,
            provider="kakao",
            is_verified=True
        )

        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        return redirect("/")

# =====================
# Kakao OAuth 설정
# =====================
RREST_API_KEY = os.getenv("KAKAO_REST_API_KEY")
CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET")
redirect_uri = "http://127.0.0.1:5000/login/kakao/process"

@app.route("/login/kakao")
def kakao_login():
    kakao_auth_url = f"https://kauth.kakao.com/oauth/authorize?response_type=code&client_id={RREST_API_KEY}&redirect_uri={redirect_uri}"
    return redirect(kakao_auth_url)

@app.route("/login/kakao/process")
def kakao_login_process():
    code = request.args.get("code")
    if not code:
        return "로그인 실패: 코드가 없습니다."

    token_url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": RREST_API_KEY,
        "redirect_uri": redirect_uri,
        "code": code,
        "client_secret": CLIENT_SECRET
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    token_response = requests.post(token_url, data=data, headers=headers)
    if token_response.status_code != 200:
        return f"토큰 요청 실패: {token_response.text}"

    access_token = token_response.json().get("access_token")
    user_info_url = "https://kapi.kakao.com/v2/user/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    user_response = requests.get(user_info_url, headers=headers)
    if user_response.status_code != 200:
        return f"사용자 정보 요청 실패: {user_response.text}"

    user_info = user_response.json()
    kakao_account = user_info.get("kakao_account", {})
    email = kakao_account.get("email")
    if not email:
        return "카카오에서 이메일 정보를 가져올 수 없습니다. 이메일 동의를 확인하세요."
    user = User.query.filter_by(email=email).first()

    if user:
        if user.provider == "local":
            session['pending_link'] = email
            return redirect(url_for("social_link_confirm"))
        else:
            session['user_id'] = user.id
            return redirect("/")
    else:
        username = email.split("@")[0]

        user = User(
            username=username,
            email=email,
            password=None,
            provider="kakao",
            is_verified=True
        )

        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        return redirect("/")

# =====================
# 소셜 계정 연동
# =====================
@app.route("/social/link", methods=["GET", "POST"])
def social_link_confirm():
    email = session.get('pending_link')
    if not email:
        return redirect("/login")

    if request.method == "POST":
        provider = request.form.get("provider")
        user = User.query.filter_by(email=email).first()
        providers = set(user.provider.split(","))
        providers.add(provider)
        user.provider = ",".join(providers)
        db.session.commit()

        session.pop('pending_link')
        session['user_id'] = user.id
        return redirect("/")

    return render_template('login.html', pending_link=email)

# =====================
# 라우트
# =====================

# =====================
# 앱 실행
# =====================
if __name__ == '__main__':
    app.run(debug=True)
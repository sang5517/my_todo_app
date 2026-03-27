import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret_key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI", "sqlite:///blog.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")
    KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET")
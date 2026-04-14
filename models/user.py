from extensions import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False) # 아이디
    email = db.Column(db.String(100),unique=True, nullable=False) # 이메일 추가
    is_admin = db.Column(db.Boolean, default = False)
    is_active = db.Column(db.Boolean, default = True)

    password = db.Column(db.String(200), nullable=True)
    provider = db.Column(db.String(20), default="local")
    nickname = db.Column(db.String(50), unique=True ,nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='user', lazy=True)  # backref 여기만
    is_verified = db.Column(db.Boolean, default=False)
    

    likes = db.relationship(
    'Like',
    backref='user',
    lazy=True,
    cascade='all, delete-orphan'
    )

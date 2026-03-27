from extensions import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=True)
    provider = db.Column(db.String(20), default="local")
    posts = db.relationship('Post', backref='author', lazy=True)
    is_verified = db.Column(db.Boolean, default = False)
    
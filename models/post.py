from extensions import db
from datetime import datetime

class Post(db.Model):
    __table_args__ = {'sqlite_autoincrement': True}

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category = db.Column(db.String(50), default='general')
    views = db.Column(db.Integer, default=0)
    
    comments = db.relationship(
        'Comment',
        backref='post',
        lazy=True,
        cascade='all, delete-orphan'
    )
    likes = db.relationship(
    'Like',
    backref='post',
    lazy=True,
    cascade='all, delete-orphan'
    )
    
    reports = db.relationship(
    'Report',
    backref='post',
    cascade='all, delete-orphan'
    )
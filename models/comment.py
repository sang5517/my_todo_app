from extensions import db
from datetime import datetime


class Comment(db.Model):
    __table_args__ = {'sqlite_autoincrement': True}
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    likes = db.relationship(
    'Like',
    backref='comment',
    lazy=True,
    cascade='all, delete-orphan'
    )
    reports = db.relationship(
    'Report',
    backref='comment',
    cascade='all, delete-orphan'
    )
    files = db.relationship(
    'File',
    backref='comment',
    lazy=True,
    cascade='all, delete-orphan'
    )
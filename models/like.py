from extensions import db
from datetime import datetime

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)   # 🔥 바꿔
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)  # 🔥 Integer 추가
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
   

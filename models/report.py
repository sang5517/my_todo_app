from extensions import db
from datetime import datetime

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    reporter_id = db.Column(db.Integer) # 신고한 사람
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'),nullable = True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'),nullable = True)

    reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    status = db.Column(db.String(20), default="pending") # 처리 여부
    
    post = db.relationship("Post", foreign_keys=[post_id])
    comment = db.relationship("Comment", foreign_keys=[comment_id])




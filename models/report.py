from extensions import db
from datetime import datetime

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    reporter_id = db.Column(db.Integer) # 신고한 사람
    post_id = db.Column(db.Integer, nullable = True)
    comment_id = db.Column(db.Integer, nullable = True)

    reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    status = db.Column(db.String(20), default="pending") # 처리 여부


    
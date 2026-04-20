from extensions import db
from datetime import datetime
class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    file_path = db.Column(db.String(255))
    file_type = db.Column(db.String(20))
    original_filename = db.Column(db.String(255))

    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
from app.models import db
from datetime import datetime

class ChatHistory(db.Model):
    __tablename__ = 'chat_histories'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    chat_session_id = db.Column(db.Integer, db.ForeignKey('chat_sessions.id'), nullable=False)
    query = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    sources = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('chat_histories', lazy=True))
    chat_session = db.relationship('ChatSession', backref=db.backref('chat_histories', lazy=True))
    
    def to_dict(self, full=False):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'chat_session_id': self.chat_session_id,
            'query': self.query,
            'answer': self.answer,
            'sources': self.sources if full else {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_streaming': False,
        }

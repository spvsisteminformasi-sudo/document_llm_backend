from app.models import db
from datetime import datetime
import random

class Tag(db.Model):
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('tags.id'), nullable=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=True)
    page_number = db.Column(db.Integer, nullable=True)
    tag_type = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    parent = db.relationship('Tag', remote_side=[id], backref=db.backref('children', lazy='dynamic'))
    documents = db.relationship('Document', backref=db.backref('documents', lazy=True))

    def __repr__(self):
        return f'<Tag {self.name}>'

    def to_dict(self, full=False):
        return {
            'id': self.id if full else str(self.id),
            'item_id': str(self.id) + '-' + str(random.randint(1, 1000000)),
            'name': self.name,
            'parent_id': self.parent_id,
            'document_id': self.document_id,
            'page_number': self.page_number,
            'tag_type': self.tag_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'document': self.documents.to_dict() if self.document_id else False,
            'parent': self.parent.to_dict() if self.parent_id and full else False,
            'children': [child.to_dict() for child in self.children] if self.children and not full else [],
        }

from app.models import db
from datetime import datetime
import os
from app.utils.pdf_extractor import PDFExtractor

# Configure upload path
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads')

class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.Text, nullable=False)
    original_filename = db.Column(db.Text, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    file_size = db.Column(db.Integer)
    document_type = db.Column(db.String(50), nullable=True)
    initiator = db.Column(db.String(255), nullable=True)
    number = db.Column(db.String(50), nullable=True)
    year = db.Column(db.String(50), nullable=True)
    about = db.Column(db.Text, nullable=True)
    place_of_determination = db.Column(db.String(255), nullable=True)
    date_of_determination = db.Column(db.DateTime, nullable=True)
    official = db.Column(db.String(255), nullable=True)
    view_count = db.Column(db.Integer, default=0)
    download_count = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(50), default='queue')
    category_document = db.Column(db.String(50), default='national')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('documents', lazy=True))
    
    def __repr__(self):
        return f'<Document {self.title}>'

    @property
    def full_path(self):
        return os.path.join(UPLOAD_FOLDER, self.file_path)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'original_filename': self.original_filename,
            'mime_type': self.mime_type,
            'file_size': self.file_size,
            'document_type': self.document_type,
            'initiator': self.initiator,
            'number': self.number,
            'year': self.year,
            'about': self.about,
            'place_of_determination': self.place_of_determination,
            'date_of_determination': self.date_of_determination.isoformat() if self.date_of_determination else None,
            'official': self.official,
            'view_count': self.view_count,
            'download_count': self.download_count,
            'status': self.status,
            'category_document': self.category_document,
            'url': f'/uploads/{self.original_filename}',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
   

    def process_pdf_content(self):
        if self.mime_type == 'application/pdf':
            return PDFExtractor.extract_and_save(self)
        return False



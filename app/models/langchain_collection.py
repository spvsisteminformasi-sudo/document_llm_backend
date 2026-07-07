from app.models import db
from sqlalchemy.dialects.postgresql import UUID, JSON
import uuid

class LangchainCollection(db.Model):
    __tablename__ = 'langchain_pg_collection'
    
    uuid = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String, nullable=False, unique=True)
    cmetadata = db.Column(JSON)

    def __repr__(self):
        return f'<LangchainCollection {self.name}>'

    def to_dict(self):
        return {
            'uuid': str(self.uuid),
            'name': self.name,
            'cmetadata': self.cmetadata
        }

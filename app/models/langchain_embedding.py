from app.models import db
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import Index, text
from pgvector.sqlalchemy import Vector

class LangchainEmbedding(db.Model):
    __tablename__ = 'langchain_pg_embedding'

    id = db.Column(db.String, primary_key=True)
    collection_id = db.Column(UUID(as_uuid=True), 
                            db.ForeignKey('langchain_pg_collection.uuid', ondelete='CASCADE'),
                            nullable=True)
    embedding = db.mapped_column(Vector())
    document = db.Column(db.String, nullable=True)
    cmetadata = db.Column(JSONB, nullable=True)

    # Add GIN index on cmetadata
    __table_args__ = (
        Index('ix_cmetadata_gin', 'cmetadata', postgresql_using='gin'),
    )

    def __repr__(self):
        return f'<LangchainEmbedding {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'collection_id': str(self.collection_id) if self.collection_id else None,
            'document': self.document,
            'cmetadata': self.cmetadata
        }

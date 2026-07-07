from celery import shared_task
from app.utils.pdf_extractor import PDFExtractor
from app.models import db
from app.models.document import Document
from datetime import datetime
    
@shared_task
def process_pdf_content_task(document_id):
    try:
        document = Document.query.get(document_id)
        if document and document.mime_type == 'application/pdf':
            document.status = 'processing'
            db.session.commit()
            PDFExtractor.extract_and_save(document)
            document.status = 'completed'
            document.updated_at = datetime.now()
            db.session.commit()
            return True
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
    return False

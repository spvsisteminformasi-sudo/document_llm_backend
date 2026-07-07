from flask import app, make_response, jsonify, request, send_from_directory
from flask_restful import Resource
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename
from app.models.document import Document, UPLOAD_FOLDER
from app.models import db
import os
from app.tasks.pdf_tasks import process_pdf_content_task
from app.utils.pdf_extractor import OpenAIConfig
from app.schemas.document import DocumentSchema
from pydantic import ValidationError

class DocumentResource(Resource):
    
    @jwt_required()
    def get(self, id=None):
        if id:
            args = request.args
            document = Document.query.get(id)
            if not document:
                return make_response(jsonify({'success': False, 'message': 'Document not found'}), 404)
                
            if args.get('download') == 'true':
                return send_from_directory(
                    UPLOAD_FOLDER,
                    document.original_filename,
                    as_attachment=True,
                )

            return make_response(jsonify({'data': document.to_dict()}), 200)
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 25, type=int)
        query = request.args.get('q', type=str)
        category_document = request.args.get('category_document', type=str)

        pagination = Document.query

        if query:
            pagination = pagination.filter(Document.title.ilike(f'%{query}%'))
            
        if category_document:
            pagination = pagination.filter(Document.category_document == category_document)
        
        pagination = pagination.paginate(page=page, per_page=per_page, error_out=False)

        return make_response(jsonify({
            'data': [document.to_dict() for document in pagination.items],
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'total_pages': pagination.pages
        }), 200)

    @jwt_required()
    def post(self):
        try:
            if request.args.get('refresh'):
                ids = request.json.get('ids')
                for id in ids:
                    document = Document.query.get(id)
                    if document:
                        OpenAIConfig.delete_vectors_by_document_id(document_id=document.id)
                        process_pdf_content_task.delay(id)
                        
                return make_response(jsonify({'success': True, 'message': 'Document refreshed successfully'}), 200)
            

            if 'file' not in request.files:
                return make_response(jsonify({'success': False, 'message': 'No file uploaded'}), 400)
            
            file = request.files['file']
            if file.filename == '':
                return make_response(jsonify({'success': False, 'message': 'No file selected'}), 400)

            filename = secure_filename(file.filename)
            
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
                
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            
            current_user = get_jwt_identity()
            
            # Validate document data
            doc_data = DocumentSchema(**request.form)
            
            document = Document(
                user_id=int(current_user),
                mime_type=file.content_type,
                original_filename=filename,
                file_size=os.path.getsize(file_path),
                file_path=file_path,
                **doc_data.model_dump()
            )
            
            db.session.add(document)
            db.session.commit()
            
            process_pdf_content_task.delay(document.id)
            
            return make_response(jsonify({
                'success': True,
                'message': 'Document uploaded successfully',
                'data': document.to_dict()
            }), 201)
        except ValidationError as e:
            return make_response(jsonify({
                'success': False,
                'message': 'Validation error',
                'errors': e.errors()
            }), 400)

    @jwt_required()
    def put(self, id):
        try:
            document = Document.query.get(id)
            if not document:
                return make_response(jsonify({'success': False, 'message': 'Document not found'}), 404)

            # Validate document data
            doc_data = DocumentSchema(**request.form)
            
            # Update document fields
            for key, value in doc_data.model_dump().items():
                setattr(document, key, value)
            
            db.session.commit()

            return make_response(jsonify({
                'success': True,
                'message': 'Document updated successfully',
                'data': document.to_dict()
            }), 200)
        except ValidationError as e:
            return make_response(jsonify({
                'success': False,
                'message': 'Validation error',
                'errors': e.errors()
            }), 400)

    @jwt_required()
    def delete(self, id):
        try:
            document = Document.query.get(id)
            if not document:
                return make_response(jsonify({'success': False, 'message': 'Document not found'}), 404)

            # Delete physical file
            if document.file_path and os.path.exists(document.file_path):
                try:
                    os.remove(document.file_path)
                except OSError as e:
                    return make_response(jsonify({'success': False, 'message': f'Error deleting file: {str(e)}'}), 500)

            
            OpenAIConfig.delete_vectors_by_document_id(document_id=document.id)
            # Delete document record
            db.session.delete(document)
            db.session.commit()
            
            return make_response(jsonify({'success': True, 'message': 'Document and content deleted successfully'}), 200)
            
        except Exception as e:
            db.session.rollback()
            return make_response(jsonify({'success': False, 'message': f'Error deleting document: {str(e)}'}), 500)

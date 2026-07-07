import time
from flask import app, make_response, jsonify, request, send_from_directory, Response, stream_with_context
from flask_restful import Resource
from app.models.document import Document, UPLOAD_FOLDER
from app.models import db
from app.models.tag import Tag
from app.utils.pdf_extractor import PDFExtractor

class PortalResource(Resource):
    
    @staticmethod
    def qa():
        # Get pagination parameters
        qa = request.args.get('qa', type=str)
        limit = request.args.get('limit', 5, type=int)

        if qa:
            search_results = PDFExtractor.qa_documents(qa, limit=limit)

            return make_response(jsonify({
                'success': True,
                'data': search_results,
            }), 200)
        if not qa:
            return Response(
                'data: {"success": false, "message": "No question provided"}\n\n',
                content_type='text/event-stream'
            )

        @stream_with_context
        def generate():
            yield 'data: {"success": true, "data": {"answer": "'
            # for word in PDFExtractor.qa_documents(qa, stream=True):
            for word in ["Sedang", "memproses", "pertanyaan", qa]:
                time.sleep(0.2)
                yield word + " "
            yield '", "sources": []}}\n\n'

        return Response(generate(), content_type='text/event-stream')

    @staticmethod
    def qa2():
        # Get pagination parameters
        qa = request.args.get('qa', type=str)
        limit = request.args.get('limit', 5, type=int)

        if not qa:
            return Response(
                'data: {"success": false, "message": "No question provided"}\n\n',
                content_type='text/event-stream'
            )

        @stream_with_context
        def generate():
            try:
                # Dapatkan hasil QA dari PDFExtractor
                qa_result = PDFExtractor.qa_documents(qa, limit=limit)
                
                # Stream jawaban per kata
                answer = qa_result.get('answer', '')
                sources = qa_result.get('sources', [])
                
                # Kirim data awal
                yield f'data: {{"success": true, "data": {{"answer": "'
                
                # Stream jawaban per kata
                words = answer.split()
                for i, word in enumerate(words):
                    time.sleep(0.1)  # Delay untuk efek streaming
                    if i == len(words) - 1:
                        yield word
                    else:
                        yield word + " "
                
                # Tutup dengan sources
                yield f'", "sources": {sources}}}}}\n\n'
                
            except Exception as e:
                error_msg = f'Error processing question: {str(e)}'
                yield f'data: {{"success": false, "message": "{error_msg}"}}\n\n'

        return Response(
            generate(), 
            content_type='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*'
            }
        )

    @staticmethod
    def document_search():
        query = request.args.get('q', type=str)
        data = PDFExtractor.search_documents(query)
        return make_response(jsonify({'success': True, 'data': data}), 200)
        
            
    @staticmethod
    def documents(id=None):
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
        else:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 25, type=int)
            query = request.args.get('q', type=str)
            if query:
                pagination = Document.query.filter(Document.title.ilike(f'%{query}%')).paginate(page=page, per_page=per_page, error_out=False)
            else:
                pagination = Document.query.paginate(page=page, per_page=per_page, error_out=False)
            
            return make_response(jsonify({
                'data': [document.to_dict() for document in pagination.items],
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'total_pages': pagination.pages
            }), 200)
        
    @staticmethod
    def tags(id=None):
        if id:
            tag = Tag.query.get(id)
            if not tag:
                return make_response(jsonify({'success': False, 'message': 'Tag not found'}), 404)
            return make_response(jsonify({'success': True, 'data': tag.to_dict()}), 200)
        
        # Get pagination parameters
        full = request.args.get('full')
        search = request.args.get('query', type=str)
        
        if not full:
            # Get paginated results
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 25, type=int)
            
            query = Tag.query
            if search:
                search = f"%{search}%"
                query = query.filter(Tag.name.ilike(search))
                
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            return make_response(jsonify({
                'success': True,
                'data': [tag.to_dict(True) for tag in pagination.items],
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'total_pages': pagination.pages
            }), 200)
        else:
            query = Tag.query
            if search:
                search = f"%{search}%"
                query = query.filter(Tag.name.ilike(search))
            else:
                query = query.filter_by(parent_id=None)
                
            tags = query.all()
            return make_response(jsonify({'success': True, 'data': [tag.to_dict() for tag in tags]}), 200)

    @staticmethod
    def uploaded_file(filename):
        try:
            return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=False)
        except FileNotFoundError:
            return make_response(jsonify({'success': False, 'message': 'File not found'}), 404)
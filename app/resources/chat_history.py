from flask import make_response, jsonify, request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.chat_history import ChatHistory
from app.schemas.chat_history import ChatHistorySchema
from app.models import db
from pydantic import ValidationError

from app.utils.pdf_extractor import PDFExtractor

class ChatHistoryResource(Resource):
    @jwt_required()
    def get(self, id=None):
        if id:
            chatHistory = db.session.query(ChatHistory).get(id)
            if not chatHistory:
                return make_response(jsonify({'message': 'Chat History not found'}), 404)
            return make_response(jsonify({'data': chatHistory.to_dict(True)}), 200)
        
        user_id = get_jwt_identity()
        
        chat_session_id = request.args.get('chat_session_id', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 25, type=int)
        
        pagination = db.session.query(ChatHistory).filter_by(
            chat_session_id=chat_session_id,
            user_id=user_id
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return make_response(jsonify({
            'data': [row.to_dict() for row in pagination.items],
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'total_pages': pagination.pages
        }), 200)

    @jwt_required()
    def post(self):
        try:
            user_id = get_jwt_identity()
            data = ChatHistorySchema(**request.get_json())
            
            histories = db.session.query(ChatHistory).filter_by(
                chat_session_id=data.chat_session_id,
                user_id=user_id
            ).paginate(page=1, per_page=3, error_out=False)
            
            chat = PDFExtractor.qa_documents(data.query, histories)
            
            chat_history = ChatHistory(
                chat_session_id=data.chat_session_id,
                user_id=user_id,
                query=data.query,
                answer=chat.get('answer'),
                sources=chat.get('sources'),
            )
            
            db.session.add(chat_history)
            db.session.commit()
            
            return make_response(jsonify({
                'success': True,
                'message': 'Chat history created successfully',
                'data': chat_history.to_dict()
            }), 201)
        except ValidationError as e:
            return make_response(jsonify({
                'success': False,
                'message': 'Validation error',
                'errors': e.errors()
            }), 400)

    @jwt_required()
    def delete(self, id):
        chat_history = ChatHistory.query.get(id)
        if not chat_history:
            return make_response(jsonify({'message': 'Chat history not found'}), 404)

        db.session.delete(chat_history)
        db.session.commit()
        return make_response(jsonify({
            'success': True,
            'message': 'Chat history deleted successfully'
        }), 200)

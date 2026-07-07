from flask import make_response, jsonify, request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.chat_session import ChatSession
from app.models.chat_history import ChatHistory
from app.schemas.chat_session import ChatSessionSchema
from app.models import db
from pydantic import ValidationError
from datetime import datetime

class ChatSessionResource(Resource):
    @jwt_required()
    def get(self, id=None):
        if id:
            chat_session = ChatSession.query.get(id)
            if not chat_session:
                return make_response(jsonify({'message': 'Chat session not found'}), 404)
            return make_response(jsonify({'data': chat_session.to_dict()}), 200)
        
        user_id = get_jwt_identity()
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 25, type=int)
        query = request.args.get('q', type=str)
        if query:
            pagination = ChatSession.query.filter(ChatSession.name.ilike(f'%{query}%')).filter_by(user_id=user_id).paginate(page=page, per_page=per_page, error_out=False)
        else:
            pagination = ChatSession.query.filter_by(user_id=user_id).paginate(page=page, per_page=per_page, error_out=False)
        
        return make_response(jsonify({
            'data': [row.to_dict() for row in pagination],
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'total_pages': pagination.pages
        }), 200)

    @jwt_required()
    def post(self):
        try:
            user_id = get_jwt_identity()
            data = ChatSessionSchema(**request.get_json())
            
            chat_session = ChatSession(
                name=data.name,
                user_id=user_id,
                created_at=datetime.utcnow()
            )
            db.session.add(chat_session)
            db.session.commit()
            
            return make_response(jsonify({
                'success': True,
                'message': 'Chat session created successfully',
                'data': chat_session.to_dict()
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
            chat_session = ChatSession.query.get(id)
            if not chat_session:
                return make_response(jsonify({'message': 'Chat session not found'}), 404)

            data = ChatSessionSchema(**request.get_json())
            chat_session.name = data.name
            db.session.commit()

            return make_response(jsonify({
                'success': True,
                'message': 'Chat session updated successfully',
                'data': chat_session.to_dict()
            }), 200)
        except ValidationError as e:
            return make_response(jsonify({
                'success': False,
                'message': 'Validation error',
                'errors': e.errors()
            }), 400)

    @jwt_required()
    def delete(self, id):
        chat_session = ChatSession.query.get(id)
        if not chat_session:
            return make_response(jsonify({'message': 'Chat session not found'}), 404)

        # Delete associated chat histories first
        db.session.query(ChatHistory).filter_by(chat_session_id=id).delete()
        
        # Then delete the chat session
        db.session.delete(chat_session)
        db.session.commit()
        
        return make_response(jsonify({
            'success': True,
            'message': 'Chat session and its histories deleted successfully'
        }), 200)

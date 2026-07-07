from operator import itemgetter
import os
import time
import uuid
from flask import Response, make_response, jsonify, request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.chat_history import ChatHistory
from app.models.chat_session import ChatSession
from app.schemas.chat_history import ChatHistorySchema
from app.models import db
from pydantic import ValidationError

from app.utils.pdf_chat_completion import PdfChatCompletion
from flask import current_app

class ChatCompletionResource(Resource):
    
    def __init__(self):
        self.chat = PdfChatCompletion(current_app._get_current_object())

    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        params = {
            "chat_session_id": request.args.get('chat_session_id', type=int, default=0),
            "query": request.args.get('query'),
            "answer": "AI is typing...",
            "sources": {},
            "created_at": time.time(),
        }
        
        # Validate params using schema
        data = ChatHistorySchema(**params)
        
        chat_history = ChatHistory(
            chat_session_id=data.chat_session_id,
            user_id=user_id,
            query=data.query,
            answer=data.answer,
            sources=data.sources
        )
        
        db.session.add(chat_history)
        db.session.commit()
        
        count = db.session.query(ChatHistory).filter_by(
            chat_session_id=chat_history.chat_session_id
        ).count()
        
        if count == 1:
            chat_session = db.session.query(ChatSession).filter_by(
                id=chat_history.chat_session_id
            ).first()
            
            session_name = chat_history.query[:50] + '...' if len(chat_history.query) > 50 else chat_history.query
            chat_session.name = session_name
            db.session.commit()

        return Response(self.chat.generate_response(chat_history.to_dict()), content_type='text/event-stream')
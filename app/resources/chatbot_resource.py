from flask_restful import Resource
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.qa_chat_history import QAWithChatHistory

class ChatbotHistoryResource(Resource):
    @jwt_required()
    def get(self):
        """Get chat history for current user"""
        try:
            user_id = get_jwt_identity()
            limit = request.args.get('limit', 5, type=int)
            history = QAWithChatHistory.get_chat_history(user_id, limit)
            return jsonify({'success': True, "status": "success", "data": history})
        except Exception as e:
            return {'success': False, "status": "error", "message": str(e)}, 500

    @jwt_required()
    def post(self):
        """Ask a question with chat history context"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            query = data.get('query')
            
            if not query:
                return {'success': False,"status": "error", "message": "Query is required"}, 400

            result = QAWithChatHistory.qa_with_history(
                user_id=user_id,
                query=query,
                limit=data.get('limit', 5)
            )

            return jsonify({
                'success': True,
                "status": "success",
                "data": {
                    "answer": result['answer'],
                    "sources": result['sources']
                }
            })
        except Exception as e:
            return {'success': False, "status": "error", "message": str(e)}, 500
        
    @jwt_required()
    def delete(self):
        """Clear chat history for current user"""
        try:
            user_id = get_jwt_identity()
            # Implement chat history deletion logic here
            return {'success': True,"status": "success", "message": "Chat history cleared"}
        except Exception as e:
            return {'success': False,"status": "error", "message": str(e)}, 500

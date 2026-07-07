from typing import List, Dict, Any
from app.models import db
from app.models.chat_history import ChatHistory
from app.utils.pdf_extractor import PDFExtractor

class QAWithChatHistory:
    """Handles question answering with chat history stored in PostgreSQL."""

    @staticmethod
    def save_chat_history(user_id: int, query: str, answer: str, sources: List[Dict[str, Any]]) -> bool:
        try:
            chat_history = ChatHistory(
                user_id=user_id,
                query=query,
                answer=answer,
                sources=sources
            )
            db.session.add(chat_history)
            db.session.commit()
            return True
        except Exception as e:
            print(f"Error saving chat history: {str(e)}")
            db.session.rollback()
            return False

    @staticmethod
    def get_chat_history(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            histories = ChatHistory.query.filter_by(user_id=user_id)\
                .order_by(ChatHistory.created_at.desc())\
                .limit(limit)\
                .all()
            
            return [{
                "id": h.id,
                "query": h.query,
                "answer": h.answer,
                "sources": h.sources,
                "created_at": h.created_at.isoformat()
            } for h in histories]
        except Exception as e:
            print(f"Error retrieving chat history: {str(e)}")
            return []

    @staticmethod
    def qa_with_history(user_id: int, query: str, limit: int = 5) -> Dict[str, Any]:
        try:
            chat_history = QAWithChatHistory.get_chat_history(user_id, limit=3)
            qa_result = PDFExtractor.qa_documents(
                query=query,
                chat_history=chat_history,
                limit=limit
            )
            
            QAWithChatHistory.save_chat_history(
                user_id=user_id,
                query=query,
                answer=qa_result['answer'],
                sources=qa_result['sources']
            )
            
            return qa_result
        except Exception as e:
            print(f"Error in QA with history: {str(e)}")
            return {
                'answer': 'Sorry, I encountered an error while processing your question.',
                'sources': []
            }

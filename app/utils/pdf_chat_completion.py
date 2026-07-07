from operator import itemgetter
import os
import time
from typing import List
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import trim_messages
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_postgres import PGVector
from langchain.docstore.document import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_openai import ChatOpenAI
from app.models import db
from app.models.chat_history import ChatHistory
from app.utils.pdf_extractor import OpenAIConfig
from langchain_google_genai import ChatGoogleGenerativeAI

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
LLM_MODEL = "gpt-4-turbo-preview"

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
LLM_MODEL_GOOGLE = "gemini-2.5-flash"

store = {}

class PdfChatCompletion:
    
    def __init__(self, app=None):
        self.app = app
        # self.llm = ChatOpenAI(
        #     temperature=0,
        #     model=LLM_MODEL,
        #     openai_api_key=OPENAI_API_KEY
        # )
        self.llm = ChatGoogleGenerativeAI(
            model=LLM_MODEL_GOOGLE,
            google_api_key=GOOGLE_API_KEY,
            temperature=0,
            convert_system_message_to_human=True # Opsional, membantu kompatibilitas model lama
        )
        self.vector_store = OpenAIConfig.get_vector_store()

    def _update_chat_history(self, chat_history_id: int, full_answer: str, context: list):
        """Update chat history with answer and sources including similarity scores"""
        with self.app.app_context():
            chat_history = db.session.query(ChatHistory).filter_by(
                id=chat_history_id
            ).first()
            
            if chat_history:
                chat_history.answer = full_answer
                chat_history.sources = [{
                    'content': doc.page_content[:500],
                    'metadata': doc.metadata,
                    'score': doc.metadata.get('score', 0)
                } for doc in context]
                
                db.session.add(chat_history)
                db.session.commit()

    def generate_response(self, chat_history): 
        # generate a stream of responses using langchain (simply replace the invoke with stream)
        response = json.dumps(chat_history)
        yield f"data: [CHAT_HISTORY]{response}\n\n"
                
        chat_chain = self.get_chat_chain(chat_history)
        stream = chat_chain.stream({"input": chat_history.get('query')})
        # reformat stream to event-stream format
        full_answer = ""
        context = []
        for chunk in stream:
            answer = chunk.get("answer", "")
            if chunk.get("context", ""):
                context = chunk.get("context", [])
                
            if answer.strip():
                full_answer += answer
                answer = answer.replace("\n", "<br>")
                yield f"data: {answer}\n\n"
        
        self._update_chat_history(
            chat_history_id=chat_history.get('id'),
            full_answer=full_answer,
            context=context
        )
        
        yield "data: [DONE]\n\n"

    def _get_chat_histories(self, chat_session_id: int, user_id: int, limit: int = 3) -> str:
        """Get previous chat histories and format them as context"""
        chat_context = "\nChat History:\n"
        
        with self.app.app_context():
            chat_histories = db.session.query(ChatHistory).filter_by(
                chat_session_id=chat_session_id,
                user_id=user_id
            ).paginate(page=1, per_page=limit, error_out=False)
            
            if chat_histories:
                for hist in chat_histories:
                    chat_context += f"Question: {hist.query}\n"
                    chat_context += f"Answer: {hist.answer}\n\n"
                    
        return chat_context

    def get_chat_chain(self, chat_history, limit: int = 5):
        chat_context = self._get_chat_histories(
            chat_session_id=chat_history.get('chat_session_id'),
            user_id=chat_history.get('user_id')
        )

        system_prompt = (
            "Anda adalah Asisten AI untuk Perumda Air Minum Surya Sembada Kota Surabaya. "
            "Tugas utama Anda adalah membantu karyawan dan manajemen dalam memahami, menafsirkan, "
            "dan menemukan informasi dari dokumen internal perusahaan seperti Peraturan Direksi, "
            "SOP (Standard Operating Procedure), Surat Edaran, dan dokumen kebijakan lainnya.\n\n"
            "Jawaban Anda harus:\n"
            "- Berdasarkan isi dokumen internal perusahaan yang tersedia. "
            "Selalu sertakan referensi ke dokumen sumber, termasuk judul dan, jika memungkinkan, nomor halaman atau pasal.\n"
            "- Jika pertanyaan tidak dapat dijawab dari dokumen yang tersedia, nyatakan bahwa "
            "informasi tersebut tidak ditemukan dalam basis data dokumen internal. Jangan mengarang jawaban.\n"
            "- Jika pertanyaan tidak relevan dengan dokumen atau kebijakan internal perusahaan, "
            "berikan respons yang sopan dan nyatakan bahwa pertanyaan berada di luar cakupan Anda. "
            "Contoh: 'Pertanyaan ini berada di luar cakupan dokumen internal yang saya miliki.'\n"
            "- Gunakan bahasa yang profesional, jelas, dan lugas. Hindari jargon yang tidak perlu.\n"
            "- Selalu utamakan keakuratan dan objektivitas berdasarkan data yang ada.\n\n"
            f"{chat_context}\n"
            "Konteks Dokumen Internal Perusahaan:\n{context}\n"
        )


        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}")
        ])

        question_answer_chain = create_stuff_documents_chain(self.llm, prompt)
        rag_chain = create_retrieval_chain(
            self.vector_store.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": limit,
                    "lambda_mult": 0.7
                },
            ),
            question_answer_chain
        )

        return rag_chain
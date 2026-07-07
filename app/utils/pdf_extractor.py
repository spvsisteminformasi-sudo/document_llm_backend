from typing import List, Dict, Any

from sqlalchemy import text
from app.models import db
import os
from openai import OpenAI

from langchain_postgres import PGVector
from langchain.docstore.document import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_google_genai import ChatGoogleGenerativeAI

from app.utils.pdf_parser_national import PdfParserNational
from app.utils.pdf_parser_international import PDFParserInternational

# Configuration constants
TEMP_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'temp')

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
CONNECTION_STRING = os.getenv('SQLALCHEMY_DATABASE_URI') or os.getenv('DATABASE_URL') or ''


CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
EMBEDDING_MODEL = "text-embedding-3-large"
LLM_MODEL = "gpt-4-turbo-preview"

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
LLM_MODEL_GOOGLE = "gemini-2.5-flash"

class OpenAIConfig:
    """Configuration class for OpenAI settings"""
    @staticmethod
    def get_embeddings() -> OpenAIEmbeddings:
        return OpenAIEmbeddings(
            openai_api_key=OPENAI_API_KEY, 
            model=EMBEDDING_MODEL
        )
    
    @staticmethod
    def get_vector_store() -> PGVector:
        return PGVector(
            embeddings=OpenAIConfig.get_embeddings(),
            collection_name="document_embeddings",
            connection=CONNECTION_STRING,
            use_jsonb=True,
        )
    
    @staticmethod
    def delete_vectors_by_document_id(document_id: int) -> bool:
        """
        Delete all vector store entries for a specific document_id
        
        Args:
            document_id: ID of the document to delete vectors for
            
        Returns:
            bool: Success status of the operation
        """
        try:
            vector_store = OpenAIConfig.get_vector_store()
            with vector_store._make_sync_session() as session:
                session.execute(
                    text("DELETE FROM langchain_pg_embedding WHERE cmetadata->>'document_id' = :document_id"),
                    {"document_id": str(document_id)}
                )
                session.commit()
                print(f"Deleted vectors for document_id: {document_id}")
            return True
        except Exception as e:
            print(f"Error deleting vectors: {str(e)}")
            return False

class PDFExtractor:
    """Handles PDF document extraction, searching, and QA functionality"""

    @staticmethod
    def extract_and_save(document) -> bool:
        """
        Extract content from PDF and save to database with embeddings
        
        Args:
            document: Document object containing PDF information
            
        Returns:
            bool: Success status of the operation
        """
        vector_store = OpenAIConfig.get_vector_store()
        docs = []
        parser = PDFParserInternational(document.full_path)
            
        doc_list = parser.parse()
        
        for index, entry in enumerate(doc_list):
            doc = Document(
                page_content=entry['content'],
                metadata={
                    "id": f"{document.id}{index}",
                    "document_id": document.id,
                    "title": document.title,
                    "source": document.full_path,
                    "page_number": entry['page_number'],
                }
            )
            docs.append(doc)
                
        vector_store.add_documents(docs, ids=[doc.metadata["id"] for doc in docs])
        return True

    @staticmethod
    def search_documents(query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar documents based on query
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of document results with similarity scores
        """
        try:
            vector_store = OpenAIConfig.get_vector_store()
            search_results = vector_store.similarity_search_with_score(query, k=limit)
            
            return [{
                'content': doc.page_content,
                'metadata': doc.metadata,
                'similarity_score': score
            } for doc, score in search_results]
            
        except Exception as e:
            print(f"Error searching documents: {str(e)}")
            return []

    @staticmethod
    def qa_documents(query: str, chat_history: List = [], limit: int = 5) -> Dict[str, Any]:
        """
        Question answering system for documents with fallback to general answer if no relevant documents.
        
        Args:
            query: Question to be answered
            chat_history: List of previous chat interactions
            limit: Maximum number of documents to consider
            
        Returns:
            Dictionary containing answer and source documents
        """
        try:
            vector_store = OpenAIConfig.get_vector_store()
            
            # llm = ChatOpenAI(
            #     temperature=0,
            #     model=LLM_MODEL,
            #     openai_api_key=OPENAI_API_KEY
            # )

            llm = ChatGoogleGenerativeAI(
                model=LLM_MODEL_GOOGLE,
                google_api_key=GOOGLE_API_KEY,
                temperature=0,
                convert_system_message_to_human=True # Opsional, membantu kompatibilitas model lama
            )

            # Format chat history into context
            chat_context = "\nRiwayat Chat Sebelumnya:\n"
            if chat_history:
                for hist in chat_history[-3:]:  # Use last 3 conversations
                    chat_context += f"Pertanyaan: {hist.query}\n"
                    chat_context += f"Jawaban: {hist.answer}\n\n"
            
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

            question_answer_chain = create_stuff_documents_chain(llm, prompt)
            rag_chain = create_retrieval_chain(
                vector_store.as_retriever(
                    search_type="mmr",
                    search_kwargs={
                        "k": limit,
                        "lambda_mult": 0.7
                    },
                ),
                question_answer_chain
            )

            results = rag_chain.invoke({"input": query})
            sources = results.get('context', [])
            
            if not sources:
                fallback_prompt = (
                    "Anda adalah asisten hukum maritim yang cerdas. "
                    "Pertanyaan berikut tidak memiliki referensi dari dokumen. "
                    "Jawablah sebaik mungkin berdasarkan pengetahuan umum Anda sebagai AI:\n\n"
                    f"{chat_context}\n"
                    f"Pertanyaan: {query}"
                )
                fallback_answer = llm.invoke(fallback_prompt)
                return {
                    'answer': fallback_answer.content,
                    'sources': []
                }
            
            return {
                'answer': results['answer'],
                'sources': [{
                    'content': doc.page_content[:500],
                    'metadata': doc.metadata
                } for doc in sources]
            }
            
        except Exception as e:
            print(f"Error in QA system: {str(e)}")
            return {
                'answer': 'Maaf, terjadi kesalahan saat memproses pertanyaan Anda.',
                'sources': []
            }

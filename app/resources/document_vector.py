from flask import make_response, jsonify, request
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from app.models import db
from openai import OpenAI
from sqlalchemy import text
from app.utils.pdf_extractor import PDFExtractor
import os

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

class DocumentVectorResource(Resource):
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
    
    def get_embedding(self, text):
        response = self.client.embeddings.create(input=text,
            model="text-embedding-ada-002")
        return response.data[0].embedding

    @jwt_required()
    def get(self, id=None):
        # Get pagination parameters
        qa = request.args.get('qa', type=str)
        
        if qa:
            # Use OpenAI's search API
            search_results = PDFExtractor.qa_documents(qa)

            return make_response(jsonify({
                'data': search_results,
            }), 200)
        
    
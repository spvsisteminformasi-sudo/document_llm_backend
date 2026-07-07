from langchain_pymupdf4llm import PyMuPDF4LLMLoader
from typing import Dict, List
import re

from langchain_text_splitters import RecursiveCharacterTextSplitter

class PDFParserInternational:
    """
    PDF Parser for International Documents
    This class handles the extraction and parsing of text from PDF files.
    It uses the PyMuPDF4LLMLoader for loading PDF files and
    RecursiveCharacterTextSplitter for splitting text into chunks.
    """
    def __init__(self, file_path: str):
        self.file_path = file_path
        loader = PyMuPDF4LLMLoader(
            file_path, 
            mode='page', 
            table_strategy="lines"
        )
        self.doc = loader.load()
        self.raw_text = ""
        self.entries = []
        
    def extract_text(self) -> str:
        """Extract text from PDF file"""
        try:
            text = ""
            for page in self.doc:
                text += page.page_content 
                text += "-------THIS IS A CUSTOM END OF PAGE-------"
            self.raw_text = text
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
    
    def parse(self) -> List[str]:
        """Split text into semantically meaningful chunks"""
        if not self.raw_text:
            self.extract_text()
            
        try:
            text_splitter = RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap=100)
            
            chunks = text_splitter.split_text(self.raw_text)
            
            # Split full text into pages using delimiter
            page_number = 1
            for chunk in chunks:
                # Count delimiters before this chunk to determine page number
                delimiter_count = chunk.count("-------THIS IS A CUSTOM END OF PAGE-------")
                page_number += delimiter_count
                
                entry = {
                    "content": chunk.replace("-------THIS IS A CUSTOM END OF PAGE-------", ""),
                    "page_number": page_number
                }
                self.entries.append(entry)
            return self.entries
        except Exception as e:
            raise Exception(f"Error splitting text: {str(e)}")
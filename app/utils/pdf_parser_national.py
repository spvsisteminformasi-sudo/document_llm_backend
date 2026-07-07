from langchain_pymupdf4llm import PyMuPDF4LLMLoader
import re
import json
from typing import List, Dict


class PdfParserNational:
    def __init__(self, file_path: str):
        self.file_path = file_path
        loader = PyMuPDF4LLMLoader(file_path, mode='page', table_strategy="lines")
        self.doc = loader.load()
        self.entries: List[Dict] = []

    def extract_title_and_preamble(self):
        full_text = "\n".join([page.page_content for page in self.doc[:5]])

        nomor_match = re.search(r'NOMOR\s+(\d+)\s+TAHUN\s+(\d+)', full_text, re.IGNORECASE)
        if nomor_match:
            self.number = nomor_match.group(1)
            self.year = nomor_match.group(2)

        judul_match = re.search(r'TENTANG\s+(.*?)\n', full_text, re.IGNORECASE)
        if judul_match:
            self.title = judul_match.group(1).strip().title()

    def parse(self):
        self.extract_title_and_preamble()

        chapter_pattern = re.compile(r'\bBAB\s+([IVXLCDM]+)\b(?:\s+(.*))?', re.IGNORECASE)

        current_chapter = None
        current_page = None
        buffer = []

        for page_num, page in enumerate(self.doc, start=1):
            text = page.page_content
            lines = text.split('\n')

            for line in lines:
                line = line.strip()

                # Deteksi BAB
                chapter_match = chapter_pattern.match(line)
                if chapter_match:
                    self._save_chapter(current_chapter, buffer, current_page)
                    roman, title = chapter_match.groups()
                    current_chapter = f"BAB {roman}"
                    if title:
                        current_chapter += f" - {title.strip()}"
                    current_page = page_num
                    buffer = [line]  # Simpan judul BAB juga ke dalam content
                    continue

                if current_chapter:
                    buffer.append(line)

        self._save_chapter(current_chapter, buffer, current_page)
        return self.entries

    def _save_chapter(self, chapter, buffer, page):
        if chapter and buffer:
            entry = {
                "title": self.title,
                "content": "\n".join(buffer).strip(),
                "page_number": page
            }
            self.entries.append(entry)

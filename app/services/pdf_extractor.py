"""
PDF text extraction service.
"""
import io
from typing import Optional
import PyPDF2
import pdfplumber


class PDFExtractor:
    """Service for extracting text from PDF files."""
    
    @staticmethod
    def extract_text(pdf_content: bytes) -> str:
        """
        Extract text from PDF content.
        
        Args:
            pdf_content: PDF file content as bytes
            
        Returns:
            Extracted text as string
            
        Raises:
            ValueError: If PDF cannot be processed
        """
        text = ""
        
        # Try pdfplumber first (better for complex layouts)
        try:
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                pages_text = []
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        pages_text.append(page_text)
                text = "\n\n".join(pages_text)
                
                if text.strip():
                    return text.strip()
        except Exception as e:
            # Fallback to PyPDF2 if pdfplumber fails
            pass
        
        # Fallback to PyPDF2
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            pages_text = []
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)
            text = "\n\n".join(pages_text)
            
            if not text.strip():
                raise ValueError("No text could be extracted from the PDF")
                
            return text.strip()
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")


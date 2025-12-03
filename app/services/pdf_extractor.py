"""
PDF text extraction service with multiple extraction methods for better compatibility.
"""
import io
import re
import logging
import PyPDF2
import pdfplumber

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Service for extracting text from PDF files with multiple fallback methods."""
    
    @staticmethod
    def extract_text(pdf_content: bytes) -> str:
        """
        Extract text from PDF content using multiple extraction methods.
        
        Tries multiple extraction methods in order:
        1. pdfplumber with table extraction (best for structured data)
        2. pdfplumber standard extraction
        3. pypdfium2 (if available)
        4. PyPDF2 (fallback)
        
        Args:
            pdf_content: PDF file content as bytes
            
        Returns:
            Extracted text as string (normalized and cleaned)
            
        Raises:
            ValueError: If PDF cannot be processed
        """
        extraction_methods = [
            PDFExtractor._extract_with_pdfplumber_tables,
            PDFExtractor._extract_with_pdfplumber,
            PDFExtractor._extract_with_pypdfium2,
            PDFExtractor._extract_with_pypdf2,
        ]
        
        last_error = None
        for method in extraction_methods:
            try:
                text = method(pdf_content)
                if text and len(text.strip()) > 50:  # Minimum viable text
                    normalized_text = PDFExtractor._normalize_text(text)
                    logger.info(f"Successfully extracted text using {method.__name__}, length: {len(normalized_text)}")
                    return normalized_text
            except Exception as e:
                last_error = e
                logger.debug(f"Extraction method {method.__name__} failed: {str(e)}")
                continue
        
        # If all methods failed, try OCR as last resort (optional)
        try:
            text = PDFExtractor._extract_with_ocr(pdf_content)
            if text and len(text.strip()) > 50:
                normalized_text = PDFExtractor._normalize_text(text)
                logger.info(f"Successfully extracted text using OCR, length: {len(normalized_text)}")
                return normalized_text
        except Exception as e:
            logger.debug(f"OCR extraction failed: {str(e)}")
        
        error_msg = "No text could be extracted from the PDF using any available method"
        if last_error:
            error_msg += f". Last error: {str(last_error)}"
        raise ValueError(error_msg)
    
    @staticmethod
    def _extract_with_pdfplumber_tables(pdf_content: bytes) -> str:
        """Extract text using pdfplumber with special attention to tables and layout (better for Canva PDFs)."""
        pages_text = []
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Try layout-based extraction first (better for Canva PDFs with separate text boxes)
                # This preserves spatial relationships and ordering
                try:
                    # Extract words with their positions to maintain order
                    words = page.extract_words(keep_blank_chars=False, x_tolerance=3, y_tolerance=3)
                    if words:
                        # Sort by y position (top to bottom), then x position (left to right)
                        words_sorted = sorted(words, key=lambda w: (round(w['top'], 1), w['x0']))
                        # Reconstruct text maintaining order
                        page_text = ""
                        prev_y = None
                        for word in words_sorted:
                            current_y = round(word['top'], 1)
                            # Add newline if we moved to a new line
                            if prev_y is not None and abs(current_y - prev_y) > 5:
                                page_text += "\n"
                            page_text += word['text'] + " "
                            prev_y = current_y
                        if page_text.strip():
                            pages_text.append(page_text.strip())
                            continue
                except Exception:
                    pass
                
                # Fallback to standard text extraction
                page_text = page.extract_text() or ""
                
                # Extract text from tables (important for experience dates)
                tables = page.extract_tables()
                if tables:
                    table_texts = []
                    for table in tables:
                        if table:
                            # Convert table to readable text format
                            for row in table:
                                if row:
                                    # Filter out None values and join with spaces
                                    row_text = " | ".join(str(cell) if cell else "" for cell in row if cell)
                                    if row_text.strip():
                                        table_texts.append(row_text)
                    if table_texts:
                        page_text += "\n" + "\n".join(table_texts)
                
                if page_text.strip():
                    pages_text.append(page_text)
        
        return "\n\n".join(pages_text)
    
    @staticmethod
    def _extract_with_pdfplumber(pdf_content: bytes) -> str:
        """Extract text using pdfplumber standard method."""
        pages_text = []
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)
        return "\n\n".join(pages_text)
    
    @staticmethod
    def _extract_with_pypdfium2(pdf_content: bytes) -> str:
        """Extract text using pypdfium2 (if available)."""
        try:
            import pypdfium2 as pdfium
        except ImportError:
            raise ValueError("pypdfium2 not available")
        
        pages_text = []
        pdf = pdfium.PdfDocument(pdf_content)
        try:
            for page_num in range(len(pdf)):
                page = pdf.get_page(page_num)
                textpage = page.get_textpage()
                page_text = textpage.get_text_range()
                if page_text:
                    pages_text.append(page_text)
        finally:
            pdf.close()
        
        return "\n\n".join(pages_text)
    
    @staticmethod
    def _extract_with_pypdf2(pdf_content: bytes) -> str:
        """Extract text using PyPDF2 (fallback method)."""
        pages_text = []
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                pages_text.append(page_text)
        return "\n\n".join(pages_text)
    
    @staticmethod
    def _extract_with_ocr(pdf_content: bytes) -> str:
        """
        Extract text using OCR (Tesseract) for scanned PDFs.
        This is optional and requires pytesseract and tesseract-ocr to be installed.
        """
        try:
            import pytesseract  # type: ignore
            from PIL import Image  # type: ignore
            import fitz  # type: ignore # PyMuPDF
        except ImportError:
            raise ValueError("OCR dependencies not available (pytesseract, Pillow, PyMuPDF)")
        
        # Convert PDF pages to images and OCR them
        pages_text = []
        pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
        
        try:
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                # Render page to image
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                # OCR the image
                page_text = pytesseract.image_to_string(img)
                if page_text.strip():
                    pages_text.append(page_text)
        finally:
            pdf_document.close()
        
        return "\n\n".join(pages_text)
    
    @staticmethod
    def _normalize_text(text: str) -> str:
        """
        Normalize and clean extracted text to improve date/experience extraction.
        
        - Fixes common OCR/extraction issues
        - Normalizes whitespace
        - Preserves date formats
        - Fixes common character encoding issues
        """
        if not text:
            return ""
        
        # Fix common date format issues FIRST (before normalizing whitespace)
        # Fix dates with spaces in the middle: "201 9" -> "2019", "20 15" -> "2015"
        # Pattern: 4 digits with space(s) in between
        text = re.sub(r'(\d{1,2})\s+(\d{2,4})', r'\1\2', text)
        # Fix "20 1 5" -> "2015", "20 1 0" -> "2010", etc. (3+ digit groups)
        text = re.sub(r'(\d{2})\s+(\d{1,2})\s+(\d{1,2})', r'\1\2\3', text)
        # Fix dates in format like "06/201 9" -> "06/2019" or "04/202 3" -> "04/2023"
        text = re.sub(r'(\d{1,2}/)(\d{1,3})\s+(\d{1,2})', r'\1\2\3', text)
        # Fix dates like "201 9" -> "2019" or "20 19" -> "2019" (year with space in middle)
        # This handles cases where a 4-digit year is split: "201 9", "20 19", "2 019", etc.
        def fix_year_space(match):
            parts = match.group(0).split()
            combined = ''.join(parts)
            # If it looks like a year (3-4 digits), combine them
            if len(combined) >= 3 and len(combined) <= 4 and all(c.isdigit() for c in combined):
                return combined
            return match.group(0)
        text = re.sub(r'\d{2,4}\s+\d{1,2}(?!\s*\d)', fix_year_space, text)
        
        # Normalize whitespace (multiple spaces/newlines to single space, but preserve line breaks for structure)
        # First, normalize multiple spaces to single space
        text = re.sub(r' +', ' ', text)
        # Then normalize multiple newlines to double newline (paragraph break)
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Fix "Jan uary" -> "January", "Feb ruary" -> "February", etc.
        month_fixes = {
            r'Jan\s+uary': 'January',
            r'Feb\s+ruary': 'February',
            r'Mar\s+ch': 'March',
            r'Apr\s+il': 'April',
            r'May\s+': 'May',
            r'Jun\s+e': 'June',
            r'Jul\s+y': 'July',
            r'Aug\s+ust': 'August',
            r'Sep\s+tember': 'September',
            r'Oct\s+ober': 'October',
            r'Nov\s+ember': 'November',
            r'Dec\s+ember': 'December',
        }
        for pattern, replacement in month_fixes.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Fix common OCR mistakes in dates
        # "O" -> "0" in dates (e.g., "2O15" -> "2015")
        text = re.sub(r'(\d)O(\d)', r'\g<1>0\g<2>', text)
        # "l" -> "1" in dates (e.g., "2Ol5" -> "2015")
        text = re.sub(r'(\d)l(\d)', r'\g<1>1\g<2>', text)
        
        # Normalize date separators
        text = re.sub(r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})', r'\1/\2/\3', text)
        
        # Fix "Present" variations
        present_variations = ['Present', 'present', 'PRESENT', 'Current', 'current', 'CURRENT', 
                             'Now', 'now', 'NOW', 'Till date', 'till date', 'TILL DATE']
        for variant in present_variations:
            text = re.sub(rf'\b{variant}\b', 'Present', text, flags=re.IGNORECASE)
        
        # Final cleanup: ensure dates are properly formatted
        # Fix dates like "04/2023" that might have been corrupted
        # Ensure year is 4 digits when possible
        text = re.sub(r'(\d{1,2}/)(\d{2})(?!\d)', lambda m: m.group(1) + ('20' + m.group(2) if int(m.group(2)) < 50 else '19' + m.group(2)), text)
        
        # Trim and return
        return text.strip()


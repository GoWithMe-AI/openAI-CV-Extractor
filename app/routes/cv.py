"""
CV processing routes.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from app.models.response import CVSummaryResponse, ErrorResponse
from app.services.pdf_extractor import PDFExtractor
from app.services.ai_service import AIService
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["CV"])

# Initialize services
pdf_extractor = PDFExtractor()

# Lazy initialization of AI service to handle missing API keys gracefully
_ai_service = None

def get_ai_service():
    """Get or create AI service instance."""
    global _ai_service
    if _ai_service is None:
        try:
            _ai_service = AIService()
        except ValueError as e:
            logger.error(f"AI service initialization failed: {str(e)}")
            raise ValueError(f"AI service not configured: {str(e)}")
    return _ai_service


@router.post(
    "/process-cv",
    response_model=CVSummaryResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Process CV PDF and extract summary",
    description="Upload a CV PDF file to extract summary, skills, and experience years"
)
async def process_cv(file: UploadFile = File(...)):
    """
    Process a CV PDF file and return structured summary.
    
    Args:
        file: PDF file upload
        
    Returns:
        CVSummaryResponse with summary, skills, and experience_years
    """
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
        allowed_extensions = settings.allowed_extensions_set
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Read file content
        content = await file.read()
        
        # Validate file size
        if len(content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )
        
        # Extract text from PDF
        try:
            cv_text = pdf_extractor.extract_text(content)
            if not cv_text or len(cv_text.strip()) < 50:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not extract sufficient text from PDF. Please ensure the PDF contains readable text."
                )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        # Get AI summary
        try:
            ai_service = get_ai_service()
            result = await ai_service.summarize_cv(cv_text)
        except ValueError as e:
            logger.error(f"AI service error: {str(e)}")
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            if "not configured" in str(e).lower() or "required" in str(e).lower():
                status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            raise HTTPException(
                status_code=status_code,
                detail=f"AI processing failed: {str(e)}"
            )
        
        # Return structured response
        return CVSummaryResponse(
            summary=result["summary"],
            skills=result["skills"],
            experience_years=result["experience_years"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing CV: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "CV Extractor API"}


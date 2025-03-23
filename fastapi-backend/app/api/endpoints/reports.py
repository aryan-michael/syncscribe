from fastapi import APIRouter, HTTPException, Path, Response
from typing import Optional
from fastapi.responses import FileResponse
from app.schemas.zoom import ReportsResponse, ReportContentResponse
from app.services.report_service import ReportService

router = APIRouter()

@router.get("/{meeting_id}", response_model=ReportsResponse)
async def get_reports(meeting_id: str = Path(..., description="Meeting ID")):
    """
    Get available reports for a meeting
    """
    success, reports, error = ReportService.get_meeting_reports(meeting_id)
    
    if not success:
        return {
            "success": False,
            "reports": [],
            "error": error
        }
    
    return {
        "success": True,
        "reports": reports
    }

@router.get("/content/{filename}", response_model=ReportContentResponse)
async def get_report_content(filename: str = Path(..., description="Report filename")):
    """
    Get content of a specific report file
    """
    print(f"Getting content for file: {filename}")
    success, content, filename, error = ReportService.get_report_content(filename)
    
    if not success:
        print(f"Error getting report content: {error}")
        return {
            "success": False,
            "error": error,
            "filename": filename
        }
    
    return {
        "success": True,
        "content": content,
        "filename": filename
    }

    
@router.get("/download/{filename}")
async def download_report(filename: str = Path(..., description="Report filename")):
    """
    Download a report file
    """
    success, content, filename, error = ReportService.get_report_content(filename)
    
    if not success:
        raise HTTPException(status_code=404, detail=error)
    
    # For text files, return as attachment
    from app.core.config import settings
    file_path = f"{settings.MEETING_OUTPUTS_DIR}/{filename}"
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )

@router.get("/pdf/{meeting_id}")
async def generate_pdf_report(meeting_id: str = Path(..., description="Meeting ID")):
    """
    Generate a PDF report for a meeting
    """
    # This is a placeholder - in a real implementation, you would:
    # 1. Get meeting transcript, summary, and insights
    # 2. Call ReportService.generate_pdf_report
    # 3. Return the PDF file
    
    raise HTTPException(status_code=501, detail="Not implemented yet")
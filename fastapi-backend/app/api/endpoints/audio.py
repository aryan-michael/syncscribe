from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas.audio import AudioProcessingResponse
from app.services.audio_service import AudioService

router = APIRouter()

@router.post("/upload", response_model=AudioProcessingResponse)
async def upload_audio(file: UploadFile = File(...)):
    """
    Process an uploaded audio file and return transcription, summary, and insights
    """
    success, transcript, summary, insights, error = await AudioService.process_audio(file)
    
    if not success:
        return {
            "success": False,
            "error": error
        }
    
    return {
        "success": True,
        "transcript": transcript,
        "summary": summary or "Summary generation skipped for testing",
        "insights": insights or ["Insights generation skipped for testing"]
    }
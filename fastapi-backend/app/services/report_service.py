import os
import sys
from typing import Dict, List, Tuple, Optional, Any
from app.core.config import settings

# Add the project root to Python path to import ZoomBot
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.services.zoom_service import active_bots, meeting_statuses

class ReportService:
    """Service for handling meeting reports and recordings"""
    
    @staticmethod
    def get_meeting_reports(meeting_id: str) -> Tuple[bool, List[Dict[str, str]], Optional[str]]:
        """Get available reports for a meeting"""
        print(f"Looking for reports for meeting ID: {meeting_id}")
        print(f"Meeting statuses: {meeting_statuses}")
        
        # Find the session for this meeting
        session_id = None
        for mid, status in meeting_statuses.items():
            if mid == meeting_id:
                session_id = status.get('session_id')
                break
        
        if not session_id or session_id not in active_bots:
            print(f"No session found for meeting ID: {meeting_id}")
            print(f"Active bots: {list(active_bots.keys())}")
            return False, [], "No session found for this meeting"
        
        bot = active_bots[session_id]
        
        # Check if we have a meeting start time
        if not hasattr(bot, 'meeting_start_time'):
            print(f"No meeting_start_time attribute on bot for session {session_id}")
            return False, [], "No recordings available for this meeting"
        
        # Get all files in meeting_outputs directory
        meeting_time = bot.meeting_start_time
        report_files = []
        
        try:
            # Check if directory exists
            output_dir = settings.MEETING_OUTPUTS_DIR
            print(f"Checking for files in directory: {output_dir}")
            
            if not os.path.exists(output_dir):
                print(f"Directory does not exist: {output_dir}")
                os.makedirs(output_dir, exist_ok=True)
                return False, [], f"Report directory does not exist: {output_dir}"
            
            files = os.listdir(output_dir)
            print(f"Files in directory: {files}")
            
            # Find files matching meeting time
            for filename in files:
                if meeting_time in filename:
                    file_path = os.path.join(output_dir, filename)
                    print(f"Found matching file: {filename}")
                    report_files.append({
                        "filename": filename,
                        "path": file_path,
                        "type": "transcript" if "transcript" in filename else "summary" if "summary" in filename else "report"
                    })
            
            return True, report_files, None
        except Exception as e:
            print(f"Error getting reports: {str(e)}")
            import traceback
            traceback.print_exc()
            return False, [], str(e)
    
    @staticmethod
    def get_report_content(filename: str) -> Tuple[bool, Optional[str], str, Optional[str]]:
        """Get content of a specific report file"""
        try:
            file_path = os.path.join(settings.MEETING_OUTPUTS_DIR, filename)
            
            if not os.path.exists(file_path):
                return False, None, filename, "File not found"
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            return True, content, filename, None
        except Exception as e:
            return False, None, filename, str(e)
    
    @staticmethod
    def generate_pdf_report(meeting_id: str, transcript: str, summary: str, insights: List[str]) -> Tuple[bool, Optional[str], Optional[str]]:
        """Generate a PDF report for a meeting"""
        try:
            # Logic to generate PDF would go here
            # This is a placeholder for the actual implementation
            
            # Return path to the generated PDF
            pdf_path = os.path.join(settings.MEETING_OUTPUTS_DIR, f"{meeting_id}_report.pdf")
            
            return True, pdf_path, None
        except Exception as e:
            return False, None, str(e)
Zoom Bot API
A FastAPI-based application for controlling Zoom meetings and processing recordings using AI.
Features

Create and join Zoom meetings
Record meeting audio and video
Transcribe meeting recordings
Generate summaries and insights using AI
Produce PDF reports of meeting content

Project Structure
This project follows the Model-View-Controller (MVC) architecture pattern:

Models: Data structures and database interactions
Views: API schemas and responses (using Pydantic)
Controllers: Business logic in service classes and API endpoints

Copy📁 app/
├── 📁 api/             # API endpoints and router
├── 📁 core/            # Core configuration and security
├── 📁 models/          # Data models
├── 📁 schemas/         # Pydantic schemas for validation
├── 📁 services/        # Business logic services
├── 📁 utils/           # Utility functions
└── 📄 main.py          # Application entry point
Setup and Installation
Prerequisites

Python 3.9+
Zoom API credentials
Cohere API key (for AI summaries)
Google Cloud account with Vertex AI enabled (for insights)

Installation

Clone the repository:
Copygit clone https://github.com/yourusername/zoom-bot-api.git
cd zoom-bot-api

Create a virtual environment:
Copypython -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install dependencies:
Copypip install -r requirements.txt

Create a .env file with your configuration:
Copy# API Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Zoom API Credentials
ZOOM_API_KEY=your_zoom_api_key
ZOOM_API_SECRET=your_zoom_api_secret
ZOOM_SDK_KEY=your_zoom_sdk_key
ZOOM_SDK_SECRET=your_zoom_sdk_secret

# External API Keys
COHERE_API_KEY=your_cohere_api_key

# Google Cloud Settings
GOOGLE_APPLICATION_CREDENTIALS=path_to_credentials.json
GOOGLE_CLOUD_PROJECT=your_gcp_project_id
GOOGLE_CLOUD_LOCATION=us-central1

Run the application:
Copypython -m app.main


API Endpoints
Audio Processing

POST /api/audio/upload: Upload and process an audio recording

Zoom Meetings

POST /api/zoom/signature: Generate a Zoom Meeting SDK signature
POST /api/zoom/sessions: Create a new ZoomBot session
POST /api/zoom/meetings/create: Create a new Zoom meeting
POST /api/zoom/meetings/join: Join an existing Zoom meeting
POST /api/zoom/meetings/start-recording: Start recording a meeting
POST /api/zoom/meetings/stop-recording: Stop recording a meeting
POST /api/zoom/meetings/end: End a Zoom meeting
GET /api/zoom/meetings/list: List Zoom meetings
GET /api/zoom/meetings/status/{meeting_id}: Get status of a meeting

Meeting Reports

GET /api/reports/{meeting_id}: Get available reports for a meeting
GET /api/reports/content/{filename}: Get content of a report file
GET /api/reports/download/{filename}: Download a report file

Development
Running in Debug Mode
Copyuvicorn app.main:app --reload --host 0.0.0.0 --port 8000
Documentation
API documentation is available at:

Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc

License
This project is licensed under the MIT License - see the LICENSE file for details.
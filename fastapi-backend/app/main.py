# app/main.py
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI app
app = FastAPI(
    title="Zoom Bot API",
    description="API for controlling Zoom meetings and processing recordings",
    version="1.0.0"
)

# Add CORS middleware - note we're allowing all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import router after CORS setup to avoid circular imports
from app.api.router import api_router

# Include API router
app.include_router(api_router, prefix="/api")

# Root endpoint
@app.get("/")
async def root():
    return {"status": "online", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=5000,  # Change to port 5000 to match frontend expectations
        reload=True
    )
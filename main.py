# FastAPI application for LLM-assisted code generation and deployment
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import logging
from src.validate_secrets import validate_secret
from src.round1 import round1
from src.round2 import round2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Pydantic models for request validation
class AttachmentModel(BaseModel):
    name: str = Field(..., description="File name")
    url: str = Field(..., description="Data URI or file URL")


class TaskRequest(BaseModel):
    email: str = Field(..., description="Student email")
    secret: str = Field(..., description="Authentication secret")
    task: str = Field(..., description="Task identifier")
    round: int = Field(..., ge=1, le=2, description="Round number (1 or 2)")
    nonce: str = Field(..., description="Unique nonce")
    brief: str = Field(..., description="Task description/brief")
    checks: Optional[List[str]] = Field(default=[], description="Validation checks")
    evaluation_url: str = Field(..., description="URL to notify evaluation server")
    attachments: Optional[List[AttachmentModel]] = Field(default=[], description="File attachments")


class SuccessResponse(BaseModel):
    status: str = Field(default="success")
    message: str = Field(...)
    repo_url: str = Field(...)
    pages_url: str = Field(...)
    commit_sha: str = Field(...)


class ErrorResponse(BaseModel):
    status: str = Field(default="error")
    message: str = Field(...)


app = FastAPI(title="LLM App Developer", version="1.0.0")

# Add CORS middleware to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/submit", response_model=SuccessResponse)
async def submit(task_request: TaskRequest):
    """
    Accept task requests from the evaluation server and process them.
    
    Returns repo URL, Pages URL, and commit SHA on success.
    """
    try:
        data = task_request.model_dump()
        logger.info(f"Received request: email={data.get('email')}, round={data.get('round')}")
        
        # Validate the secret
        if not validate_secret(data.get("secret", "")):
            logger.warning(f"Invalid secret for {data.get('email')}")
            raise HTTPException(status_code=401, detail="Invalid secret")
        
        # Process based on round
        round_num = data.get("round")
        
        if round_num == 1:
            logger.info(f"Processing Round 1 for {data.get('email')}")
            result = await round1(data)
        elif round_num == 2:
            logger.info(f"Processing Round 2 for {data.get('email')}")
            result = await round2(data)
        else:
            raise HTTPException(status_code=400, detail="Invalid round number")
        
        if result.get("status") == "error":
            logger.error(f"Processing failed: {result.get('message')}")
            raise HTTPException(status_code=500, detail=result.get('message'))
        
        logger.info(f"Successfully processed request for {data.get('email')}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "LLM App Developer",
        "version": "1.0.0",
        "endpoints": {
            "POST /submit": "Process task requests (Round 1 or 2)",
            "GET /health": "Health check",
        },
        "documentation": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
    )
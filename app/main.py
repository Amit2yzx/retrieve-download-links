"""
Main FastAPI application for URL analyzer.
"""
import os
from typing import Dict, List, Optional, Any
import asyncio

from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, HttpUrl

from app.agents import url_analyzer_agent

# Create FastAPI app
app = FastAPI(title="URL Analyzer and Download Link Extractor")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")


class URLRequest(BaseModel):
    """Request model for URL analysis."""
    url: str


class URLResponse(BaseModel):
    """Response model for URL analysis."""
    success: bool
    url: str
    error: Optional[str] = None
    is_direct_download: bool = False
    download_links: List[str] = []
    recommended_link: Optional[str] = None
    title: Optional[str] = None
    content_type: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the index page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/analyze", response_model=URLResponse)
async def analyze_url(url_request: URLRequest):
    """Analyze a URL and extract download links."""
    try:
        # Initialize agent state
        initial_state = {"url": url_request.url}
        
        # Run the agent
        result = await url_analyzer_agent.ainvoke(initial_state)
        
        # Extract final result
        final_result = result.get("final_result", {})
        if not final_result:
            raise HTTPException(status_code=500, detail="Failed to analyze URL")
        
        return final_result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing URL: {str(e)}")


@app.post("/analyze-form")
async def analyze_url_form(request: Request, url: str = Form(...)):
    """Analyze a URL from a form submission and render the results page."""
    try:
        # Initialize agent state
        initial_state = {"url": url}
        
        # Run the agent
        result = await url_analyzer_agent.ainvoke(initial_state)
        
        # Extract final result
        final_result = result.get("final_result", {})
        if not final_result:
            return templates.TemplateResponse(
                "error.html", 
                {"request": request, "error": "Failed to analyze URL"}
            )
        
        return templates.TemplateResponse(
            "results.html", 
            {"request": request, "result": final_result}
        )
    
    except Exception as e:
        return templates.TemplateResponse(
            "error.html", 
            {"request": request, "error": f"Error analyzing URL: {str(e)}"}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

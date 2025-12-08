from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from ddgs import DDGS
from openai import OpenAI
from pydantic import BaseModel
from typing import List, Optional
import os
from validation import ValidateURLs
import holidays
from datetime import datetime, timedelta
import subprocess

app = FastAPI(
    title="Lead Management API",
    description="FastAPI server for lead management with restricted access",
    version="1.0.0",
)

# Configure CORS to allow only https://n8n.sesai.in
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://n8n.sesai.in",
        "http://127.0.0.1:8000",
        "https://n8n.thelinkai.com",
        "http://69.62.82.163:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware to verify origin
@app.middleware("http")
async def verify_origin(request: Request, call_next):
    """
    Middleware to verify that requests come from allowed origin.
    Checks both Origin and Referer headers.
    """
    origin = request.headers.get("origin")
    referer = request.headers.get("referer")

    allowed_origins = [
        "https://n8n.sesai.in",
        "http://127.0.0.1:8000",
        "https://n8n.thelinkai.com",
        "http://69.62.82.163:8000",
    ]

    # Allow requests without origin/referer for direct API access (like Postman during development)
    # Comment out the following lines in production if you want strict enforcement
    if not origin and not referer:
        # For development/testing - you may want to remove this in production
        pass
    elif origin and origin not in allowed_origins:
        return JSONResponse(
            status_code=403, content={"detail": "Access forbidden: Invalid origin"}
        )
    elif referer and not any(
        referer.startswith(allowed) for allowed in allowed_origins
    ):
        return JSONResponse(
            status_code=403, content={"detail": "Access forbidden: Invalid referer"}
        )

    response = await call_next(request)
    return response


@app.get("/api/holidays")
async def get_holidays(year: int, timeframe: Optional[str] = None):
    """
    Get Indian holidays for a given year.
    
    Args:
        year: The year to get holidays for
        timeframe: Optional filter - 'week' for current week (Sun-Sat), 'month' for current month
    """
    indian_holidays = holidays.India(years=year)
    
    # Filter by timeframe if specified
    if timeframe:
        today = datetime.now().date()
        
        if timeframe.lower() == "week":
            # Get start of week (Sunday)
            # weekday() returns 0 for Monday, 6 for Sunday
            days_since_sunday = (today.weekday() + 1) % 7
            start_of_week = today - timedelta(days=days_since_sunday)
            # Get end of week (Saturday)
            end_of_week = start_of_week + timedelta(days=6)
            filtered_holidays = {
                date: name
                for date, name in indian_holidays.items()
                if start_of_week <= date <= end_of_week
            }
        elif timeframe.lower() == "month":
            # Get start of current month
            start_of_month = today.replace(day=1)
            # Get end of current month
            if today.month == 12:
                end_of_month = today.replace(day=31)
            else:
                end_of_month = (today.replace(month=today.month + 1, day=1) - timedelta(days=1))
            filtered_holidays = {
                date: name
                for date, name in indian_holidays.items()
                if start_of_month <= date <= end_of_month
            }
        else:
            # If invalid timeframe, return all holidays
            filtered_holidays = indian_holidays
    else:
        filtered_holidays = indian_holidays
    
    holidays_list = [
        {"date": str(date), "name": name}
        for date, name in sorted(filtered_holidays.items())
    ]
    
    return {
        "success": True,
        "year": year,
        "timeframe": timeframe,
        "total_holidays": len(holidays_list),
        "holidays": holidays_list,
    }

@app.get("/api/searchr")
async def search_links(query: str, max_results: int = 25, timelimit: str = "y"):
    """
    Search for links using DuckDuckGo and return all hrefs.
    """
    try:
        results = DDGS().text(
            query,
            region="wt-wt",
            safesearch="off",
            timelimit=timelimit,
            max_results=max_results,
        )

        # Extract only the hrefs
        links = [result["href"] for result in results]

        return {
            "success": True,
            "query": query,
            "total_results": len(links),
            "links": links,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """
    Health check endpoint to verify that the server is running.
    """
    return {"status": "ok", "message": "Server is running", "version": "2025.11.07"}


@app.get("/api/validate")
async def validate_api(
    summary: str,
    pp_scope: str,
    max_results: int,
    access_token: str,
    original_url: Optional[str] = None,
):
    validator = ValidateURLs(
        access_token=access_token,
        insight=summary,
        pp_scope=pp_scope,
        max_results=max_results,
    )

    validated_urls = validator.validate()

    # Remove original_url from the list if it's present and not None
    if original_url is not None and original_url in validated_urls:
        validated_urls.remove(original_url)

    return {"validated_urls": validated_urls, "validation_score": len(validated_urls)}


@app.post("/api/convert-to-pdf")
async def convert_to_pdf(file: UploadFile = File(...)):
    """
    Convert uploaded document (DOCX, etc.) to PDF using LibreOffice.
    Returns the path to the generated PDF file.
    """
    try:
        # Create output folder if it doesn't exist
        os.makedirs("output_folder", exist_ok=True)
        
        # Save uploaded file temporarily
        temp_file_path = f"output_folder/{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # Convert to PDF using LibreOffice
        result = subprocess.run([
            'libreoffice',
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', 'output_folder',
            temp_file_path
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Conversion failed: {result.stderr}")
        
        # Get the PDF filename
        pdf_filename = os.path.splitext(file.filename)[0] + ".pdf"
        pdf_path = f"output_folder/{pdf_filename}"
        
        if not os.path.exists(pdf_path):
            raise Exception(f"PDF file not created at {pdf_path}")
        
        return {
            "success": True,
            "message": "File converted to PDF successfully",
            "pdf_filename": pdf_filename,
            "pdf_path": pdf_path,
            "original_filename": file.filename
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from ddgs import DDGS

app = FastAPI(
    title="Lead Management API",
    description="FastAPI server for lead management with restricted access",
    version="1.0.0"
)

# Configure CORS to allow only https://n8n.sesai.in
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://n8n.sesai.in", "http://127.0.0.1:8000"],
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
    
    allowed_origins = ["https://n8n.sesai.in", "http://127.0.0.1:8000"]
    
    # Allow requests without origin/referer for direct API access (like Postman during development)
    # Comment out the following lines in production if you want strict enforcement
    if not origin and not referer:
        # For development/testing - you may want to remove this in production
        pass
    elif origin and origin not in allowed_origins:
        return JSONResponse(
            status_code=403,
            content={"detail": "Access forbidden: Invalid origin"}
        )
    elif referer and not any(referer.startswith(allowed) for allowed in allowed_origins):
        return JSONResponse(
            status_code=403,
            content={"detail": "Access forbidden: Invalid referer"}
        )
    
    response = await call_next(request)
    return response


@app.get("/api/search")
async def search_links(query: str, max_results: int = 25, timelimit: str = 'y'):
    """
    Search for links using DuckDuckGo and return all hrefs.
    """
    try:
        results = DDGS().text(
            query,
            region='wt-wt',
            safesearch='off',
            timelimit=timelimit,
            max_results=max_results
        )
        
        # Extract only the hrefs
        links = [result['href'] for result in results]
        
        return {
            "success": True,
            "query": query,
            "total_results": len(links),
            "links": links
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import FastAPI, Request, HTTPException
from scraper import scrape_google_maps
import os

app = FastAPI(
    title="Google Maps Scraper API",
    description="An API to scrape Google Maps for public business data.",
    version="1.0.0"
)

# Get the RapidAPI proxy secret from environment variables
RAPIDAPI_PROXY_SECRET = os.environ.get("RAPIDAPI_PROXY_SECRET")

@app.middleware("http")
async def verify_rapidapi_secret(request: Request, call_next):
    # If the RAPIDAPI_PROXY_SECRET is not set, we can assume it's a development environment
    # and skip the verification. In a production environment, this secret should be set.
    if RAPIDAPI_PROXY_SECRET:
        # The header name is 'x-rapidapi-proxy-secret'
        rapidapi_secret = request.headers.get("x-rapidapi-proxy-secret")
        if not rapidapi_secret or rapidapi_secret != RAPIDAPI_PROXY_SECRET:
            raise HTTPException(status_code=403, detail="Invalid RapidAPI secret")
    
    response = await call_next(request)
    return response

@app.get("/search")
async def search_places(q: str, max_results: int = 10, reviews_count: int = 0):
    """
    Searches for places on Google Maps.

    - **q**: The search query (e.g., "ramen in san francisco").
    - **max_results**: The maximum number of results to return.
    - **reviews_count**: The minimum number of reviews for a place to be included in the results.
    """
    if not q:
        return {"error": "Search query 'q' is required."}
    
    results = await scrape_google_maps(q, max_results, reviews_count)
    return {"query": q, "results": results}
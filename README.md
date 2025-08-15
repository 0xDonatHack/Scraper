# Google Maps Scraper

This project is a FastAPI application that scrapes Google Maps for public business data. It provides an API endpoint to search for places and returns the results in JSON format. The scraper is built using Playwright and BeautifulSoup, and it runs in parallel to speed up the data extraction process.

## Features

- Scrape business name, address, phone number, rating, and website.
- API endpoint to search for places.
- Parallel scraping for faster results.
- Saves results to a JSON file (`scraped_data.json`) and an SQLite database (`scraper_results.db`).
- Dockerized for easy setup and deployment.

## Setup and Running the Project

### Using Docker (Recommended)

1.  **Build the Docker image:**
    ```bash
    docker build -t google-maps-scraper .
    ```

2.  **Run the Docker container:**
    ```bash
    docker run -p 8000:8000 -v $(pwd):/app google-maps-scraper
    ```
    This will start the FastAPI server on `http://localhost:8000`. The `-v $(pwd):/app` command mounts the current directory into the container, so the database and JSON file will be saved on your host machine.

### Running Locally

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Install Playwright browsers:**
    ```bash
    playwright install --with-deps
    ```

3.  **Run the scraper from the command line:**
    ```bash
    python scraper.py "your search query" [max_results]
    ```
    Example:
    ```bash
    python scraper.py "ramen in san francisco" 15
    ```

4.  **Run the API server:**
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000
    ```
    The API will be available at `http://localhost:8000`.

## API Usage

### `/search`

Searches for places on Google Maps.

- **Method:** `GET`
- **Query Parameters:**
    - `q` (string, **required**): The search term (e.g., "pizza in new york").
    - `max_results` (integer, optional, default: 10): The maximum number of results to return.

- **Example Request:**
    ```bash
    curl "http://localhost:8000/search?q=ramen%20in%20san%20francisco&max_results=5"
    ```

- **Example Response:**
    ```json
    {
      "query": "ramen in san francisco",
      "results": [
        {
          "name": "Marufuku Ramen",
          "rating": 4.6,
          "address": "1581 Webster St #235, San Francisco, CA 94115",
          "website": "https://marufukuramen.com/",
          "phone_number": "+1 415-872-9786",
          "email": "N/A"
        }
      ]
    }
    ```

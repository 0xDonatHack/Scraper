
import asyncio
import json
import os
import sys
import sqlite3
import getpass
import re
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import asyncio

async def scrape_google_maps(search_query: str, max_results: int = 10, reviews_count: int = 0):
    """
    Scrapes Google Maps for a given search query and returns a list of places.
    """
    print(f"Starting scrape for '{search_query}'...")
    places = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            # Get process ID and username
            process_id = os.getpid()
            username = getpass.getuser()
            # Go to Google Maps
            await page.goto("https://www.google.com/maps", timeout=60000)

            # Search for the query
            await page.locator("#searchboxinput").fill(search_query)
            await page.keyboard.press("Enter")

            # Wait for results to load
            await page.wait_for_selector('[role="feed"]', timeout=15000)
            print("Results loaded. Parsing links..")
            

            # Scroll to load more results
            for _ in range(10): # Scroll 5 times
                await page.mouse.wheel(0, 10000)
                await asyncio.sleep(2)

            # Get all links from the results feed
            html_content = await page.inner_html('[role="feed"]')
            soup = BeautifulSoup(html_content, "html.parser")
            links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].startswith('https://www.google.com/maps/place/')]
            unique_links = list(set(links))
            print(f"Found {len(unique_links)} unique places.")

            # Visit each link and extract data
            tasks = []
            for i, link in enumerate(unique_links):
                if i >= max_results:
                    break
                tasks.append(scrape_place(browser, link, i + 1, len(unique_links)))

            scraped_places = await asyncio.gather(*tasks)

            # Filter out empty results and places with fewer reviews than specified
            places = [p for p in scraped_places if p and p.get('reviews_count', 0) >= reviews_count]

        except Exception as e:
            print(f"An error occurred: {e}")

        finally:
            await browser.close()
        return places


async def scrape_place(browser, link, index, total):
    print(f"Scraping place {index}/{total}: {link}")
    page = await browser.new_page()
    try:
        await page.goto(link, timeout=60000)
        await page.wait_for_selector('h1', timeout=10000)  # Wait for the name to load

        # Extract content after the page has loaded
        page_content = await page.content()
        details_soup = BeautifulSoup(page_content, "html.parser")

        place_data = {}

        # Extract Name
        name_element = details_soup.find('h1')
        place_data['name'] = name_element.text.strip() if name_element else 'N/A'

        # Extract Rating and Reviews Count
        try:
            rating_text = details_soup.select_one('div.F7nice').text
            rating_match = re.search(r'([\d\.]+)', rating_text)
            reviews_match = re.search(r'\(([\d,]+)\)', rating_text)
            
            if rating_match:
                place_data['rating'] = float(rating_match.group(1))
            else:
                place_data['rating'] = 'N/A'
            
            if reviews_match:
                place_data['reviews_count'] = int(reviews_match.group(1).replace(',', ''))
            else:
                place_data['reviews_count'] = 0
        except (AttributeError, ValueError):
            place_data['rating'] = 'N/A'
            place_data['reviews_count'] = 0

        # Extract other details using data-item-id
        address_element = details_soup.find(attrs={'data-item-id': 'address'})
        website_element = details_soup.find(attrs={'data-item-id': 'authority'})
        phone_element = details_soup.find(attrs={'data-item-id': lambda x: x and x.startswith('phone')})

        place_data['address'] = address_element.text.strip().replace('', '').strip() if address_element else 'N/A'
        place_data['website'] = website_element['href'] if website_element else 'N/A'
        place_data['phone_number'] = phone_element.text.strip().replace('', '').strip() if phone_element else 'N/A'
        place_data['email'] = 'N/A'  # Email is not available on Google Maps
        return place_data

    except Exception as e:
        print(f"Error scraping {link}: {e}")
        return {}
    finally:
        await page.close()

async def main():
    # Database setup
    conn = sqlite3.connect('scraper_results.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            process_id INTEGER,
            user TEXT,
            search_query TEXT,
            data TEXT
        )
    ''')
    conn.commit()

    if len(sys.argv) < 2:
        print("Usage: python scraper.py \"search query\" [max_results]")
        sys.exit(1)

    search_query = sys.argv[1]
    max_results = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    try:
        scraped_data = await scrape_google_maps(search_query, max_results)

        # Get process ID and username
        process_id = os.getpid()
        username = getpass.getuser()

        # Store results in the database
        json_data = json.dumps(scraped_data, indent=2, ensure_ascii=False)
        cursor.execute("INSERT INTO results (process_id, user, search_query, data) VALUES (?, ?, ?, ?)",
                       (process_id, username, search_query, json_data))
        conn.commit()

        print("Data saved to database.")

        # Save results to JSON file
        with open('scraped_data.json', 'w', encoding='utf-8') as f:
            json.dump(scraped_data, f, indent=2, ensure_ascii=False)

        print("Data saved to scraped_data.json")
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(main())

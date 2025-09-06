# app.py
# This is the code for your web crawler.
# It uses the Flask framework to create a simple web server.
# Save this file as 'app.py'.

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Initialize the Flask application
app = Flask(__name__)
# Enable CORS to allow your frontend to call this service
CORS(app) 

# --- Helper: Standard way to get soup object ---
def get_soup(url):
    """Fetches a URL and returns a BeautifulSoup object."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return BeautifulSoup(response.content, 'html.parser')

# --- NEW: Endpoint to fetch Table of Contents ---
@app.route('/table-of-contents', methods=['POST'])
def fetch_toc():
    """
    This function handles fetching the table of contents from a novel's main page.
    """
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"error": "A 'url' key is required."}), 400

    url = data['url']
    if "kakuyomu.jp/works/" not in url:
        return jsonify({"error": "Invalid URL. Only kakuyomu.jp novel URLs are supported."}), 400

    try:
        soup = get_soup(url)

        # --- Extract Novel Title ---
        novel_title_element = soup.select_one('#workTitle')
        novel_title = novel_title_element.get_text(strip=True) if novel_title_element else "Unknown Novel Title"
        
        # --- Extract Chapters ---
        chapters = []
        # This selector targets the list of episodes in the table of contents.
        chapter_links = soup.select('.widget-toc-episode-episodeTitle a')

        if not chapter_links:
             return jsonify({"error": "Could not find a chapter list. The page structure may have changed."}), 500

        for link in chapter_links:
            chapter_title = link.get_text(strip=True)
            # The 'href' attribute might be a relative URL, so we join it with the base URL.
            chapter_url = urljoin(url, link['href'])
            chapters.append({"title": chapter_title, "url": chapter_url})

        # Prepare the successful response
        toc_data = {
            "novelTitle": novel_title,
            "chapters": chapters
        }
        return jsonify(toc_data), 200

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to fetch the URL: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


# --- Existing endpoint for crawling a single chapter ---
@app.route('/crawl', methods=['POST'])
def crawl_novel():
    """
    This function is the main endpoint for crawling a single chapter.
    It receives a URL, fetches the content, parses it, and returns the data.
    """
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"error": "A 'url' key in a JSON body is required."}), 400

    url = data['url']
    if "kakuyomu.jp/works/" not in url:
        return jsonify({"error": "Invalid URL. Only kakuyomu.jp chapter URLs are supported."}), 400

    try:
        soup = get_soup(url)

        # --- Extract Data ---
        novel_title_element = soup.select_one('#workColorHeader a')
        novel_title = novel_title_element.get_text(strip=True) if novel_title_element else "Unknown Novel Title"

        chapter_title_element = soup.select_one('.widget-episodeTitle')
        chapter_title = chapter_title_element.get_text(strip=True) if chapter_title_element else "Unknown Chapter Title"

        content_body = soup.select_one('.widget-episodeBody')
        paragraphs = content_body.find_all('p') if content_body else []
        content = "\n\n".join(p.get_text(strip=True) for p in paragraphs)

        if not content:
            return jsonify({"error": "Could not find chapter content. The page structure may have changed."}), 500

        # Prepare the successful response
        crawled_data = {
            "novelTitle": novel_title,
            "chapterTitle": chapter_title,
            "content": content
        }
        
        return jsonify(crawled_data), 200

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to fetch the URL: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

# This part allows you to run the server locally for testing
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

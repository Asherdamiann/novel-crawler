# app.py
# This is the code for your web crawler.
# It uses the Flask framework to create a simple web server.
# Save this file as 'app.py'.

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

# Initialize the Flask application
app = Flask(__name__)
# Enable CORS to allow your frontend to call this service
CORS(app) 

# Define a route '/crawl' that accepts POST requests
@app.route('/crawl', methods=['POST'])
def crawl_novel():
    """
    This function is the main endpoint for the crawler.
    It receives a URL, fetches the content, parses it, and returns the data.
    """
    # Get the JSON data from the request body
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"error": "A 'url' key in a JSON body is required."}), 400

    url = data['url']
    # Simple validation to ensure it's a kakuyomu URL
    if "kakuyomu.jp/works/" not in url:
        return jsonify({"error": "Invalid URL. Only kakuyomu.jp chapter URLs are supported."}), 400

    try:
        # Fetch the webpage content with a timeout
        response = requests.get(url, timeout=15)
        response.raise_for_status()  # Raise an error for bad responses (like 404)

        # Parse the HTML with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # --- Extract Data ---
        # *** FIX: Updated the selector for the novel title to match the current website layout. ***
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

# This part allows you to run the server locally for testing if needed
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import os
import re
import logging
import time
import argparse
from flask import Flask, request, jsonify, send_file

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache ChromeDriverManager installation
CHROMEDRIVER_PATH = ChromeDriverManager().install()

app = Flask(__name__)

def get_safe_filename(url, suffix=""):
    """Generate a safe filename from the URL."""
    filename = re.sub(r'[^\w\-_\. ]', '_', url)
    if suffix:
        filename += f"_{suffix}"
    return filename

def take_screenshots(driver, url, output_dir, prefix="", file_type="png"):
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Ensure the zoom level is set to 100%
        driver.execute_script("document.body.style.zoom='100%'")
        
        # Get the dimensions of the viewport
        viewport_height = driver.execute_script("return window.innerHeight")
        
        # Get the total height of the page
        total_height = driver.execute_script("return document.documentElement.scrollHeight")
        
        # Initialize the scroll position
        scroll_position = 0
        screenshot_index = 1

        # Scroll and take screenshots
        while scroll_position < total_height:
            # Generate the output path
            output_path = os.path.join(output_dir, f"{get_safe_filename(url, prefix)}_part_{screenshot_index}.{file_type}")
            
            # Take the screenshot
            driver.save_screenshot(output_path)
            logger.info(f"Screenshot saved: {output_path} | URL: {url}")
            
            # Scroll down
            scroll_position += viewport_height
            driver.execute_script(f"window.scrollTo(0, {scroll_position})")
            time.sleep(2)  # Let the page load
            
            screenshot_index += 1
    except Exception as e:
        logger.error(f"Failed to take screenshots of {url}: {e}")

def collect_links(driver):
    """Collect all unique links from the current page."""
    links = driver.find_elements(By.TAG_NAME, "a")
    urls = set()
    for link in links:
        href = link.get_attribute("href")
        if href and href.startswith("http"):
            urls.add(href)
    return urls

def main(url, output_dir, file_type="png"):
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Ensure GUI is off
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-gpu")

    # Initialize WebDriver
    webdriver_service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)

    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Initialize a set to keep track of visited URLs
    visited_urls = set()
    # Initialize a list with the starting URL
    to_visit = [url]

    while to_visit:
        current_url = to_visit.pop(0)
        if current_url in visited_urls:
            continue

        visited_urls.add(current_url)
        take_screenshots(driver, current_url, output_dir, file_type=file_type)

        driver.get(current_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Collect links from the current page
        new_links = collect_links(driver)
        to_visit.extend(new_links - visited_urls)

    driver.quit()

@app.route('/screenshot', methods=['POST'])
def screenshot():
    data = request.json
    url = data.get('url')
    output_dir = data.get('path', 'screenshots')
    file_type = data.get('type', 'png')

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    main(url, output_dir, file_type)
    return jsonify({'message': 'Screenshots taken successfully', 'path': output_dir})

@app.route('/files/<path:filename>', methods=['GET'])
def get_file(filename):
    return send_file(os.path.join('screenshots', filename))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Take screenshots of a webpage and its linked pages.')
    parser.add_argument('--url', type=str, help='The starting URL')
    parser.add_argument('--path', type=str, default='screenshots', help='The output directory path')
    parser.add_argument('--type', type=str, default='png', help='The screenshot file type (e.g., png, jpg)')

    args = parser.parse_args()

    if not args.url:
        args.url = input('Please enter the URL: ')
    if not args.path:
        args.path = input('Please enter the output directory path: ')
    if not args.type:
        args.type = input('Please enter the screenshot file type (e.g., png, jpg): ')

    main(args.url, args.path, args.type)

    app.run(host='0.0.0.0', port=5000)

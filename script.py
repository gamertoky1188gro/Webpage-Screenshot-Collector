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
from flask import Flask, request, jsonify, send_file, Response, stream_with_context, make_response
from collections import deque
from PIL import Image
from docx import Document
from urllib.parse import urljoin
from flask_cors import CORS
import json

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Cache ChromeDriverManager installation
CHROMEDRIVER_PATH = ChromeDriverManager().install()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

SUPPORTED_FILE_TYPES = ["webp", "jpg", "png", "pdf", "word"]

def get_safe_filename(url, suffix=""):
    """Generate a safe filename from the URL."""
    filename = re.sub(r'[^\w\-_\. ]', '_', url)
    if suffix:
        filename += f"_{suffix}"
    return filename

def take_screenshots(driver, url, temp_dir, prefix="", file_type="png"):
    screenshot_paths = []
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Ensure the zoom level is set to 100%
        driver.execute_script("document.body.style.zoom='100%'")
        
        # Handle dynamic elements like pop-ups or dropdowns
        popups = driver.find_elements(By.CLASS_NAME, "popup-class")
        for popup in popups:
            try:
                popup.click()
                logger.info("Closed a popup.")
            except:
                pass
        
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
            output_path = os.path.join(temp_dir, f"{get_safe_filename(url, prefix)}_part_{screenshot_index}.{file_type}")
            
            # Take the screenshot
            driver.save_screenshot(output_path)
            screenshot_paths.append(output_path)
            logger.info(f"Screenshot saved: {output_path} | URL: {url}")
            
            # Scroll down
            scroll_position += viewport_height
            driver.execute_script(f"window.scrollTo(0, {scroll_position})")
            time.sleep(2)  # Let the page load
            
            # Explicit wait for content to load
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            screenshot_index += 1
    except Exception as e:
        logger.error(f"Failed to take screenshots of {url}: {e}")
    return screenshot_paths

def collect_links(driver, base_url, debugging=False):
    """Collect all unique links from the current page."""
    links = driver.find_elements(By.TAG_NAME, "a")
    urls = set()
    for link in links:
        href = link.get_attribute("href")
        if href:
            if href.startswith("http"):
                urls.add(href)
                if debugging:
                    logger.debug(f"Captured URL: {href}")
            else:
                full_url = urljoin(base_url, href)
                urls.add(full_url)
                if debugging:
                    logger.debug(f"Captured URL: {full_url} (joined from {href})")
        else:
            if debugging:
                logger.debug(f"Skipped element with no href: {link.get_attribute('outerHTML')}")
    return urls

def collect_links_from_element(driver, base_url, element_by, element_value, debugging=False):
    """Collect all unique links from a specific element in the current page."""
    try:
        element = driver.find_element(element_by, element_value)
        links = element.find_elements(By.TAG_NAME, "a")
        urls = set()
        for link in links:
            href = link.get_attribute("href")
            if href:
                if href.startswith("http"):
                    urls.add(href)
                    if debugging:
                        logger.debug(f"Captured URL: {href}")
                else:
                    full_url = urljoin(base_url, href)
                    urls.add(full_url)
                    if debugging:
                        logger.debug(f"Captured URL: {full_url} (joined from {href})")
            else:
                if debugging:
                    logger.debug(f"Skipped link with no href: {link.get_attribute('outerHTML')}")
        return urls
    except Exception as e:
        if debugging:
            logger.error(f"Error while collecting links from element: {e}")
        return set()

def convert_images_to_pdf(image_paths, output_pdf_path):
    """Convert a list of images to a single PDF file."""
    images = [Image.open(image_path).convert("RGB") for image_path in image_paths]
    images[0].save(output_pdf_path, save_all=True, append_images=images[1:])
    logger.info(f"PDF saved: {output_pdf_path}")

def convert_images_to_word(image_paths, output_word_path):
    """Convert a list of images to a single Word document."""
    doc = Document()
    for image_path in image_paths:
        doc.add_picture(image_path)
    doc.save(output_word_path)
    logger.info(f"Word document saved: {output_word_path}")

def main(urls, output_dir, file_type="png", no_other_page_screenshot=False, no_ads=False, id_or_element=None, class_or_element=None, is_headless=True, debugging=False):
    # Ensure valid file type
    if file_type not in SUPPORTED_FILE_TYPES:
        logger.error(f"Unsupported file type: {file_type}. Supported file types are: {', '.join(SUPPORTED_FILE_TYPES)}")
        return

    # Setup Chrome options
    chrome_options = Options()
    if no_ads:
        chrome_options.add_extension('ublock.crx')  # Path to uBlock extension
    if is_headless:
        chrome_options.add_argument("--headless")  # Ensure GUI is off
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    # Initialize WebDriver
    webdriver_service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)

    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Create a temporary directory for storing PNG files if file_type is PDF or Word
    temp_dir = os.path.join(output_dir, "temp_screenshots")
    if file_type in ["pdf", "word"] and not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # Initialize a set to keep track of visited URLs
    visited_urls = set()
    # Initialize a deque with the starting URLs
    to_visit = deque(urls)

    while to_visit:
        current_url = to_visit.popleft()
        if current_url in visited_urls:
            if debugging:
                logger.debug(f"Skipping already visited URL: {current_url}")
            continue

        visited_urls.add(current_url)
        if debugging:
            logger.debug(f"Visiting URL: {current_url}")
        screenshot_paths = take_screenshots(driver, current_url, temp_dir if file_type in ["pdf", "word"] else output_dir, file_type="png")
        yield screenshot_paths

        if no_other_page_screenshot:
            continue

        driver.get(current_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Collect links from the current page
        new_links = collect_links(driver, current_url, debugging=debugging)
        to_visit.extend(new_links - visited_urls)

        # Collect links from the specified element if provided
        if id_or_element:
            element_tag, element_id = id_or_element
            new_links_from_element = collect_links_from_element(driver, current_url, By.ID, element_id, debugging=debugging)
            if debugging:
                logger.debug(f"New links found in element {element_tag} with id {element_id}: {new_links_from_element}")
            to_visit.extend(new_links_from_element - visited_urls)
        
        if class_or_element:
            for item in class_or_element:
                element_tag, class_value = item if isinstance(item, tuple) else (None, item)
                if element_tag:
                    new_links_from_element = collect_links_from_element(driver, current_url, By.CLASS_NAME, class_value, debugging=debugging)
                    if debugging:
                        logger.debug(f"New links found in element {element_tag} with class {class_value}: {new_links_from_element}")
                    to_visit.extend(new_links_from_element - visited_urls)

    driver.quit()

    # Convert PNGs to a single PDF or Word document if file_type is PDF or Word
    if file_type == "pdf":
        pdf_path = os.path.join(output_dir, f"{get_safe_filename(urls[0])}.pdf")
        convert_images_to_pdf(screenshot_paths, pdf_path)
        for path in screenshot_paths:
            os.remove(path)  # Clean up temporary PNG files
        os.rmdir(temp_dir)  # Remove the temporary directory
    elif file_type == "word":
        word_path = os.path.join(output_dir, f"{get_safe_filename(urls[0])}.docx")
        convert_images_to_word(screenshot_paths, word_path)
        for path in screenshot_paths:
            os.remove(path)  # Clean up temporary PNG files
        os.rmdir(temp_dir)  # Remove the temporary directory

# In-memory status tracking
screenshot_status = {}

@app.route('/screenshot', methods=['POST'])
def screenshot():
    data = request.json
    urls = data.get('urls', [])
    output_dir = data.get('path', 'screenshots')
    file_type = data.get('type', 'png')
    no_other_page_screenshot = data.get('no_other_page_screenshot', False)
    no_ads = data.get('no_ads', False)
    id_or_element = data.get('id_or_element', None)
    class_or_element = data.get('class_or_element', None)
    debugging = data.get('debugging', False)

    if not isinstance(urls, list) or not urls:
        return jsonify({'error': 'URLs are required'}), 400

    if file_type not in SUPPORTED_FILE_TYPES:
        return jsonify({'error': f"Unsupported file type: {file_type}. Supported file types are: {', '.join(SUPPORTED_FILE_TYPES)}"}), 400

    job_id = str(time.time())
    screenshot_status[job_id] = {'status': 'processing', 'message': 'Screenshots are being taken...'}

    def generate():
        yield f'data: {{"job_id": "{job_id}", "status": "processing", "message": "Screenshots are being taken..."}}\n\n'
        for screenshot_paths in main(urls, output_dir, file_type, no_other_page_screenshot, no_ads, id_or_element, class_or_element, debugging=debugging):
            for path in screenshot_paths:
                url_path = request.host_url + 'files/' + os.path.basename(path)
                yield f'data: {{"job_id": "{job_id}", "path": "{url_path}"}}\n\n'
        screenshot_status[job_id] = {'status': 'complete', 'message': 'All screenshots taken.'}
        yield f'data: {{"job_id": "{job_id}", "status": "complete", "message": "All screenshots taken."}}\n\n'

    response = make_response(Response(stream_with_context(generate()), content_type='text/event-stream'))
    response.headers['X-Job-Id'] = job_id
    return response

@app.route('/screenshot-stream/<job_id>', methods=['GET'])
def screenshot_stream(job_id):
    def generate():
        while True:
            if job_id in screenshot_status:
                status = screenshot_status[job_id]
                yield f'data: {json.dumps(status)}\n\n'
                if status['status'] == 'complete':
                    break
            else:
                yield f'data: {{"status": "not_found", "message": "Job ID not found"}}\n\n'
            time.sleep(1)

    response = Response(stream_with_context(generate()), content_type='text/event-stream')
    # Adding CORS headers to the EventSource response
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route('/files/<path:filename>', methods=['GET'])
def get_file(filename):
    return send_file(os.path.join('screenshots', filename))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Take screenshots of a webpage and its linked pages.')
    parser.add_argument('--urls', type=str, help='The starting URLs, separated by commas')
    parser.add_argument('--path', type=str, help='The output directory path')
    parser.add_argument('--type', type=str, help='The screenshot file type (e.g., png, jpg, webp, pdf, word)')
    parser.add_argument('--no-other-page-screenshot', '--nops', action='store_true', help='Only take the given URL screenshot')
    parser.add_argument('--no-ads', action='store_true', help='Use uBlock to block ads')
    parser.add_argument('--id-or-element', '--idoe', type=str, help='Get URLs of "a" tag/btns from the given id')
    parser.add_argument('--class-or-element', '--coe', type=str, help='Get URLs of "a" tag/btns from the given class')
    parser.add_argument('--element', type=str, help='Find all links from the given element')
    parser.add_argument('--id-and-element', '--idae', type=str, help='Find links from the given element and id as {element,id}')
    parser.add_argument('--class-and-element', '--cae', type=str, help='Find links from the given element and class as {element,class}')
    parser.add_argument('--head', action='store_true', help='Show browser window (disable headless mode)')
    parser.add_argument('--flask', action='store_true', help='Run the Flask server')
    parser.add_argument('--debugging', action='store_true', help='Enable debugging output')

    args = parser.parse_args()

    urls = args.urls.split(',') if args.urls else [input('Please enter the URL: ')]
    output_dir = args.path or "screenshots"
    file_type = args.type or "png"
    is_headless = not args.head
    debugging = args.debugging
    
    id_or_element = None
    if args.id_or_element:
        id_or_element = tuple(args.id_or_element.strip("{}").split(','))

    class_or_element = None
    if args.class_or_element:
        class_or_element = [tuple(item.split(',')) for item in args.class_or_element.split(';')]

    if args.flask:
        app.run(host='0.0.0.0', port=5000)
    else:
        for _ in main(urls, output_dir, file_type, args.no_other_page_screenshot, args.no_ads, id_or_element, class_or_element, is_headless, debugging=debugging):
            pass  # Run the generator to completion

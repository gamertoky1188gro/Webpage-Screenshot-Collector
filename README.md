# Webpage Screenshot Collector (v2)

This project is an advanced version (v2) of a web application that takes screenshots of a webpage and its linked pages. It uses Selenium with Chrome WebDriver to capture screenshots and Flask to provide a comprehensive API for taking screenshots and retrieving files. The project was created in under 45 minutes.

> **Note:** If you need to perform lightweight tasks, consider using v1.

## Features

- :camera: **Capture full-page screenshots** of a given URL.
- :repeat: **Automatically scrolls** and captures multiple screenshots if the page height exceeds the viewport height.
- :link: **Collects all unique links** from the current page and captures screenshots of those linked pages.
- :rocket: **Advanced Flask API** to request screenshots and retrieve files.
- :file_folder: **Generates safe filenames** for the screenshots based on the URL.
- :lock: **CORS enabled** for all routes.
- :scroll: **Handles dynamic elements** like pop-ups or dropdowns.
- :page_facing_up: **Supports multiple file types** including PNG, JPG, WEBP, PDF, and Word.
- :gear: **In-memory status tracking** for ongoing screenshot jobs.

## Requirements

- :snake: **Python 3.x**
- :globe_with_meridians: **Google Chrome browser**

## Installation

1. Clone the repository:
    ```sh
    git clone <repository-url>
    cd <repository-directory>
    ```

2. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

### Command Line Interface

You can run the script from the command line:

```sh
python script.py --urls <starting-urls> --path <output-directory> --type <file-type> [options]
```

### Example

```sh
python script.py --urls https://example.com --path screenshots --type png
```

### Flask API

1. Start the Flask server:
    ```sh
    python script.py --flask
    ```

2. Make a POST request to `/screenshot` with the URLs and optional path and type:
    ```sh
    curl -X POST http://127.0.0.1:5000/screenshot -H "Content-Type: application/json" -d '{"urls": ["https://example.com"], "path": "screenshots", "type": "png"}'
    ```

3. Retrieve a screenshot file:
    ```sh
    curl -O http://127.0.0.1:5000/files/<filename>
    ```

## Configuration Options

### Command Line Arguments

- `--urls`: The starting URLs for taking screenshots, separated by commas.
- `--path`: The directory to save the screenshots (default: `screenshots`).
- `--type`: The file type for the screenshots (default: `png`). Supported types: `webp`, `jpg`, `png`, `pdf`, `word`.
- `--no-other-page-screenshot`, `--nops`: Only take the given URL screenshot.
- `--no-ads`: Use uBlock to block ads.
- `--id-or-element`, `--idoe`: Get URLs of "a" tag/btns from the given id.
- `--class-or-element`, `--coe`: Get URLs of "a" tag/btns from the given class.
- `--element`: Find all links from the given element.
- `--id-and-element`, `--idae`: Find links from the given element and id as `{element,id}`.
- `--class-and-element`, `--cae`: Find links from the given element and class as `{element,class}`.
- `--head`: Show browser window (disable headless mode).
- `--flask`: Run the Flask server.
- `--debugging`: Enable debugging output.

### Example Request

Here is an example request to take screenshots of a webpage and its linked pages:

```sh
curl -X POST http://127.0.0.1:5000/screenshot -H "Content-Type: application/json" -d '{"urls": ["https://example.com"], "path": "screenshots", "type": "png"}'
```

## License

This project is licensed under the MIT License.

## Author

**Cyber Code Master**

## Acknowledgments

- [Selenium](https://www.selenium.dev/)
- [Flask](https://flask.palletsprojects.com/)
- [WebDriverManager](https://github.com/SergeyPirogov/webdriver_manager)

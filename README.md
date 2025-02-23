# Webpage Screenshot Collector

This project is a lightweight version (v1) of a web application that takes screenshots of a webpage and its linked pages. It uses Selenium with Chrome WebDriver to capture screenshots and Flask to provide a simple API for taking screenshots and retrieving files.

> **Note:** Use this version for lightweight tasks. If you need a more robust solution, consider using v2.

## Features

- :camera: **Capture full-page screenshots** of a given URL.
- :repeat: **Automatically scrolls** and captures multiple screenshots if the page height exceeds the viewport height.
- :link: **Collects all unique links** from the current page and captures screenshots of those linked pages.
- :rocket: **Simple Flask API** to request screenshots and retrieve files.
- :file_folder: **Generates safe filenames** for the screenshots based on the URL.

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
python script.py --url <starting-url> --path <output-directory> --type <file-type>
```

### Example

```sh
python script.py --url https://example.com --path screenshots --type png
```

### Flask API

1. Start the Flask server:
    ```sh
    python script.py
    ```

2. Make a POST request to `/screenshot` with the URL and optional path and type:
    ```sh
    curl -X POST http://127.0.0.1:5000/screenshot -H "Content-Type: application/json" -d '{"url": "https://example.com", "path": "screenshots", "type": "png"}'
    ```

3. Retrieve a screenshot file:
    ```sh
    curl -O http://127.0.0.1:5000/files/<filename>
    ```

## Configuration Options

- `--url`: The starting URL for taking screenshots.
- `--path`: The directory to save the screenshots (default: `screenshots`).
- `--type`: The file type for the screenshots (default: `png`).

## Example Request

Here is an example request to take screenshots of a webpage and its linked pages:

```sh
curl -X POST http://127.0.0.1:5000/screenshot -H "Content-Type: application/json" -d '{"url": "https://example.com", "path": "screenshots", "type": "png"}'
```

## License

This project is licensed under the MIT License.

## Author

**Cyber Code Master**

## Acknowledgments

- [Selenium](https://www.selenium.dev/)
- [Flask](https://flask.palletsprojects.com/)
- [WebDriverManager](https://github.com/SergeyPirogov/webdriver_manager)

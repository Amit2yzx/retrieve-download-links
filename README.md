# URL Analyzer and Download Link Extractor

An AI-powered application that analyzes URLs and extracts download links. Built with LangGraph for the agentic workflow and Puppeteer for web interactions.

## Features

- URL validation and analysis
- Extraction of download links from web pages
- Support for both static and dynamic (JavaScript-rendered) content
- Direct download link detection
- User-friendly web interface

## Requirements

- Python 3.8+
- Dependencies listed in requirements.txt

## Installation

1. Clone this repository
2. Create a virtual environment:
   ```
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```
   python run.py
   ```
2. Open your browser and navigate to `http://localhost:8000`
3. Enter a URL to analyze
4. View the analysis results and download links

## API Endpoints

- `GET /`: Main page with URL input form
- `POST /analyze`: API endpoint for URL analysis (JSON request/response)
- `POST /analyze-form`: Form submission endpoint (HTML response)

## How It Works

1. The user submits a URL through the web interface
2. The application validates the URL format
3. The LangGraph agent analyzes the URL using a multi-step process:
   - First, it attempts to fetch and analyze the URL using standard HTTP requests
   - If needed, it uses Puppeteer to handle JavaScript-rendered content
4. Download links are extracted using pattern matching and heuristics
5. The application recommends the best download link based on various factors
6. Results are presented to the user in a clean, user-friendly interface

## License

MIT

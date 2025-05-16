# URL Analyzer and Download Link Extractor (Streamlit Version)

An AI-powered application that analyzes URLs and extracts download links. Built with Streamlit for the web interface, and using Puppeteer for web interactions.

## Features

- URL validation and analysis
- Extraction of download links from web pages
- Support for both static and dynamic (JavaScript-rendered) content
- Direct download link detection
- User-friendly Streamlit interface

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

1. Run the Streamlit application:
   ```
   streamlit run streamlit_app.py
   ```
2. Open your browser and navigate to the URL shown in the terminal (typically http://localhost:8501)
3. Enter a URL to analyze
4. View the analysis results and download links

## How It Works

1. The user submits a URL through the Streamlit interface
2. The application validates the URL format
3. The application analyzes the URL using a multi-step process:
   - First, it attempts to fetch and analyze the URL using standard HTTP requests
   - If needed, it uses Puppeteer to handle JavaScript-rendered content
4. Download links are extracted using pattern matching and heuristics
5. The application recommends the best download link based on various factors
6. Results are presented to the user in a clean, user-friendly interface

## Deployment

This application can be easily deployed to Streamlit Cloud:

1. Push your code to GitHub
2. Sign in to [Streamlit Cloud](https://streamlit.io/cloud)
3. Create a new app and connect it to your GitHub repository
4. Select the `streamlit_app.py` file as the main file
5. Deploy the application

## License

MIT

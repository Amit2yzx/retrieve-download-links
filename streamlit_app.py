"""
Streamlit application for URL analyzer and download link extractor.
"""
import asyncio
import streamlit as st
from urllib.parse import urlparse
import re
import requests
from bs4 import BeautifulSoup
from pyppeteer import launch

# Set page configuration
st.set_page_config(
    page_title="URL Analyzer & Download Link Extractor",
    page_icon="🔗",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #4285F4;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #5F6368;
    }
    .success-box {
        background-color: #E6F4EA;
        padding: 20px;
        border-radius: 10px;
        border-left: 6px solid #34A853;
    }
    .info-box {
        background-color: #E8F0FE;
        padding: 20px;
        border-radius: 10px;
        border-left: 6px solid #4285F4;
    }
    .warning-box {
        background-color: #FCE8E6;
        padding: 20px;
        border-radius: 10px;
        border-left: 6px solid #EA4335;
    }
    .download-button {
        background-color: #34A853;
        color: white;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 5px;
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">URL Analyzer & Download Link Extractor</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Analyze URLs and extract download links using AI</p>', unsafe_allow_html=True)

# Functions from the original application
def extract_download_links(html_content: str, base_url: str):
    """Extract potential download links from HTML content."""
    soup = BeautifulSoup(html_content, "html.parser")
    download_links = []
    
    # Look for links with download attributes or keywords
    download_keywords = ['download', 'descargar', 'télécharger', 'herunterladen', 'скачать']
    file_extensions = ['.zip', '.pdf', '.exe', '.dmg', '.tar.gz', '.mp4', '.mp3', '.doc', '.docx', '.xls', '.xlsx']
    
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        text = a_tag.text.lower()
        
        # Check for download attribute
        if a_tag.get('download') is not None:
            download_links.append(href)
            continue
            
        # Check for download keywords in text or href
        if any(keyword in text or keyword in href.lower() for keyword in download_keywords):
            download_links.append(href)
            continue
            
        # Check for file extensions
        if any(href.lower().endswith(ext) for ext in file_extensions):
            download_links.append(href)
    
    # Convert relative URLs to absolute
    parsed_base = urlparse(base_url)
    base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"
    
    absolute_links = []
    for link in download_links:
        if link.startswith('http'):
            absolute_links.append(link)
        elif link.startswith('//'):
            absolute_links.append(f"{parsed_base.scheme}:{link}")
        elif link.startswith('/'):
            absolute_links.append(f"{base_domain}{link}")
        else:
            # Handle relative paths
            path = '/'.join(parsed_base.path.split('/')[:-1]) + '/'
            absolute_links.append(f"{base_domain}{path}{link}")
    
    return absolute_links

async def analyze_with_browser(url):
    """Analyze URL using Puppeteer for JavaScript-rendered content."""
    try:
        browser = await launch(headless=True)
        page = await browser.newPage()
        
        # Set user agent
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        # Navigate to the URL
        await page.goto(url, {'waitUntil': 'networkidle0', 'timeout': 30000})
        
        # Get page title
        title = await page.title()
        
        # Extract download links
        download_links = []
        
        # Look for download buttons and links
        elements = await page.querySelectorAll('a[href]')
        for element in elements:
            href = await page.evaluate('(element) => element.href', element)
            text = await page.evaluate('(element) => element.textContent', element)
            
            # Check for download keywords
            download_keywords = ['download', 'descargar', 'télécharger', 'herunterladen', 'скачать']
            file_extensions = ['.zip', '.pdf', '.exe', '.dmg', '.tar.gz', '.mp4', '.mp3', '.doc', '.docx', '.xls', '.xlsx']
            
            if (any(keyword in text.lower() for keyword in download_keywords) or 
                any(href.lower().endswith(ext) for ext in file_extensions)):
                download_links.append(href)
        
        await browser.close()
        
        return {
            "title": title,
            "download_links": download_links,
            "error": None
        }
        
    except Exception as e:
        return {
            "title": None,
            "download_links": [],
            "error": f"Error analyzing URL with browser: {str(e)}"
        }

def analyze_url(url):
    """Analyze a URL and extract basic information."""
    try:
        # Basic URL validation
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            return {
                "success": False,
                "error": "Invalid URL format",
                "is_direct_download": False,
                "download_links": [],
                "recommended_link": None,
                "title": None,
                "content_type": None,
            }

        # Fetch the URL content
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Basic analysis
        content_type = response.headers.get("Content-Type", "")
        is_html = "text/html" in content_type
        
        # Extract page title if HTML
        title = None
        if is_html:
            soup = BeautifulSoup(response.text, "html.parser")
            title_tag = soup.find("title")
            title = title_tag.text if title_tag else None
        
        # Check if this is a direct download link
        is_direct_download = False
        filename = None
        
        content_disposition = response.headers.get("Content-Disposition", "")
        if "attachment" in content_disposition:
            is_direct_download = True
            filename_match = re.search(r'filename="?([^"]+)"?', content_disposition)
            if filename_match:
                filename = filename_match.group(1)
        
        # Check file extension in URL
        file_extensions = ['.zip', '.pdf', '.exe', '.dmg', '.tar.gz', '.mp4', '.mp3', '.doc', '.docx', '.xls', '.xlsx']
        for ext in file_extensions:
            if url.lower().endswith(ext):
                is_direct_download = True
                filename = url.split('/')[-1]
                break
        
        # If it's HTML, try to extract download links
        download_links = []
        needs_browser = False
        if is_html:
            download_links = extract_download_links(response.text, url)
            
            # If no download links found with simple parsing, we might need browser
            if not download_links:
                needs_browser = True
        
        # Prepare result
        result = {
            "success": True,
            "url": url,
            "error": None,
            "is_direct_download": is_direct_download,
            "download_links": download_links,
            "recommended_link": None,
            "title": title,
            "content_type": content_type,
            "needs_browser": needs_browser,
            "filename": filename,
        }
        
        # If it's a direct download, use the original URL
        if is_direct_download:
            result["recommended_link"] = url
        # Otherwise, recommend the first download link if available
        elif download_links:
            result["recommended_link"] = download_links[0]
        
        return result
    
    except Exception as e:
        return {
            "success": False,
            "url": url,
            "error": f"Error analyzing URL: {str(e)}",
            "is_direct_download": False,
            "download_links": [],
            "recommended_link": None,
            "title": None,
            "content_type": None,
            "needs_browser": True,
        }

# URL input form
url = st.text_input("Enter URL to analyze", placeholder="https://example.com/download-page")

if st.button("Analyze URL"):
    if not url:
        st.error("Please enter a URL")
    else:
        with st.spinner("Analyzing URL..."):
            # First analysis
            result = analyze_url(url)
            
            # If needed, try with browser
            if result.get("needs_browser") and not result.get("recommended_link"):
                st.info("Using browser to analyze dynamic content...")
                browser_result = asyncio.run(analyze_with_browser(url))
                
                if browser_result.get("download_links"):
                    result["download_links"] = browser_result["download_links"]
                    result["recommended_link"] = browser_result["download_links"][0]
                
                if browser_result.get("title") and not result.get("title"):
                    result["title"] = browser_result["title"]
            
            # Display results
            if result["success"]:
                st.success("URL analyzed successfully!")
                
                if result.get("title"):
                    st.subheader(f"Page Title: {result['title']}")
                
                if result.get("content_type"):
                    st.text(f"Content Type: {result['content_type']}")
                
                if result["is_direct_download"]:
                    st.markdown(f"""
                    <div class="success-box">
                        <h3>Direct Download Link Detected!</h3>
                        <p>This URL points directly to a downloadable file.</p>
                        <a href="{result['recommended_link']}" class="download-button" target="_blank">Download Now</a>
                    </div>
                    """, unsafe_allow_html=True)
                elif result["recommended_link"]:
                    st.markdown(f"""
                    <div class="info-box">
                        <h3>Download Link Found!</h3>
                        <p>We found a download link on this page.</p>
                        <a href="{result['recommended_link']}" class="download-button" target="_blank">Download Now</a>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="warning-box">
                        <h3>No Download Links Found</h3>
                        <p>We couldn't find any download links on this page.</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Show all download links if there are multiple
                if len(result["download_links"]) > 1:
                    with st.expander("All Download Links Found"):
                        for i, link in enumerate(result["download_links"], 1):
                            st.markdown(f"{i}. [{link}]({link})")
            else:
                st.error(f"Error: {result['error']}")

# How it works section
with st.expander("How It Works"):
    st.markdown("""
    1. Enter a URL that contains or leads to downloadable content
    2. Our application analyzes the page using requests and BeautifulSoup
    3. If needed, Puppeteer is used to handle dynamic content
    4. Download links are extracted and the best one is recommended
    5. You get direct access to the download without navigating through ads or waiting
    """)

# Footer
st.markdown("---")
st.markdown("Powered by LangGraph and Puppeteer | [View on GitHub](https://github.com/Amit2yzx/retrieve-download-links)")

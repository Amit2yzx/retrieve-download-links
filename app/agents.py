"""
LangGraph agents for URL analysis and download link extraction.
"""
from typing import Dict, List, Optional, Any
import re
from urllib.parse import urlparse

from langgraph.graph import StateGraph, END, START

import requests
from bs4 import BeautifulSoup
from pyppeteer import launch


# Define the state
class AgentState(dict):
    """State for the URL analyzer agent."""
    url: str
    analysis: Optional[Dict[str, Any]] = None
    download_links: Optional[List[str]] = None
    error: Optional[str] = None
    needs_browser: bool = False
    final_result: Optional[Dict[str, Any]] = None


# Tools for the agent
async def analyze_url(state: AgentState) -> AgentState:
    """Analyze a URL and extract basic information."""
    url = state["url"]
    try:
        # Basic URL validation
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            state["error"] = "Invalid URL format"
            return state

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

        state["analysis"] = {
            "url": url,
            "title": title,
            "content_type": content_type,
            "is_html": is_html,
            "is_direct_download": is_direct_download,
            "filename": filename,
            "status_code": response.status_code,
            "size": len(response.content),
        }

        # If it's HTML, try to extract download links
        if is_html:
            download_links = extract_download_links(response.text, url)
            state["download_links"] = download_links

            # If no download links found with simple parsing, we might need browser
            if not download_links:
                state["needs_browser"] = True

        return state

    except Exception as e:
        state["error"] = f"Error analyzing URL: {str(e)}"
        state["needs_browser"] = True  # Try with browser as fallback
        return state


def extract_download_links(html_content: str, base_url: str) -> List[str]:
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


async def analyze_with_browser(state: AgentState) -> AgentState:
    """Analyze URL using Puppeteer for JavaScript-rendered content."""
    url = state["url"]
    try:
        browser = await launch(headless=True)
        page = await browser.newPage()

        # Set user agent
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

        # Navigate to the URL
        await page.goto(url, {'waitUntil': 'networkidle0', 'timeout': 30000})

        # Get page title
        title = await page.title()

        # Get HTML content and extract download links
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

        # Update state
        if not state.get("analysis"):
            state["analysis"] = {
                "url": url,
                "title": title,
                "is_html": True,
                "is_direct_download": False,
                "filename": None,
            }

        # Add or update download links
        if download_links:
            state["download_links"] = download_links

        return state

    except Exception as e:
        if not state.get("error"):
            state["error"] = f"Error analyzing URL with browser: {str(e)}"
        return state


def create_url_analyzer_agent():
    """Create the URL analyzer agent workflow."""
    # Create the graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("analyze_url", analyze_url)
    workflow.add_node("analyze_with_browser", analyze_with_browser)
    workflow.add_node("prepare_final_result", prepare_final_result)

    # Add START edge
    workflow.add_edge(START, "analyze_url")

    # Add conditional edges
    workflow.add_conditional_edges(
        "analyze_url",
        needs_browser_router
    )

    workflow.add_edge("analyze_with_browser", "prepare_final_result")
    workflow.add_edge("prepare_final_result", END)

    # Compile the graph
    return workflow.compile()


def needs_browser_router(state: AgentState):
    """Router to determine next node based on browser needs."""
    if state.get("needs_browser", False):
        return "analyze_with_browser"
    else:
        return "prepare_final_result"




def prepare_final_result(state: AgentState) -> AgentState:
    """Prepare the final result for the user."""
    analysis = state.get("analysis", {})
    download_links = state.get("download_links", [])
    error = state.get("error")

    result = {
        "success": error is None,
        "url": state.get("url"),
        "error": error,
        "is_direct_download": analysis.get("is_direct_download", False),
        "download_links": download_links,
        "recommended_link": None,
        "title": analysis.get("title"),
        "content_type": analysis.get("content_type"),
    }

    # If it's a direct download, use the original URL
    if analysis.get("is_direct_download"):
        result["recommended_link"] = state.get("url")
    # Otherwise, recommend the first download link if available
    elif download_links:
        result["recommended_link"] = download_links[0]

    state["final_result"] = result
    return state


# Create the agent
url_analyzer_agent = create_url_analyzer_agent()

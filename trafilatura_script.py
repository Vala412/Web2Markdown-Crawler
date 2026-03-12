import requests
import trafilatura
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import time

BASE_URL = "https://www.vivanshinfotech.com/"
OUTPUT_DIR = "markdown_pages"

visited = set()
queue = [BASE_URL]

os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_page_links(url):
    """Extract internal links from a webpage"""
    links = []

    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup.find_all("a", href=True):
            href = tag["href"]
            full_url = urljoin(BASE_URL, href)

            if urlparse(full_url).netloc == urlparse(BASE_URL).netloc:
                links.append(full_url)

    except Exception as e:
        print("Error extracting links:", e)

    return links


def extract_markdown(url):
    """Extract markdown content using trafilatura"""
    try:
        downloaded = trafilatura.fetch_url(url)

        if not downloaded:
            return None

        markdown = trafilatura.extract(
            downloaded,
            output_format="markdown",
            include_links=True,
            include_images=False
        )

        return markdown

    except Exception as e:
        print("Extraction error:", e)
        return None


def save_markdown(url, content):
    """Save markdown file"""
    parsed = urlparse(url)

    filename = parsed.path.strip("/")

    if not filename:
        filename = "home"

    filename = filename.replace("/", "_")

    path = os.path.join(OUTPUT_DIR, f"{filename}.md")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


while queue:

    url = queue.pop(0)

    if url in visited:
        continue

    print("Crawling:", url)

    visited.add(url)

    markdown = extract_markdown(url)

    if markdown:
        save_markdown(url, markdown)

    links = get_page_links(url)

    for link in links:
        if link not in visited:
            queue.append(link)

    time.sleep(1)

print("Crawling finished.")
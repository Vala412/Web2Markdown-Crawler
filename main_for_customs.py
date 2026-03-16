import os
import time
import logging
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
import requests

# Configure custom logger to match the specified layout
class CustomFormatter(logging.Formatter):
    def format(self, record):
        return f"{record.levelname} | {record.getMessage()}"

logger = logging.getLogger("Crawler")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(CustomFormatter())
logger.addHandler(ch)

class RAGCrawler:
    def __init__(self, start_url, output_dir="documents"):
        self.start_url = start_url
        self.output_dir = output_dir
        self.domain = urlparse(start_url).netloc
        
        # Queue-based attributes
        self.visited = set()
        self.queue = [start_url]
        
        # Track if header/footer have been saved
        self.header_saved = False
        self.footer_saved = False
        self.downloaded_files = set()
        
        # Setup Selenium WebDriver (Visible Chrome Browser)
        options = webdriver.ChromeOptions()
        self.driver = webdriver.Chrome(options=options)
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

    def remove_elements(self, soup):
        """Removes unwanted elements from the soup based on generic CSS selectors."""
        unwanted_selectors = ['.mobileNav','#chatbot-container']
        for selector in unwanted_selectors:
            for el in soup.select(selector):
                el.decompose()
        return soup

    def extract_header_footer(self, soup):
        """Extracts and saves header and footer exactly once, cleaning them from the page."""
        header = soup.find('header')
        if header:
            if not self.header_saved:
                header_md = md(str(header), heading_style="ATX")
                with open(os.path.join(self.output_dir, '_header.md'), 'w', encoding='utf-8') as f:
                    f.write(header_md)
                self.header_saved = True
                logger.info("Saved _header.md")
            header.decompose()

        footer = soup.find('footer')
        if footer:
            if not self.footer_saved:
                footer_md = md(str(footer), heading_style="ATX")
                with open(os.path.join(self.output_dir, '_footer.md'), 'w', encoding='utf-8') as f:
                    f.write(footer_md)
                self.footer_saved = True
                logger.info("Saved _footer.md")
            footer.decompose()

    def get_main_content(self, soup):
        """Finds the main content container using ordered CSS selectors fallback to <body>."""
        selectors = ['main', 'article', '.content', '.page-content', '.entry-content', '#content']
        for selector in selectors:
            content = soup.select_one(selector)
            if content:
                logger.info(f"Using content selector: {selector}")
                return content
        
        logger.info("Using content selector: body (fallback)")
        return soup.find('body')

    def extract_downloads(self, content_soup):
        """Extracts specific file extension links from the content and downloads them."""
        extensions = {'.pdf', '.xlsx', '.docx', '.pptx', '.csv'}
        downloads = []
        for a in content_soup.find_all('a', href=True):
            href = a['href']
            parsed_href = urlparse(href)
            
            if any(parsed_href.path.lower().endswith(ext) for ext in extensions):
                file_name = a.get_text(strip=True) or parsed_href.path.split('/')[-1]
                full_url = urljoin(self.driver.current_url, href)
                
                # Create the 'document' folder
                download_dir = os.path.join(self.output_dir, "document")
                os.makedirs(download_dir, exist_ok=True)
                
                # Clean up filename
                safe_filename = os.path.basename(urldefrag(parsed_href.path)[0])
                if not safe_filename:
                    safe_filename = f"file_{int(time.time())}.{ext.strip('.')}"
                    
                filepath = os.path.join(download_dir, safe_filename)
                
                # Download if not already downloaded
                if full_url not in self.downloaded_files:
                    try:
                        headers = {'User-Agent': 'Mozilla/5.0'}
                        response = requests.get(full_url, headers=headers, stream=True, timeout=15)
                        if response.status_code == 200:
                            with open(filepath, 'wb') as f:
                                for chunk in response.iter_content(1024):
                                    f.write(chunk)
                            logger.info(f"Downloaded document: {safe_filename}")
                            self.downloaded_files.add(full_url)
                        else:
                            logger.error(f"Download failed for {full_url} with status {response.status_code}")
                    except Exception as e:
                        logger.error(f"Failed to download {full_url}: {e}")
                
                # Local relative path for markdown
                rel_path = f"document/{safe_filename}"
                downloads.append(f"- [{file_name}]({rel_path})")
                
        return downloads

    def get_slug(self, url):
        """Generates a filename slug from the URL."""
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        if not path or path == 'index.html' or path == 'index.php':
            return 'home'
        # e.g., about-us/team -> about-us-team
        return path.replace('/', '-')

    def extract_page(self, url, page_num=1):
        """Extracts content from the current DOM, formats as MD, and saves it. Returns generated MD."""
        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        
        # Clean HTML
        self.extract_header_footer(soup)
        self.remove_elements(soup)
        
        content = self.get_main_content(soup)
        if not content:
            return None
        
        # Scrape downloadable links before converting to markdown
        downloads = self.extract_downloads(content)
        
        # Convert HTML to MD
        content_md = md(str(content), heading_style="ATX").strip()
        
        # Append downloads
        if downloads:
            content_md += "\n\n## Downloads\n\n" + "\n".join(downloads)
        
        slug = self.get_slug(url)
        filename = f"{slug}.md" if page_num == 1 else f"{slug}_page{page_num}.md"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content_md)
            
        logger.info(f"Saved {filename}")
        return content_md

    def handle_pagination(self, url):
        """Handles pagination using Selenium click events."""
        page_num = 1
        logger.info(f"Extracting page {page_num}")
        last_md = self.extract_page(url, page_num)
        
        while True:
            try:
                # Commonly used Next button selectors
                next_selectors = '.pagination .next, a.next, button.next, [aria-label="Next"], [rel="next"]'
                next_buttons = self.driver.find_elements(By.CSS_SELECTOR, next_selectors)
                
                if not next_buttons:
                    break
                    
                # Pick the first visible matching element
                next_btn = None
                for btn in next_buttons:
                    if btn.is_displayed():
                        btn_text = btn.text.strip()
                        btn_cls = btn.get_attribute('class') or ""
                        if '…' in btn_text or '...' in btn_text or 'skip' in btn_cls.lower():
                            continue
                        next_btn = btn
                        break
                        
                if not next_btn:
                    break

                # Check if it's disabled via class or disabled attribute
                btn_class = next_btn.get_attribute('class') or ""
                if 'disabled' in btn_class.lower() or next_btn.get_attribute('disabled'):
                    break

                logger.info("Clicking next page")
                # Using Javascript click as a fallback to avoid intercepted clicks
                self.driver.execute_script("arguments[0].click();", next_btn)
                time.sleep(3)  # Wait for rendering
                
                page_num += 1
                logger.info(f"Extracting page {page_num}")
                current_md = self.extract_page(url, page_num)
                
                if current_md is None or current_md == last_md:
                    logger.info("Page content did not change, stopping pagination.")
                    # remove the duplicate file
                    filename = f"{self.get_slug(url)}_page{page_num}.md"
                    filepath = os.path.join(self.output_dir, filename)
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    break
                
                last_md = current_md
                
            except WebDriverException as e:
                # Typically means element not interactable or removed
                break
            except Exception as e:
                logger.error(f"Pagination error: {str(e)}")
                break

        if page_num > 1:
            logger.info("Pagination finished")

    def extract_links(self):
        """Extracts and filters internal links to process further."""
        soup = BeautifulSoup(self.driver.page_source, 'lxml')
        for a in soup.find_all('a', href=True):
            href = a['href']
            
            # Remove fragment/hash from URL
            href, _ = urldefrag(href)
            full_url = urljoin(self.driver.current_url, href)
            parsed_full = urlparse(full_url)
            
            # Check if internal link
            if parsed_full.netloc == self.domain:
                # Ignore query parameters with pagination e.g., ?page=1
                queries = parsed_full.query.split('&')
                is_pagination_link = any(q.startswith('page=') or q.startswith('p=') for q in queries)
                
                if not is_pagination_link:
                    if full_url not in self.visited and full_url not in self.queue:
                        self.queue.append(full_url)

    def crawl(self):
        """Main queue-based crawling execution loop."""
        try:
            while self.queue:
                url = self.queue.pop(0)
                
                if url in self.visited:
                    continue
                
                logger.info(f"Crawling {url}")
                try:
                    self.driver.get(url)
                    time.sleep(3)  # Render delay
                    
                    self.extract_links()
                    self.handle_pagination(url)
                    
                    self.visited.add(url)
                except Exception as e:
                    logger.error(f"Error crawling {url}: {str(e)}")
                    # Continue crawling even if one page fails
        finally:
            self.driver.quit()

if __name__ == "__main__":
    # Insert start URL here to run
    START_URL = "https://mumbaicustomszone3.gov.in/"
    crawler = RAGCrawler(start_url=START_URL, output_dir="day5_output_test")
    crawler.crawl()

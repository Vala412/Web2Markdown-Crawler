# Web2Markdown Crawler

This is a Python-based web scraping tool that converts website content to clean Markdown files using the Trafilatura library. It crawls specified websites and extracts articles/pages into organized Markdown format.

## Features
- Scrapes full web pages or specific sections into Markdown.
- Uses Trafilatura for high-quality content extraction (removes ads, navigation, etc.).
- Outputs to structured folders like `md/` and `markdown_pages/`.
- Handles multiple pages/case studies/services from sites like vivanshinfotech.com.

## File Structure
```
Scraping/
├── main.py                 # Main entrypoint script
├── trafilatura_script.py   # Core scraping logic with Trafilatura
├── md/                     # Markdown files (general scraped content)
│   ├── home.md
│   ├── about-us.md
│   └── ... (other pages)
└── markdown_pages/         # Organized by page type (e.g., case-studies, services)
    ├── home.md
    ├── services_web-development.md
    └── ...
```

## Prerequisites
- Python 3.8+
- Git (for this repo)

## Installation
1. Clone the repo:
   ```
   git clone git@github.com:Vala412/Web2Markdown-Crawler.git
   cd Web2Markdown-Crawler
   ```
2. Install dependencies:
   ```
   pip install trafilatura requests beautifulsoup4
   ```

## Usage
1. Edit `main.py` or `trafilatura_script.py` to set target URLs.
2. Run the scraper:
   ```
   python main.py
   ```
3. Output Markdown files will be generated in `md/` and `markdown_pages/`.

## Example
Target: https://www.vivanshinfotech.com  
Output: Clean Markdown versions of home, services, case studies, etc.

## Scraping Targets (Examples)
- Home page
- Services (AI, Web, App Development, etc.)
- Case Studies (ClickControl, Digip, etc.)
- Technologies (React, Laravel, Flutter, etc.)

## Libraries Used
- **Trafilatura**: Main extraction engine.
- **Requests/BeautifulSoup**: Optional for URL handling and parsing.




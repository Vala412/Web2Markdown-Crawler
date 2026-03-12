import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md

base = "https://www.vivanshinfotech.com"

visited = set()
queue = [base]

while queue:

    url = queue.pop(0)

    if url in visited:
        continue

    print("Crawling:", url)

    visited.add(url)

    response = requests.get(url)

    soup = BeautifulSoup(response.text, "html.parser")

    markdown = md(str(soup.body))

    filename = url.split("/")[-1] or "home"

    with open(f"{filename}.md", "w", encoding="utf-8") as f:
        f.write(markdown)

    for link in soup.find_all("a"):
        href = link.get("href")

        if href and href.startswith("/"):
            full = base + href

            if full not in visited:
                queue.append(full)
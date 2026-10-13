from multiprocessing import Semaphore
from typing import TypedDict
import urllib
from urllib.parse import urljoin, urlparse

import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup, Tag


class PageData(TypedDict):
    url: str
    heading: str
    first_paragraph: str
    outgoing_links: list[str]
    image_urls: list[str]

class AsyncCrawler():
    def __init__(self, base_url: str, max_concurrency: int, max_pages : int):
        self.base_url : str = base_url
        self.base_domain: str  = urlparse(self.base_url).netloc
        self.page_data = {}
        self.visited = set()
        self.lock = asyncio.Lock()
        self.max_concurrency: int = max_concurrency
        self.semaphore = asyncio.Semaphore(self.max_concurrency)
        self.session = None
        self.max_pages = max_pages
        self.should_stop = False
        self.all_tasks = set()

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def add_page_visit(self, normalized_url):
        if self.should_stop:
            return False
        async with self.lock:
            if normalized_url in self.visited:
                return False
            if len(self.visited) >= self.max_pages:
                self.should_stop = True
                print("Reached maximum number of pages to crawl.")
                return False
            else:
                self.visited.add(normalized_url)
                return True

    async def get_html(self, url: str) -> str:
        async with self.session.get(url) as r:
            r.raise_for_status()
            content_type = r.headers.get("content-type", "").lower()
            if "text/html" not in content_type:
                raise Exception("Wrong content-type. Content-type must be text/html")
            return await r.text()

    async def crawl_page(self, current_url=None):
        print(f"Crawling {current_url}...")
        if self.should_stop:
            return
        try:
            if current_url is None:
                current_url = self.base_url
            if self.base_domain != urlparse(current_url).netloc:
                return
            current_url_norm = normalize_url(current_url)
            if not await self.add_page_visit(current_url_norm):
                return

            async with self.semaphore:
                html_string = await self.get_html(current_url)
                async with self.lock:
                    self.page_data[current_url_norm]= extract_page_data(html_string,current_url)
                tasks = []
                for hlink in self.page_data[current_url_norm]["outgoing_links"]:
                    new_task = asyncio.create_task(self.crawl_page(hlink))
                    tasks.append(new_task)
                    self.all_tasks.add(new_task)
            await asyncio.gather(*tasks)
        finally:
            self.all_tasks.discard(asyncio.current_task())


    async def crawl(self):
        await self.crawl_page()
        return self.page_data

async def crawl_site_async(base_url, max_concurrency, max_pages):
    async with AsyncCrawler(base_url, max_concurrency, max_pages) as site:
        await site.crawl()
        return site.page_data

def normalize_url(raw_url: str) -> str:
    url_properties = urlparse(raw_url)
    return url_properties.netloc + url_properties.path


def get_heading_from_html(html: str) -> str:
    soup = BeautifulSoup(html, features="html.parser")
    h_tag = soup.find('h1')
    if h_tag is None:
        h_tag = soup.find('h2')
    return h_tag.get_text(strip=True) if isinstance(h_tag, Tag) else ""

def get_first_paragraph_from_html(html: str) -> str:
    soup = BeautifulSoup(html, features="html.parser")
    main_tag = soup.find('main')
    if main_tag is None:
        h_tag = soup.find('p')
    else:
        h_tag = main_tag.find('p')
        if h_tag is None:
            h_tag = soup.find('p')
    return h_tag.get_text(strip=True) if isinstance(h_tag, Tag) else ""

def get_urls_from_html(html: str, base_url):
    soup = BeautifulSoup(html, features ="html.parser")
    h_ref_list = []
    for link in soup.find_all('a'):
        h_ref_list.append(link.get('href'))
    h_ref_list_joined = []
    for url in h_ref_list:
        if url is None:
            continue
        else:
            url = urljoin(base_url, url)
            h_ref_list_joined.append(url)
    return h_ref_list_joined

def get_images_from_html(html, base_url):
    soup = BeautifulSoup(html, features ="html.parser")
    image_list = []
    for link in soup.find_all('img'):
        image_list.append(link.get('src'))
    image_list_joined = []
    for url in image_list:
        if url is None:
            continue
        else:
            url = urljoin(base_url, url)
            image_list_joined.append(url)
    return image_list_joined

def extract_page_data(html: str, page_url: str) -> PageData:
    data: PageData = {
        "url": page_url,
        "heading": get_heading_from_html(html),
        "first_paragraph": get_first_paragraph_from_html(html),
        "outgoing_links": get_urls_from_html(html, page_url),
        "image_urls": get_images_from_html(html, page_url)
    }
    return data

def get_html(url: str) -> str:
    r = requests.get(url, headers={"User-Agent": "BootCrawler/1.0"})
    r.raise_for_status()
    content_type = r.headers.get("content-type", "").lower()
    if "text/html" not in content_type:
        raise Exception("Wrong content-type. Content-type must be text/html")
    return r.text

def crawl_page(base_url, current_url=None, page_data=None):
    if current_url is None:
        current_url = base_url
    if page_data is None:
        page_data = {}
    if urlparse(base_url).netloc != urlparse(current_url).netloc:
        return page_data

    current_url_norm = normalize_url(current_url)
    if current_url_norm in page_data:
        return page_data

    html_string = get_html(current_url)
    page_data[current_url_norm]=extract_page_data(html_string,current_url)
    for hlink in page_data[current_url_norm]["outgoing_links"]:
        page_data = crawl_page(base_url,hlink,page_data)
    return page_data

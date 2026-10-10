from urllib.parse import urlparse
from bs4 import BeautifulSoup, Tag

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
    pass

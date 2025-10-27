# tools/fetch_articles.py
import re, time, requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from readability import Document

FPL_NEWS_BASE = "https://fantasy.premierleague.com/news/"

HEADERS = {"User-Agent": "FPL-Agent (personal use)"}

def get(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r

def list_latest_articles(limit=10):
    """Scrape the FPL News index for latest article links (lightweight)."""
    resp = get(FPL_NEWS_BASE)
    soup = BeautifulSoup(resp.text, "html.parser")
    cards = soup.select("a[href*='/news/']")  # simple selector
    seen, items = set(), []
    for a in cards:
        href = a.get("href", "")
        url = urljoin(FPL_NEWS_BASE, href)
        if url in seen or "/news/" not in url: 
            continue
        seen.add(url)
        title = (a.get_text(" ", strip=True) or "").strip()
        if title and url:
            items.append({"url": url, "title": title})
        if len(items) >= limit:
            break
    return items

def fetch_article(url):
    """Fetch and extract readable text from article URL."""
    resp = get(url)
    doc = Document(resp.text)
    html = doc.summary()
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    return text

def extract_player_mentions(text, player_names):
    """Very simple case-insensitive match on web_name; can be improved (fuzzy)."""
    mentions = []
    low = text.lower()
    for p in player_names:
        name = p.lower()
        # basic word-boundary match to reduce false positives
        if re.search(rf"\b{re.escape(name)}\b", low):
            mentions.append(p)
    return sorted(set(mentions))

def collect_news_bundle(player_names, max_articles=8, sleep=0.6):
    """Return a compact list of {url,title,players,text[:N]} for agent context."""
    bundle = []
    for item in list_latest_articles(limit=max_articles):
        try:
            content = fetch_article(item["url"])
            players = extract_player_mentions(content, player_names)
            bundle.append({
                "url": item["url"],
                "title": item["title"],
                "players": players,
                "snippet": content[:1200]  # keep context small for LLM
            })
            time.sleep(sleep)  # be polite
        except Exception as e:
            # skip noisy failures
            continue
    return bundle

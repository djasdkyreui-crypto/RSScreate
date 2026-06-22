import requests
import re
import json
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString

URL = "https://www.reuters.com/technology/"
OUTPUT_FILE = "reuters_tech.xml"
FEED_TITLE = "Reuters Technology"
FEED_DESC = "Latest technology news from Reuters"
FEED_LINK = "https://www.reuters.com/technology/"

def fetch_articles():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    resp = requests.get(URL, headers=headers, timeout=30)
    resp.raise_for_status()
    html = resp.text

    # 提取页面中内嵌的预加载状态 JSON
    match = re.search(r"window\.__PRELOADED_STATE__\s*=\s*({.*?});", html, re.DOTALL)
    if not match:
        raise ValueError("无法找到预加载数据")

    data = json.loads(match.group(1))

    # 导航到文章列表: __PRELOADED_STATE__ -> root -> sections -> [section] -> items
    # 使用递归查找所有包含 'title' 和 'url' 的项
    def find_articles(obj, depth=0):
        items = []
        if isinstance(obj, dict):
            if "title" in obj and "url" in obj and isinstance(obj["url"], str):
                items.append(obj)
            for v in obj.values():
                items.extend(find_articles(v, depth+1))
        elif isinstance(obj, list):
            for v in obj:
                items.extend(find_articles(v, depth+1))
        return items

    articles = find_articles(data)
    # 去重（按url）
    seen = set()
    unique_articles = []
    for a in articles:
        url = a["url"]
        if url not in seen:
            seen.add(url)
            title = a.get("title", "").strip()
            if title:
                unique_articles.append({"title": title, "url": url})
    return unique_articles

def build_rss(articles):
    rss = Element("rss", version="2.0")
    channel = SubElement(rss, "channel")
    SubElement(channel, "title").text = FEED_TITLE
    SubElement(channel, "link").text = FEED_LINK
    SubElement(channel, "description").text = FEED_DESC

    for art in articles:
        item = SubElement(channel, "item")
        SubElement(item, "title").text = art["title"]
        SubElement(item, "link").text = art["url"]
        # 路透社通常需要完整域名补全
        if art["url"].startswith("/"):
            full_url = "https://www.reuters.com" + art["url"]
            item.find("link").text = full_url
        # 用一个简单的时间戳作为 pubDate
        SubElement(item, "pubDate").text = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

    xml_str = tostring(rss, encoding="unicode")
    pretty = parseString(xml_str).toprettyxml(indent="  ")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(pretty)
    print(f"RSS 生成成功，共 {len(articles)} 篇文章")

if __name__ == "__main__":
    articles = fetch_articles()
    build_rss(articles)

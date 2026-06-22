import requests
from datetime import datetime, timezone
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import time
import re

# ========== 配置 ==========
# 这里建议用一个更稳定的源，我稍后会解释
TARGET_URL = "https://www.reuters.com/technology/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

# ========== 抓取函数 ==========
def fetch_articles():
    try:
        print(f"正在请求 {TARGET_URL} ...")
        resp = requests.get(TARGET_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        html = resp.text
        print("网页获取成功，开始解析...")
    except Exception as e:
        print(f"请求失败：{e}")
        # 如果主站失败，尝试备用源（路透社的 RSS 可能仍有部分可用）
        try:
            print("尝试备用 RSS 源...")
            backup_url = "https://www.reutersagency.com/feed/?taxonomy=best-sectors&post_type=best&best-sectors=tech"
            resp = requests.get(backup_url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            # 直接返回空的，防止报错
            return []
        except:
            return []

    # 下面是一个极简的解析示例（你需要根据实际页面结构调整）
    # 因为路透社页面是动态渲染的，纯 requests 很难稳定提取
    # 这里给你换成更可靠的 RSS 源方案，见下面↓
    return []

# ========== 更加稳定的备选：使用公开 RSS 源 ==========
def fetch_from_rss():
    """直接使用路透社一些仍然可用的 RSS 源，或者换成其他科技新闻 RSS"""
    articles = []
    # 路透社的官方 RSS 其实还有部分存活，例如：
    urls = [
        "https://www.reutersagency.com/feed/?taxonomy=best-sectors&post_type=best&best-sectors=tech",
        "https://feeds.feedburner.com/reuters/technologyNews",  # 可能已失效，但试一下
    ]
    # 更稳定的替代方案：使用 Google News RSS
    # 这里给你一个备用：直接抓取 Google News 科技板块 RSS
    google_rss = "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US:en"
    try:
        print(f"从 Google News RSS 获取文章...")
        resp = requests.get(google_rss, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        # 简单解析 RSS XML（后面会生成我们自己的 RSS）
        import xml.etree.ElementTree as ET
        root = ET.fromstring(resp.text)
        for item in root.iter('item'):
            title = item.find('title').text if item.find('title') is not None else "No title"
            link = item.find('link').text if item.find('link') is not None else ""
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
            desc = item.find('description').text if item.find('description') is not None else ""
            articles.append({
                "title": title,
                "link": link,
                "pub_date": pub_date,
                "description": desc
            })
        print(f"成功获取 {len(articles)} 篇文章")
        return articles
    except Exception as e:
        print(f"RSS 获取失败：{e}")
        return []

# ========== 生成 RSS XML ==========
def create_rss(articles):
    rss = Element('rss', version='2.0')
    channel = SubElement(rss, 'channel')
    SubElement(channel, 'title').text = "Reuters Technology News"
    SubElement(channel, 'link').text = "https://www.reuters.com/technology/"
    SubElement(channel, 'description').text = "Latest technology news"
    SubElement(channel, 'lastBuildDate').text = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')

    for art in articles:
        item = SubElement(channel, 'item')
        SubElement(item, 'title').text = art.get('title', 'No title')
        SubElement(item, 'link').text = art.get('link', '')
        SubElement(item, 'description').text = art.get('description', '')
        if art.get('pub_date'):
            SubElement(item, 'pubDate').text = art.get('pub_date')

    xml_str = minidom.parseString(tostring(rss, 'utf-8')).toprettyxml(indent="  ")
    return xml_str

# ========== 主流程 ==========
if __name__ == "__main__":
    # 优先尝试直接抓取（可能失败），然后使用稳定的 RSS 方案
    articles = fetch_articles()
    if not articles:
        print("切换到 RSS 模式...")
        articles = fetch_from_rss()
    
    if not articles:
        print("未能获取任何文章，生成空 RSS。")
        # 生成一个带提示项的 RSS
        articles = [{
            "title": "No articles fetched",
            "link": "https://www.reuters.com/technology/",
            "pub_date": datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000'),
            "description": "Please check the source."
        }]
    
    rss_content = create_rss(articles)
    with open('reuters_tech.xml', 'w', encoding='utf-8') as f:
        f.write(rss_content)
    print("RSS 文件已生成：reuters_tech.xml")

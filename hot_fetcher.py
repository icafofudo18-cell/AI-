"""
热点获取模块
从聚合 API 获取多平台热点，过滤已发布记录，返回待处理话题列表
"""

import requests
import json
import os
import logging
from datetime import date
from config import HOT_SOURCES, PUBLISHED_FILE

logger = logging.getLogger(__name__)

API_BASE = "https://api.pearapi.ai/api/dailyhot/?title={source}"


def load_published() -> set:
    """加载已发布记录"""
    if not os.path.exists(PUBLISHED_FILE):
        return set()
    try:
        with open(PUBLISHED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data.get("titles", []))
    except Exception:
        return set()


def save_published(title: str):
    """记录已发布标题，防止重复发布"""
    published = {"titles": list(load_published())}
    published["titles"].append(title)
    # 只保留最近 500 条，防止文件过大
    published["titles"] = published["titles"][-500:]
    with open(PUBLISHED_FILE, "w", encoding="utf-8") as f:
        json.dump(published, f, ensure_ascii=False, indent=2)


def fetch_hot_topics(sources: list = None, count: int = 5) -> list:
    """
    从多个平台获取热点话题
    
    Args:
        sources: 平台列表，默认使用 config.HOT_SOURCES
        count: 返回数量
    
    Returns:
        list of dict: [{"title": "...", "desc": "...", "url": "...", "source": "微博"}]
    """
    if sources is None:
        sources = HOT_SOURCES

    published = load_published()
    topics = []
    seen_titles = set()

    for source in sources:
        try:
            url = API_BASE.format(source=requests.utils.quote(source))
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            if data.get("code") != 200:
                logger.warning(f"[{source}] API 返回异常: {data.get('msg')}")
                continue

            items = data.get("data", [])
            logger.info(f"[{source}] 获取到 {len(items)} 条热点")

            for item in items[:15]:  # 每个平台取前15条备用
                title = item.get("title", "").strip()
                if not title:
                    continue
                # 去重（跨平台去重 + 已发布过滤）
                if title in seen_titles or title in published:
                    continue
                seen_titles.add(title)
                topics.append({
                    "title": title,
                    "desc": item.get("desc", title).strip(),
                    "url": item.get("url", ""),
                    "source": source,
                    "hot": item.get("hot", 0),
                })

        except requests.RequestException as e:
            logger.error(f"[{source}] 请求失败: {e}")
        except Exception as e:
            logger.error(f"[{source}] 处理异常: {e}")

    # 优先选取时事、社会类话题（过滤纯娱乐）
    result = _filter_topics(topics, count)
    logger.info(f"最终筛选出 {len(result)} 条热点待处理")
    return result


def _filter_topics(topics: list, count: int) -> list:
    """
    简单过滤：优先保留正式新闻类话题，排除纯娱乐八卦
    """
    entertainment_keywords = ["明星", "恋爱", "出轨", "综艺", "偶像", "流量", "粉丝", "CP"]
    
    priority = []
    normal = []
    
    for t in topics:
        title = t["title"]
        is_entertainment = any(kw in title for kw in entertainment_keywords)
        if not is_entertainment:
            priority.append(t)
        else:
            normal.append(t)
    
    combined = priority + normal
    return combined[:count]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    topics = fetch_hot_topics(count=5)
    for i, t in enumerate(topics, 1):
        print(f"{i}. [{t['source']}] {t['title']}")

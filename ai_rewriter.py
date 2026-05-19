"""
AI 改写模块
使用 OpenAI 兼容接口将热点话题改写为今日头条风格文章
"""

import json
import logging
import re
from openai import OpenAI
from config import AI_API_BASE, AI_API_KEY, AI_MODEL

logger = logging.getLogger(__name__)

client = OpenAI(api_key=AI_API_KEY, base_url=AI_API_BASE)

REWRITE_PROMPT = """你是一名专业的今日头条自媒体内容创作者，擅长将热点事件改写成吸引眼球、内容详实的资讯文章。

请根据以下热点话题，创作一篇适合今日头条发布的图文资讯文章。

【热点话题】{title}
【话题简介】{desc}
【来源平台】{source}

【创作要求】
1. 标题：重新创作一个吸引点击的标题，保留核心关键词，字数20~30字，可以使用数字、疑问句或对比手法
2. 正文：800~1200字，分段清晰，包含：
   - 开篇：用1~2句话抓住读者注意力
   - 事件背景：介绍事件来龙去脉
   - 深度分析：多角度解读事件意义或影响
   - 各方反应：相关方的立场或网友观点
   - 结语：总结或展望，引导读者互动（如"你怎么看？"）
3. 标签：3~5个相关标签

【输出格式】严格按照以下 JSON 格式输出，不要有其他内容：
{{
  "title": "改写后的文章标题",
  "content": "文章正文内容（保留换行用\\n分隔段落）",
  "tags": ["标签1", "标签2", "标签3"]
}}"""


def rewrite_article(topic: dict) -> dict | None:
    """
    将热点话题改写为文章
    
    Args:
        topic: {"title": "...", "desc": "...", "source": "..."}
    
    Returns:
        {"title": "...", "content": "...", "tags": [...]} 或 None（失败时）
    """
    prompt = REWRITE_PROMPT.format(
        title=topic["title"],
        desc=topic.get("desc", topic["title"]),
        source=topic.get("source", "热点"),
    )

    try:
        logger.info(f"正在改写文章: {topic['title'][:30]}...")
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=2000,
        )
        raw = response.choices[0].message.content.strip()
        
        # 提取 JSON 部分（防止模型输出多余内容）
        json_match = re.search(r'\{[\s\S]*\}', raw)
        if not json_match:
            logger.error(f"无法提取 JSON，原始输出: {raw[:200]}")
            return None
        
        article = json.loads(json_match.group())
        
        # 验证必要字段
        if not article.get("title") or not article.get("content"):
            logger.error("AI 输出缺少 title 或 content 字段")
            return None
        
        # 确保 tags 是列表
        if not isinstance(article.get("tags"), list):
            article["tags"] = []
        
        logger.info(f"改写成功: {article['title'][:40]}")
        return article

    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败: {e}, 原始内容: {raw[:200] if 'raw' in dir() else '无'}")
        return None
    except Exception as e:
        logger.error(f"AI 改写失败: {e}")
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_topic = {
        "title": "普京访华俄方代表团名单公布",
        "desc": "普京即将访华，俄方代表团名单正式公布",
        "source": "微博"
    }
    result = rewrite_article(test_topic)
    if result:
        print(f"标题: {result['title']}")
        print(f"正文（前200字）: {result['content'][:200]}")
        print(f"标签: {result['tags']}")

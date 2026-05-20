"""
今日头条自动发布系统 - 手动运行入口
用法：
  python main.py           # 正常运行（获取热点 + 改写 + 发布）
  python main.py --login   # 仅执行登录，保存 Cookie
  python main.py --fetch   # 仅测试热点获取
  python main.py --dry-run # 干运行（只改写不发布，输出到控制台）
"""

import sys
import time
import logging
import os
from datetime import datetime

# 切换工作目录到脚本所在目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from config import HOT_SOURCES, PUBLISH_COUNT, PUBLISH_INTERVAL
from hot_fetcher import fetch_hot_topics, save_published
from ai_rewriter import rewrite_article
from publisher import publish_article, login_only
from image_generator import generate_cover_image
from image_searcher import search_and_download_images


def setup_logging():
    """配置日志"""
    from config import LOG_FILE
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ]
    )


def run(dry_run: bool = False):
    """
    主流程：获取热点 → AI改写 → 发布
    
    Args:
        dry_run: True 时只输出改写结果，不实际发布
    """
    logger = logging.getLogger("main")
    logger.info("=" * 60)
    logger.info(f"开始运行 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"热点来源: {HOT_SOURCES}")
    logger.info(f"计划发布数量: {PUBLISH_COUNT}")
    logger.info("=" * 60)

    # Step 1: 获取热点
    logger.info("Step 1: 获取热点话题...")
    topics = fetch_hot_topics(HOT_SOURCES, PUBLISH_COUNT)
    
    if not topics:
        logger.warning("没有获取到新的热点话题，本次运行结束")
        return

    success_count = 0
    
    for i, topic in enumerate(topics, 1):
        logger.info(f"\n--- 处理第 {i}/{len(topics)} 篇 ---")
        logger.info(f"热点: [{topic['source']}] {topic['title']}")

        # Step 2: AI 改写
        logger.info("Step 2: AI 改写文章...")
        article = rewrite_article(topic)
        
        if not article:
            logger.error("文章改写失败，跳过")
            continue
        
        logger.info(f"改写完成 -> 标题: {article['title']}")
        logger.info(f"正文字数: {len(article['content'])} 字")
        logger.info(f"标签: {article['tags']}")

        # Step 2.5: 生成封面图和文中配图
        logger.info("Step 2.5: 生成封面图和配图...")
        cover_path = None
        inline_paths = []
        
        # # 生成封面图(使用 AI) - 暂时注释,硅基流动API返回451错误
        # if article.get("cover_prompt"):
        #     logger.info(f"正在生成封面图: {article['cover_prompt']}")
        #     cover_path = generate_cover_image(article["cover_prompt"])
        #     if cover_path:
        #         logger.info(f"封面图已生成: {cover_path}")
        #     else:
        #         logger.warning("封面图生成失败，将使用无封面模式")
        
        # 搜索文中配图(使用搜索引擎)
        if article.get("inline_prompts"):
            from config import INLINE_IMAGES_PER_ARTICLE
            logger.info(f"正在搜索 {len(article['inline_prompts'])} 张文中配图...")
            inline_paths = search_and_download_images(
                article["inline_prompts"], 
                count=INLINE_IMAGES_PER_ARTICLE
            )
            if inline_paths:
                logger.info(f"文中配图已搜索: {len(inline_paths)} 张")
            else:
                logger.warning("文中配图搜索失败")
        
        # 将图片路径添加到 article 字典中
        article["cover_path"] = cover_path
        article["inline_paths"] = inline_paths

        if dry_run:
            print("\n" + "="*60)
            print(f"[干运行] 文章 {i}")
            print(f"标题: {article['title']}")
            print(f"正文:\n{article['content'][:500]}...")
            print(f"标签: {article['tags']}")
            print("="*60)
            save_published(topic["title"])
            success_count += 1
            continue

        # Step 3: 发布到今日头条
        logger.info("Step 3: 发布到今日头条...")
        success = publish_article(article)
        
        if success:
            # 记录已发布，防止重复
            save_published(topic["title"])
            success_count += 1
            logger.info(f"第 {i} 篇发布成功")
        else:
            logger.error(f"第 {i} 篇发布失败")

        # 篇间间隔
        if i < len(topics):
            logger.info(f"等待 {PUBLISH_INTERVAL} 秒后发布下一篇...")
            time.sleep(PUBLISH_INTERVAL)

    logger.info("\n" + "="*60)
    logger.info(f"运行结束 - 成功: {success_count}/{len(topics)}")
    logger.info("="*60)


if __name__ == "__main__":
    setup_logging()
    
    args = sys.argv[1:]
    
    if "--login" in args:
        print("启动登录模式...")
        login_only()
    elif "--fetch" in args:
        print("测试热点获取...")
        topics = fetch_hot_topics(count=10)
        print(f"\n获取到 {len(topics)} 条热点：")
        for i, t in enumerate(topics, 1):
            print(f"  {i}. [{t['source']}] {t['title']}")
    elif "--dry-run" in args:
        print("干运行模式（只改写不发布）...")
        run(dry_run=True)
    else:
        run(dry_run=False)

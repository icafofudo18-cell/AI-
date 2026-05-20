"""
测试完整的图片生成和搜索流程
"""
import logging
from ai_rewriter import rewrite_article
from image_generator import generate_cover_image
from image_searcher import search_and_download_images

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

print("=" * 60)
print("完整图片流程测试")
print("=" * 60)

# 模拟一个热点话题
test_topic = {
    "title": "人工智能技术取得重大突破",
    "desc": "AI技术在多个领域实现重要进展",
    "source": "微博"
}

print("\n[步骤1] AI改写文章...")
article = rewrite_article(test_topic)

if not article:
    print("✗ 文章改写失败")
    exit(1)

print(f"✓ 标题: {article['title']}")
print(f"✓ 封面图提示词: {article.get('cover_prompt', '无')}")
print(f"✓ 配图提示词: {article.get('inline_prompts', [])}")

# 生成封面图
print("\n[步骤2] 生成封面图(AI)...")
cover_path = None
if article.get("cover_prompt"):
    cover_path = generate_cover_image(article["cover_prompt"])
    if cover_path:
        print(f"✓ 封面图: {cover_path}")
    else:
        print("✗ 封面图生成失败")

# 搜索配图
print("\n[步骤3] 搜索文中配图(Pixabay)...")
inline_paths = []
if article.get("inline_prompts"):
    inline_paths = search_and_download_images(
        article["inline_prompts"], 
        count=2
    )
    if inline_paths:
        print(f"✓ 配图 ({len(inline_paths)}张):")
        for p in inline_paths:
            print(f"    - {p}")
    else:
        print("✗ 配图搜索失败")

# 总结
print("\n" + "=" * 60)
print("测试结果总结:")
print(f"  封面图: {'✓ ' + cover_path if cover_path else '✗ 失败'}")
print(f"  配图: {'✓ ' + str(len(inline_paths)) + '张' if inline_paths else '✗ 失败'}")
print("=" * 60)

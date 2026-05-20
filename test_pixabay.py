"""
测试 Pixabay 图片搜索
"""
import logging
from image_searcher import search_and_download_images

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

print("=" * 60)
print("Pixabay 图片搜索测试")
print("=" * 60)

# 测试关键词
test_keywords = [
    "科技创新",
    "人工智能"
]

print(f"\n开始搜索 {len(test_keywords)} 张图片...")
print(f"关键词: {test_keywords}\n")

# 执行搜索
image_paths = search_and_download_images(test_keywords, count=2)

# 输出结果
print("\n" + "=" * 60)
if image_paths:
    print(f"测试成功! 下载了 {len(image_paths)} 张图片:")
    for i, path in enumerate(image_paths, 1):
        print(f"  {i}. {path}")
else:
    print("测试失败! 未能下载图片")
print("=" * 60)

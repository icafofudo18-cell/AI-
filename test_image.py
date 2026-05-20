"""
测试硅基流动 API 图片生成
"""
import logging
from image_generator import generate_cover_image

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

print("=" * 60)
print("硅基流动 API 图片生成测试")
print("=" * 60)

# 测试生成极简风格封面图
print("\n[测试] 生成极简风格封面图...")
cover = generate_cover_image("科技创新", "minimal")
if cover:
    print(f"成功: {cover}")
else:
    print("失败")

print("\n" + "=" * 60)
print("测试完成!")
print("=" * 60)

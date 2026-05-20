"""
AI 图片生成模块
使用硅基流动 API 生成封面图和文中配图
"""

import os
import time
import base64
import logging
import requests
from datetime import datetime
from config import (
    IMAGE_API_BASE, IMAGE_API_KEY, IMAGE_MODEL,
    COVER_STYLE, COVER_WIDTH, COVER_HEIGHT, COVER_DIR,
    INLINE_IMAGE_ENABLED, INLINE_IMAGES_PER_ARTICLE,
    INLINE_WIDTH, INLINE_HEIGHT, IMAGES_DIR
)

logger = logging.getLogger(__name__)

# 创建图片保存目录
os.makedirs(COVER_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

# 提示词模板
COVER_PROMPTS = {
    "minimal": (
        "minimalist illustration, {keywords}, clean design, "
        "soft color palette, white background, "
        "modern flat design, high quality, professional"
    ),
    "illustration": (
        "colorful digital illustration, {keywords}, "
        "vibrant colors, artistic style, "
        "detailed composition, professional quality, engaging"
    )
}

INLINE_PROMPT_TEMPLATE = (
    "illustration of {scene}, "
    "relevant to news article, "
    "clean and clear, informative visual, "
    "professional quality"
)


def generate_cover_image(keywords: str, style: str = None) -> str | None:
    """
    生成封面图
    
    Args:
        keywords: 图片关键词(中文)
        style: 风格 (minimal/illustration), 默认使用配置文件
    
    Returns:
        图片文件路径,失败返回 None
    """
    if style is None:
        style = COVER_STYLE
    
    logger.info(f"正在生成封面图: {keywords} (风格: {style})")
    
    # 构建提示词
    prompt_template = COVER_PROMPTS.get(style, COVER_PROMPTS["minimal"])
    prompt = prompt_template.format(keywords=keywords)
    
    # 生成图片
    image_path = _call_image_api(
        prompt=prompt,
        width=COVER_WIDTH,
        height=COVER_HEIGHT,
        output_dir=COVER_DIR,
        filename_prefix="cover"
    )
    
    if image_path:
        logger.info(f"封面图生成成功: {image_path}")
    else:
        logger.error("封面图生成失败")
    
    return image_path


def generate_inline_images(content_snippets: list) -> list:
    """
    生成文中配图
    
    Args:
        content_snippets: 正文片段列表(用于提取关键词)
    
    Returns:
        图片文件路径列表
    """
    if not INLINE_IMAGE_ENABLED:
        logger.info("文中配图功能未启用")
        return []
    
    # 限制配图数量
    snippets = content_snippets[:INLINE_IMAGES_PER_ARTICLE]
    
    logger.info(f"正在生成 {len(snippets)} 张文中配图...")
    
    image_paths = []
    for i, snippet in enumerate(snippets, 1):
        logger.info(f"生成第 {i} 张配图...")
        
        # 提取关键词(简单截取前50字)
        keywords = snippet[:50].strip()
        
        # 构建提示词
        prompt = INLINE_PROMPT_TEMPLATE.format(scene=keywords)
        
        # 生成图片
        image_path = _call_image_api(
            prompt=prompt,
            width=INLINE_WIDTH,
            height=INLINE_HEIGHT,
            output_dir=IMAGES_DIR,
            filename_prefix=f"inline_{i}"
        )
        
        if image_path:
            image_paths.append(image_path)
            logger.info(f"配图 {i} 生成成功: {image_path}")
        else:
            logger.warning(f"配图 {i} 生成失败")
        
        # 避免请求过快
        if i < len(snippets):
            time.sleep(1)
    
    logger.info(f"文中配图生成完成: {len(image_paths)}/{len(snippets)}")
    return image_paths


def _call_image_api(prompt: str, width: int, height: int, 
                    output_dir: str, filename_prefix: str) -> str | None:
    """
    调用硅基流动 API 生成图片
    
    Args:
        prompt: 英文提示词
        width: 图片宽度
        height: 图片高度
        output_dir: 输出目录
        filename_prefix: 文件名前缀
    
    Returns:
        图片文件路径,失败返回 None
    """
    url = f"{IMAGE_API_BASE}/images/generations"
    
    headers = {
        "Authorization": f"Bearer {IMAGE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": IMAGE_MODEL,
        "prompt": prompt,
        "image_size": f"{width}x{height}",
        "batch_size": 1
    }
    
    try:
        logger.info(f"调用 API 生成图片: {prompt[:50]}...")
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        
        # 提取图片数据
        if "images" in result and len(result["images"]) > 0:
            image_data = result["images"][0]
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.png"
            filepath = os.path.join(output_dir, filename)
            
            # 保存图片
            if "url" in image_data:
                # URL 格式
                img_response = requests.get(image_data["url"], timeout=60)
                img_response.raise_for_status()
                with open(filepath, "wb") as f:
                    f.write(img_response.content)
            elif "b64_json" in image_data:
                # base64 格式
                image_bytes = base64.b64decode(image_data["b64_json"])
                with open(filepath, "wb") as f:
                    f.write(image_bytes)
            else:
                logger.error("API 返回中没有图片数据")
                return None
            
            logger.info(f"图片已保存: {filepath}")
            return filepath
        else:
            logger.error(f"API 返回格式异常: {result}")
            return None
    
    except requests.exceptions.RequestException as e:
        logger.error(f"API 调用失败: {e}")
        return None
    except Exception as e:
        logger.error(f"图片生成异常: {e}", exc_info=True)
        return None

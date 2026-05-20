"""
图片搜索模块
支持从 Pixabay/Bing/Unsplash 搜索并下载真实图片
"""

import os
import time
import logging
import requests
from datetime import datetime
from config import (
    IMAGE_SEARCH_ENGINE,
    PIXABAY_API_KEY,
    BING_API_KEY,
    UNSPLASH_ACCESS_KEY,
    INLINE_WIDTH,
    INLINE_HEIGHT,
    IMAGES_DIR
)

logger = logging.getLogger(__name__)

# 创建图片保存目录
os.makedirs(IMAGES_DIR, exist_ok=True)


def search_and_download_images(keywords_list: list, count: int = 2) -> list:
    """
    搜索并下载图片
    
    Args:
        keywords_list: 关键词列表
        count: 每篇文章需要的配图数量
    
    Returns:
        图片文件路径列表
    """
    if not keywords_list:
        return []
    
    logger.info(f"开始搜索图片: {keywords_list[:count]}")
    
    image_paths = []
    
    # 根据配置的搜索引擎选择搜索函数
    if IMAGE_SEARCH_ENGINE == "pixabay":
        search_func = search_pixabay
    elif IMAGE_SEARCH_ENGINE == "bing":
        search_func = search_bing
    elif IMAGE_SEARCH_ENGINE == "unsplash":
        search_func = search_unsplash
    else:
        logger.warning(f"未知的搜索引擎: {IMAGE_SEARCH_ENGINE}, 使用 pixabay")
        search_func = search_pixabay
    
    # 为每个关键词搜索图片
    for i, keywords in enumerate(keywords_list[:count], 1):
        logger.info(f"搜索第 {i} 张图片: {keywords}")
        
        image_path = search_func(keywords, i)
        if image_path:
            image_paths.append(image_path)
            logger.info(f"图片 {i} 下载成功: {image_path}")
        else:
            logger.warning(f"图片 {i} 搜索失败")
        
        # 避免请求过快
        if i < count:
            time.sleep(1)
    
    logger.info(f"图片搜索完成: {len(image_paths)}/{count}")
    return image_paths


def search_pixabay(keywords: str, index: int) -> str | None:
    """
    从 Pixabay 搜索图片
    
    Args:
        keywords: 搜索关键词
        index: 图片序号(用于文件名)
    
    Returns:
        图片文件路径
    """
    if not PIXABAY_API_KEY:
        logger.error("未配置 PIXABAY_API_KEY")
        return None
    
    url = "https://pixabay.com/api/"
    params = {
        "key": PIXABAY_API_KEY,
        "q": keywords,
        "image_type": "photo",
        "orientation": "horizontal",
        "safesearch": "true",
        "per_page": 5,
        "lang": "zh"
    }
    
    try:
        logger.info(f"Pixabay 搜索: {keywords}")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        hits = data.get("hits", [])
        
        if not hits:
            logger.warning(f"Pixabay 未找到图片: {keywords}")
            return None
        
        # 选择第一张图片
        image_url = hits[0].get("largeImageURL")
        if not image_url:
            return None
        
        # 下载图片
        return _download_image(image_url, f"pixabay_{index}")
    
    except Exception as e:
        logger.error(f"Pixabay 搜索失败: {e}")
        return None


def search_bing(keywords: str, index: int) -> str | None:
    """
    从 Bing Image Search 搜索图片
    
    Args:
        keywords: 搜索关键词
        index: 图片序号
    
    Returns:
        图片文件路径
    """
    if not BING_API_KEY:
        logger.error("未配置 BING_API_KEY")
        return None
    
    url = "https://api.bing.microsoft.com/v7.0/images/search"
    headers = {"Ocp-Apim-Subscription-Key": BING_API_KEY}
    params = {
        "q": keywords,
        "count": 5,
        "imageType": "Photo",
        "size": "Medium",
        "safeSearch": "Strict"
    }
    
    try:
        logger.info(f"Bing 搜索: {keywords}")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        images = data.get("value", [])
        
        if not images:
            logger.warning(f"Bing 未找到图片: {keywords}")
            return None
        
        # 选择第一张图片
        image_url = images[0].get("contentUrl")
        if not image_url:
            return None
        
        # 下载图片
        return _download_image(image_url, f"bing_{index}")
    
    except Exception as e:
        logger.error(f"Bing 搜索失败: {e}")
        return None


def search_unsplash(keywords: str, index: int) -> str | None:
    """
    从 Unsplash 搜索图片
    
    Args:
        keywords: 搜索关键词
        index: 图片序号
    
    Returns:
        图片文件路径
    """
    if not UNSPLASH_ACCESS_KEY:
        logger.error("未配置 UNSPLASH_ACCESS_KEY")
        return None
    
    url = "https://api.unsplash.com/search/photos"
    headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
    params = {
        "query": keywords,
        "per_page": 5,
        "orientation": "landscape"
    }
    
    try:
        logger.info(f"Unsplash 搜索: {keywords}")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        images = data.get("results", [])
        
        if not images:
            logger.warning(f"Unsplash 未找到图片: {keywords}")
            return None
        
        # 选择第一张图片
        image_url = images[0].get("urls", {}).get("regular")
        if not image_url:
            return None
        
        # 下载图片
        return _download_image(image_url, f"unsplash_{index}")
    
    except Exception as e:
        logger.error(f"Unsplash 搜索失败: {e}")
        return None


def _download_image(image_url: str, filename_prefix: str) -> str | None:
    """
    下载图片并保存
    
    Args:
        image_url: 图片URL
        filename_prefix: 文件名前缀
    
    Returns:
        保存的文件路径
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.jpg"
        filepath = os.path.join(IMAGES_DIR, filename)
        
        logger.info(f"下载图片: {image_url[:80]}...")
        response = requests.get(image_url, timeout=60)
        response.raise_for_status()
        
        with open(filepath, "wb") as f:
            f.write(response.content)
        
        logger.info(f"图片已保存: {filepath}")
        return filepath
    
    except Exception as e:
        logger.error(f"图片下载失败: {e}")
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # 测试搜索
    test_keywords = ["科技创新", "人工智能"]
    paths = search_and_download_images(test_keywords, count=2)
    
    if paths:
        print(f"\n成功下载 {len(paths)} 张图片:")
        for p in paths:
            print(f"  - {p}")

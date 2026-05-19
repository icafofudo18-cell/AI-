"""
今日头条自动发布模块
使用 Playwright 模拟浏览器操作，登录今日头条创作者中心并发布图文文章
"""

import json
import os
import time
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from config import (
    HEADLESS, TIMEOUT, COOKIES_FILE, SCREENSHOTS_DIR,
    TOUTIAO_PHONE
)

logger = logging.getLogger(__name__)

TOUTIAO_CREATOR_URL = "https://mp.toutiao.com/profile_v4/graphic/publish"
TOUTIAO_HOME_URL = "https://mp.toutiao.com"


def ensure_screenshots_dir():
    if not os.path.exists(SCREENSHOTS_DIR):
        os.makedirs(SCREENSHOTS_DIR)


def save_cookies(context):
    """保存登录 Cookie"""
    cookies = context.cookies()
    with open(COOKIES_FILE, "w", encoding="utf-8") as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)
    logger.info(f"Cookie 已保存到 {COOKIES_FILE}")


def load_cookies(context):
    """加载已保存的 Cookie"""
    if not os.path.exists(COOKIES_FILE):
        return False
    try:
        with open(COOKIES_FILE, "r", encoding="utf-8") as f:
            cookies = json.load(f)
        context.add_cookies(cookies)
        logger.info("Cookie 加载成功")
        return True
    except Exception as e:
        logger.warning(f"Cookie 加载失败: {e}")
        return False


def is_logged_in(page) -> bool:
    """检查是否已登录"""
    try:
        page.goto(TOUTIAO_HOME_URL, timeout=TIMEOUT)
        page.wait_for_load_state("networkidle", timeout=TIMEOUT)
        # 已登录时页面不会跳转到登录页
        return "login" not in page.url and "passport" not in page.url
    except Exception:
        return False


def manual_login(page, context):
    """
    手动登录流程：弹出浏览器，等待用户扫码登录
    """
    logger.info("正在打开今日头条创作者中心，请手动扫码登录...")
    print("\n" + "="*50)
    print("请在弹出的浏览器中完成今日头条账号登录")
    print("登录成功后请按回车键继续...")
    print("="*50)
    
    page.goto(TOUTIAO_HOME_URL, timeout=TIMEOUT)
    input("登录完成后，请按回车键继续 > ")
    
    # 验证登录状态
    if is_logged_in(page):
        save_cookies(context)
        logger.info("登录验证成功，Cookie 已保存")
        return True
    else:
        logger.error("登录验证失败，请重试")
        return False


def publish_article(article: dict) -> bool:
    """
    发布一篇文章到今日头条
    
    Args:
        article: {"title": "...", "content": "...", "tags": [...]}
    
    Returns:
        bool: 是否发布成功
    """
    ensure_screenshots_dir()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            # 1. 加载 Cookie 并验证登录
            cookie_loaded = load_cookies(context)
            if not cookie_loaded or not is_logged_in(page):
                logger.warning("Cookie 失效或不存在，需要重新登录")
                if not manual_login(page, context):
                    return False

            # 2. 打开发布页面
            logger.info("正在打开文章发布页面...")
            page.goto(TOUTIAO_CREATOR_URL, timeout=TIMEOUT)
            page.wait_for_load_state("networkidle", timeout=TIMEOUT)
            time.sleep(2)

            # 截图记录初始状态
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            page.screenshot(path=f"{SCREENSHOTS_DIR}/01_publish_page_{ts}.png")

            # 3. 填写文章标题
            logger.info("正在填写标题...")
            title_selectors = [
                'input[placeholder*="标题"]',
                'input[placeholder*="请输入标题"]',
                '.title-input input',
                'input.title',
            ]
            title_input = None
            for sel in title_selectors:
                try:
                    title_input = page.wait_for_selector(sel, timeout=5000)
                    if title_input:
                        break
                except PlaywrightTimeout:
                    continue
            
            if not title_input:
                logger.error("找不到标题输入框")
                page.screenshot(path=f"{SCREENSHOTS_DIR}/error_no_title_{ts}.png")
                return False
            
            title_input.click()
            title_input.fill("")
            title_input.type(article["title"], delay=50)
            time.sleep(0.5)

            # 4. 填写正文内容
            logger.info("正在填写正文内容...")
            editor_selectors = [
                '.editor-kit-container [contenteditable="true"]',
                '[contenteditable="true"].public-DraftEditor-content',
                '.notranslate[contenteditable="true"]',
                '[contenteditable="true"]',
            ]
            editor = None
            for sel in editor_selectors:
                try:
                    editor = page.wait_for_selector(sel, timeout=5000)
                    if editor:
                        break
                except PlaywrightTimeout:
                    continue
            
            if not editor:
                logger.error("找不到正文编辑器")
                page.screenshot(path=f"{SCREENSHOTS_DIR}/error_no_editor_{ts}.png")
                return False
            
            editor.click()
            time.sleep(0.5)
            
            # 逐段输入正文（处理换行）
            paragraphs = article["content"].split("\n")
            for para in paragraphs:
                if para.strip():
                    page.keyboard.type(para.strip(), delay=20)
                page.keyboard.press("Enter")
            
            time.sleep(1)
            page.screenshot(path=f"{SCREENSHOTS_DIR}/02_content_filled_{ts}.png")

            # 5. 处理标签（如果有标签输入区域）
            if article.get("tags"):
                _fill_tags(page, article["tags"], ts)

            # 6. 点击发布按钮
            logger.info("正在点击发布按钮...")
            publish_btn_selectors = [
                'button:has-text("发布文章")',
                'button:has-text("发布")',
                '.publish-btn',
                'button[class*="publish"]',
            ]
            publish_btn = None
            for sel in publish_btn_selectors:
                try:
                    publish_btn = page.wait_for_selector(sel, timeout=5000)
                    if publish_btn and publish_btn.is_visible():
                        break
                except PlaywrightTimeout:
                    continue
            
            if not publish_btn:
                logger.error("找不到发布按钮")
                page.screenshot(path=f"{SCREENSHOTS_DIR}/error_no_publish_btn_{ts}.png")
                return False
            
            page.screenshot(path=f"{SCREENSHOTS_DIR}/03_before_publish_{ts}.png")
            publish_btn.click()
            time.sleep(3)
            
            # 7. 处理可能出现的确认弹窗
            try:
                confirm_btn = page.wait_for_selector('button:has-text("确认发布")', timeout=3000)
                if confirm_btn:
                    confirm_btn.click()
                    time.sleep(2)
            except PlaywrightTimeout:
                pass  # 没有确认弹窗，继续

            # 8. 验证发布结果
            time.sleep(3)
            page.screenshot(path=f"{SCREENSHOTS_DIR}/04_after_publish_{ts}.png")
            
            # 检查成功提示
            success_indicators = ["发布成功", "文章已发布", "审核中"]
            page_content = page.content()
            success = any(indicator in page_content for indicator in success_indicators)
            
            if success:
                logger.info(f"文章发布成功: {article['title']}")
                # 更新 Cookie（保持最新登录状态）
                save_cookies(context)
                return True
            else:
                logger.warning(f"发布结果不确定，请查看截图: {SCREENSHOTS_DIR}/04_after_publish_{ts}.png")
                return True  # 保守返回 True，避免重复发布

        except Exception as e:
            logger.error(f"发布过程异常: {e}", exc_info=True)
            try:
                page.screenshot(path=f"{SCREENSHOTS_DIR}/error_exception_{ts}.png")
            except Exception:
                pass
            return False
        finally:
            browser.close()


def _fill_tags(page, tags: list, ts: str):
    """尝试填写标签"""
    try:
        tag_selectors = [
            'input[placeholder*="标签"]',
            'input[placeholder*="添加标签"]',
            '.tag-input input',
        ]
        for sel in tag_selectors:
            tag_input = page.query_selector(sel)
            if tag_input:
                for tag in tags[:5]:
                    tag_input.click()
                    tag_input.type(tag, delay=50)
                    page.keyboard.press("Enter")
                    time.sleep(0.3)
                logger.info(f"标签填写完成: {tags}")
                return
    except Exception as e:
        logger.warning(f"标签填写跳过: {e}")


def login_only():
    """仅执行登录流程，保存 Cookie"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()
        
        page.goto(TOUTIAO_HOME_URL)
        print("\n" + "="*50)
        print("请在浏览器中完成今日头条账号登录（手机扫码或账号密码）")
        print("登录成功跳转到创作者中心后，按回车继续")
        print("="*50)
        input("按回车继续 > ")
        
        save_cookies(context)
        print("登录成功！Cookie 已保存，下次运行无需重新登录")
        browser.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    login_only()

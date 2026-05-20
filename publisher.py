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

            # 2.5 关闭右侧"头条创作助手"浮层（它的遮罩会拦截点击）
            try:
                # 方式1：点击关闭按钮（面板右上角的收起图标）
                close_btn = page.locator('.ai-assistant-drawer .byte-drawer-close, .ai-assistant-drawer [class*="close"]').first
                if close_btn.is_visible(timeout=2000):
                    close_btn.click(force=True)
                    time.sleep(0.5)
                    logger.info("已关闭 AI 创作助手面板")
            except Exception:
                pass
            
            # 如果关闭按钮没找到，尝试点击遮罩层外部区域来关闭
            try:
                drawer_mask = page.locator('.byte-drawer-mask').first
                if drawer_mask.is_visible(timeout=1000):
                    drawer_mask.click(force=True)
                    time.sleep(0.5)
                    logger.info("通过点击遮罩关闭浮层")
            except Exception:
                pass

            # 3. 填写文章标题
            logger.info("正在填写标题...")
            title_input = None
            try:
                # 方式1：通过 placeholder 文本定位（支持 contenteditable 和 textarea）
                title_input = page.get_by_placeholder("请输入文章标题").first
                title_input.wait_for(timeout=5000)
            except Exception:
                pass

            if not title_input or not title_input.is_visible():
                try:
                    # 方式2：通过 class/属性选择器备用
                    title_selectors = [
                        'textarea[placeholder*="标题"]',
                        '[data-placeholder*="标题"]',
                        '.article-title [contenteditable="true"]',
                        '.title-wrap [contenteditable="true"]',
                    ]
                    for sel in title_selectors:
                        try:
                            title_input = page.wait_for_selector(sel, timeout=3000)
                            if title_input and title_input.is_visible():
                                break
                        except PlaywrightTimeout:
                            continue
                except Exception:
                    pass

            if not title_input:
                logger.error("找不到标题输入框")
                page.screenshot(path=f"{SCREENSHOTS_DIR}/error_no_title_{ts}.png")
                return False

            title_input.click(force=True)
            time.sleep(0.3)
            # 清空现有内容
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            # 输入标题
            page.keyboard.type(article["title"], delay=50)
            time.sleep(0.5)

            # 4. 填写正文内容
            logger.info("正在填写正文内容...")
            
            # 策略1：从标题输入框直接 Tab 跳转到正文编辑区
            try:
                page.keyboard.press("Tab")
                time.sleep(0.5)
                logger.info("通过 Tab 键跳转到正文区域")
            except Exception as e:
                logger.warning(f"Tab 跳转失败: {e}")
            
            # 策略2：如果 Tab 没效果，直接定位 contenteditable 元素
            # 先尝试点击正文区域确保焦点正确
            try:
                # 排除 textarea（标题），找 contenteditable 的 div
                editor_candidates = page.locator('[contenteditable="true"]')
                count = editor_candidates.count()
                logger.info(f"找到 {count} 个 contenteditable 元素")
                
                if count > 0:
                    # 取第一个 contenteditable div（标题是 textarea，不是 contenteditable）
                    editor = editor_candidates.first
                    editor.click(force=True)
                    time.sleep(0.3)
                    logger.info("已点击正文编辑区域")
            except Exception as e:
                logger.warning(f"点击编辑器失败: {e}")
                # 策略3：通过文本定位
                try:
                    placeholder_el = page.get_by_text("请输入正文").first
                    placeholder_el.click(force=True)
                    time.sleep(0.3)
                    logger.info("通过文本定位点击正文区域")
                except Exception as e2:
                    logger.error(f"所有正文定位策略均失败: {e2}")
                    page.screenshot(path=f"{SCREENSHOTS_DIR}/error_no_editor_{ts}.png")
                    return False

            # 逐段输入正文（处理换行）
            paragraphs = article["content"].split("\n")
            for para in paragraphs:
                if para.strip():
                    page.keyboard.type(para.strip(), delay=10)
                page.keyboard.press("Enter")

            time.sleep(1)
            page.screenshot(path=f"{SCREENSHOTS_DIR}/02_content_filled_{ts}.png")

            # 5. 处理封面图(选择"无封面"单选按钮)
            logger.info("正在设置封面图为无封面模式...")
            try:
                # 直接点击"无封面"单选按钮
                no_cover_radio = None
                no_cover_selectors = [
                    'text="无封面"',  # 点击文字
                    'label:has-text("无封面")',  # 点击整个label
                    '[class*="cover-option"]:has-text("无封面")',  # 选项容器
                ]
                            
                for sel in no_cover_selectors:
                    try:
                        no_cover_radio = page.locator(sel).first
                        if no_cover_radio.is_visible(timeout=2000):
                            no_cover_radio.click(force=True)
                            time.sleep(0.5)
                            logger.info(f"已选择无封面: {sel}")
                            break
                    except Exception as e:
                        logger.debug(f"尝试 {sel} 失败: {e}")
                        continue
                            
                if not no_cover_radio:
                    logger.warning("未找到无封面选项,使用默认设置")
                else:
                    # 验证是否选中(检查单选按钮是否被选中)
                    try:
                        is_checked = page.locator('text="无封面"').first.is_checked()
                        if is_checked:
                            logger.info("无封面已选中")
                        else:
                            logger.warning("无封面未成功选中")
                    except Exception:
                        pass
                                    
            except Exception as e:
                logger.warning(f"封面图设置失败,继续发布: {e}")
                        
            # 截图记录封面设置后的状态
            page.screenshot(path=f"{SCREENSHOTS_DIR}/03_cover_set_{ts}.png")

            # 6. 处理标签（如果有标签输入区域）
            if article.get("tags"):
                _fill_tags(page, article["tags"], ts)

            # 7. 点击"预览并发布"按钮
            logger.info("正在点击预览并发布按钮...")
            publish_btn = None
            publish_btn_strategies = [
                lambda: page.locator('button:has-text("预览并发布")').last,  # 优先匹配"预览并发布"
                lambda: page.get_by_role("button", name="预览并发布"),
                lambda: page.locator('button:has-text("发布")').last,  # 备用:只匹配"发布"
                lambda: page.get_by_role("button", name="发布"),
                lambda: page.locator('.publish-btn, [class*="publish"]').first,
            ]
            for strategy in publish_btn_strategies:
                try:
                    btn = strategy()
                    if btn.is_visible(timeout=3000):
                        publish_btn = btn
                        logger.info(f"找到发布按钮: {btn.text_content()}")
                        break
                except Exception:
                    continue
                        
            if not publish_btn:
                logger.error("找不到发布按钮")
                page.screenshot(path=f"{SCREENSHOTS_DIR}/error_no_publish_btn_{ts}.png")
                return False
                        
            page.screenshot(path=f"{SCREENSHOTS_DIR}/04_before_publish_{ts}.png")
            publish_btn.click()
            time.sleep(3)
                        
            # 8. 处理预览和确认发布
            logger.info("等待预览界面出现...")
            
            # 策略1:等待弹窗出现
            preview_found = False
            try:
                preview_dialog = page.wait_for_selector('.byte-modal, .modal, [class*="preview"], [class*="dialog"]', timeout=5000)
                if preview_dialog:
                    logger.info("预览弹窗已出现")
                    preview_found = True
                    time.sleep(1)
                    page.screenshot(path=f"{SCREENSHOTS_DIR}/05_preview_dialog_{ts}.png")
            except PlaywrightTimeout:
                logger.info("未出现预览弹窗,检查是否页面跳转...")
            
            # 策略2:如果弹窗没出现,可能是页面内嵌预览,滚动查找确认按钮
            if not preview_found:
                logger.info("滚动页面查找确认按钮...")
                try:
                    # 滚动到底部
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(1)
                    page.screenshot(path=f"{SCREENSHOTS_DIR}/05_preview_scrolled_{ts}.png")
                except Exception as e:
                    logger.warning(f"滚动失败: {e}")
            
            # 查找确认发布按钮(支持多种文本)
            confirm_btn = None
            confirm_strategies = [
                lambda: page.locator('button:has-text("确认发布")').first,
                lambda: page.get_by_role("button", name="确认发布"),
                lambda: page.locator('button:has-text("确认")').first,
                lambda: page.get_by_role("button", name="确认"),
                lambda: page.locator('.byte-modal button:has-text("发布")').first,
                lambda: page.locator('.modal button:has-text("发布")').first,
                lambda: page.locator('button:has-text("确定")').first,  # 有些是"确定"
                lambda: page.get_by_role("button", name="确定"),
            ]
            
            for strategy in confirm_strategies:
                try:
                    btn = strategy()
                    if btn.is_visible(timeout=2000):
                        confirm_btn = btn
                        logger.info(f"找到确认按钮: {btn.text_content()}")
                        break
                except Exception:
                    continue
            
            if confirm_btn:
                logger.info("点击确认发布按钮...")
                confirm_btn.click()
                time.sleep(3)
            else:
                logger.warning("未找到确认按钮,尝试直接完成发布")
                page.screenshot(path=f"{SCREENSHOTS_DIR}/05_no_confirm_btn_{ts}.png")
                # 不返回False,继续验证发布结果

            # 9. 验证发布结果
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
